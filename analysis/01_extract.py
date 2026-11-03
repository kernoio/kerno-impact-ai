"""Extract the tables in the two Kerno PDFs into CSVs.

Input:  raw/kerno-audit-benchmark.txt, raw/adoption-date-sweep.txt
        (made with `pdftotext -layout`, poppler 26.10; source PDF hashes in
        raw/source-pdf-sha256.txt)
Output: data/repos.csv, data/before_after.csv, data/trends.csv,
        data/sweep_2026_02.csv, data/extract_checks.txt

Every check below compares the extraction against a total the PDF prints
itself. The script exits non-zero if any check fails.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

BA_METRICS = [
    "cyclomatic delta (per 100 production lines added)",
    "share of follow-ups that are repairs",
    "production lines added per commit",
    "reimplementations (per KLOC added)",
    "rework edits (per 100 lines added)",
    "lines rewritten within 30 days",
    "lines rewritten within 90 days",
    "excess complexity per KLOC",
    "cyclomatic delta per commit",
    "days to first follow-up",
    "follow-ups (per change)",
]
TREND_METRICS = [
    "cyclomatic delta (per 100 production lines added)",
    "share of follow-ups that are repairs",
    "production lines added per commit",
    "reimplementations (per KLOC added)",
    "rework edits (per 100 lines added)",
    "days to first follow-up",
    "follow-ups per change",
    "unknown",
]
STATUSES = ("asserted", "withheld", "excluded")


def squeeze(line):
    return re.sub(r"\s+", " ", line).strip()


def num(tok):
    """'1,234' -> 1234.0, '−0.5' -> -0.5, '—' -> None, '<0.0001' -> 0.0001."""
    tok = tok.replace("−", "-").replace(",", "")
    if tok in ("—", "-", ""):
        return None
    if tok.startswith("<"):
        tok = tok[1:]
    if tok.endswith("%"):
        tok = tok[:-1]
    return float(tok)


def split_metric(rest, metrics):
    for m in metrics:
        if rest.startswith(m + " "):
            return m, rest[len(m) + 1:]
    return None, None


bench = [squeeze(l) for l in open(os.path.join(RAW, "kerno-audit-benchmark.txt"), encoding="utf-8")]
checks = []


def check(name, got, want):
    ok = got == want
    checks.append(f"{'OK  ' if ok else 'FAIL'} {name}: extracted={got} pdf={want}")
    return ok


# --- repos (pages 31-32, "Every repository") -------------------------------
repo_re = re.compile(r"^(\S+/\S+) (measured|undated|declined) (.*)$")
repos = []
for l in bench:
    m = repo_re.match(l)
    if not m:
        continue
    full, status, rest = m.groups()
    t = rest.split()
    if status == "declined":
        repos.append(dict(full_name=full, repo=full.split("/")[1], status=status))
        continue
    # Commits AIshare Adoption Rule Headline Trends Authors WithAI Minutes PeakRSS(2 tok) Judge$
    repos.append(dict(
        full_name=full, repo=full.split("/")[1], status=status,
        commits=int(num(t[0])), ai_share_pct=num(t[1]),
        adoption=None if t[2] == "—" else t[2], rule=None if t[3] == "—" else t[3],
        headline_rows=int(t[4]), trends=int(t[5]), authors=int(num(t[6])),
        authors_with_ai=int(num(t[7])), minutes=num(t[8]),
        judge_usd=None if t[-1] == "—" else num(t[-1].lstrip("$")),
    ))
fields = ["full_name", "repo", "status", "commits", "ai_share_pct", "adoption", "rule",
          "headline_rows", "trends", "authors", "authors_with_ai", "minutes", "judge_usd"]
with open(os.path.join(DATA, "repos.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(repos)
check("repositories", len(repos), 46)
check("total commits", sum(r.get("commits", 0) for r in repos), 201576)
check("dated repositories", sum(r["status"] == "measured" for r in repos), 30)
check("undated repositories", sum(r["status"] == "undated" for r in repos), 15)
check("total authors", sum(r.get("authors", 0) for r in repos), 6847)
short = {r["repo"] for r in repos}

# --- before/after rows (pages 21-30) ---------------------------------------
ba = []
for l in bench:
    first = l.split(" ", 1)
    if len(first) < 2 or first[0] not in short:
        continue
    metric, tail = split_metric(first[1], BA_METRICS)
    if not metric:
        continue
    t = tail.split()
    if len(t) < 9 or t[8] not in STATUSES:
        continue
    ba.append(dict(
        repo=first[0], metric=metric,
        before=num(t[0]), after=num(t[1]), change_pct=num(t[2]),
        ci_low_pct=num(t[3]), ci_high_pct=num(t[4]),
        n_before=int(num(t[5])), n_after=int(num(t[6])),
        p=num(t[7]), p_raw=t[7], status=t[8], reason=" ".join(t[9:]).replace("—", "").strip(),
    ))
with open(os.path.join(DATA, "before_after.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ba[0].keys()))
    w.writeheader()
    w.writerows(ba)
check("before/after rows", len(ba), 330)  # "330 of 330 measurements shown"
check("before/after repos", len({r["repo"] for r in ba}), 30)

# --- trend fits (pages 9-17) -----------------------------------------------
tr = []
for l in bench:
    first = l.split(" ", 1)
    if len(first) < 2 or first[0] not in short:
        continue
    metric, tail = split_metric(first[1], TREND_METRICS)
    if not metric:
        continue
    t = tail.split()
    if len(t) != 7 or t[6] not in ("shown", "flat", "unfitted", "unestablished", "withheld"):
        continue
    tr.append(dict(
        repo=first[0], metric=metric.replace("follow-ups per change", "follow-ups (per change)"),
        months=int(t[0]), start=num(t[1]), end=num(t[2]), window_change_pct=num(t[3]),
        slope_per_month=num(t[4]), p=num(t[5]), p_raw=t[5], status=t[6],
    ))
with open(os.path.join(DATA, "trends.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(tr[0].keys()))
    w.writeheader()
    w.writerows(tr)
check("trend rows", len(tr), 315)  # "315 of 315 fitted series shown"
check("established trends (status=shown)", sum(r["status"] == "shown" for r in tr), 88)

# --- sweep table at forced 2026-02 ------------------------------------------
SWEEP_COLS = ["cyclomatic_delta_per100", "rework_edits", "follow_ups", "reimplementations", "repair_share"]
sweep = []
for l in open(os.path.join(RAW, "adoption-date-sweep.txt"), encoding="utf-8"):
    s = squeeze(l)
    tok = s.split()
    if not tok or tok[0] not in short:
        continue
    undated = "no detected date" in s
    vals = [x for x in tok[1:] if x == "—" or x.endswith("%")]
    if not vals and not undated:
        continue
    if len(vals) not in (0, 5):
        sys.exit(f"sweep row with {len(vals)} values: {s}")
    row = dict(repo=tok[0], detected_date=not undated)
    for c, v in zip(SWEEP_COLS, vals or ["—"] * 5):
        row[c + "_pct"] = num(v)
    sweep.append(row)
with open(os.path.join(DATA, "sweep_2026_02.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sweep[0].keys()))
    w.writeheader()
    w.writerows(sweep)
check("sweep repos", len(sweep), 45)
# The sweep's cards at 2026-02: wrong way / right way per metric (lower is better for all five)
cards = {"cyclomatic_delta_per100": (35, 0), "rework_edits": (13, 21), "follow_ups": (23, 12),
         "reimplementations": (12, 19), "repair_share": (6, 16)}
for c, (worse, better) in cards.items():
    v = [r[c + "_pct"] for r in sweep if r[c + "_pct"] is not None]
    check(f"sweep 2026-02 {c} worse/better", (sum(x > 0 for x in v), sum(x < 0 for x in v)), (worse, better))

with open(os.path.join(DATA, "extract_checks.txt"), "w") as f:
    f.write("\n".join(checks) + "\n")
print("\n".join(checks))
if any(c.startswith("FAIL") for c in checks):
    sys.exit(1)
