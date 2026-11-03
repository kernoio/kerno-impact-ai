"""Cross-repository results that need the raw benchmark data.

  A. throughput and commit kinds before/after   (from data/raw_throughput.csv, 11_raw_commits.py)
  B. whole-codebase complexity snapshots         (runs/<repo>/complexity.json:snapshots)
       share of functions with cyclomatic complexity > 10, excess complexity per KLOC,
       first vs last snapshot in the window, for every measured repository
  C. AI-labelled vs unlabelled commits in the same period
       (complexity.withinPeriodRate, churn.withinPeriod, cost.withinPeriod)
  D. primary language per repository (last snapshot, by function count)
  E. AI share vs complexity slope, reconciled with the benchmark README (rho = +0.04)
  F. bug-fix classifier precision from the hand-labelled sample (data/raw_kinds_labelled.csv)

Output: data/raw_results.json, data/raw_snapshots.csv, data/raw_within.csv, data/raw_throughput_changes.csv
"""
import csv
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # run with python3 -I
from stats_util import describe, spearman_perm

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BENCH = os.path.join(HERE, "raw", "zip", "audit-bench")
RUNS = os.path.join(BENCH, "runs")
REPOS = {r["name"]: r for r in csv.DictReader(open(os.path.join(BENCH, "data", "repositories.csv")))}
MEASURED = [n for n, r in REPOS.items() if r["status"] in ("measured", "undated")]
out = {}


def write(fn, rows):
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(os.path.join(DATA, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def rel(a, b):
    return None if not a else 100 * (b / a - 1)


# ---------------------------------------------------------------- A. throughput
tp = list(csv.DictReader(open(os.path.join(DATA, "raw_throughput.csv"))))
by = {}
for r in tp:
    by.setdefault(r["repo"], {})[r["period"]] = r
TP_METRICS = ["active_per_week", "commits_per_cw", "pr_commits_per_cw", "prod_lines_per_cw",
              "bugfix_share", "test_share", "revert_share", "hotfix_share", "ai_share"]
changes = []
for repo, d in sorted(by.items()):
    if "before" not in d or "after" not in d:
        continue
    row = dict(repo=repo, weeks_before=d["before"]["calendar_weeks"], weeks_after=d["after"]["calendar_weeks"])
    for m in TP_METRICS:
        b, a = float(d["before"][m]), float(d["after"][m])
        row[m + "_before"], row[m + "_after"], row[m + "_change_pct"] = b, a, rel(b, a)
    changes.append(row)
write("raw_throughput_changes.csv", changes)
out["throughput"] = {}
for i, m in enumerate(TP_METRICS):
    vals = [r[m + "_change_pct"] for r in changes]
    d = describe(vals, seed=7000 + i)
    d["n_zero_before"] = sum(v is None for v in vals)
    d["median_before"] = st.median(r[m + "_before"] for r in changes)
    d["median_after"] = st.median(r[m + "_after"] for r in changes)
    out["throughput"][m] = d
# Sum-of-counts view of the hard-to-see rare events (reverts): pooled across repos
out["reverts_pooled"] = {p: dict(
    commits=sum(int(by[r][p]["commits"]) for r in by if p in by[r]),
    reverts=round(sum(float(by[r][p]["revert_share"]) * int(by[r][p]["commits"]) for r in by if p in by[r])),
    hotfixes=round(sum(float(by[r][p]["hotfix_share"]) * int(by[r][p]["commits"]) for r in by if p in by[r])))
    for p in ("before", "after")}

# ---------------------------------------------------------------- B. snapshots + D. language
snaps, lang = [], {}
for name in sorted(MEASURED):
    cx = json.load(open(os.path.join(RUNS, name, "complexity.json")))
    ss = [s for s in cx.get("snapshots", []) if s.get("functions")]
    if len(ss) < 2:
        continue
    first, last = ss[0], ss[-1]
    bl = last.get("byLanguage") or {}
    tot = sum(v.get("functions", 0) for v in bl.values()) or 1
    top = max(bl.items(), key=lambda kv: kv[1].get("functions", 0)) if bl else (None, {})
    lang[name] = dict(primary=top[0], share=round(top[1].get("functions", 0) / tot, 3))
    adopt = REPOS[name]["adoption"] or None
    row = dict(repo=name, status="dated" if adopt else "undated", snapshots=len(ss),
               first=first["date"][:10], last=last["date"][:10],
               lines_first=first["lines"], lines_last=last["lines"],
               functions_first=first["functions"], functions_last=last["functions"],
               complex_share_first=first["complexFunctions"] / first["functions"],
               complex_share_last=last["complexFunctions"] / last["functions"],
               excess_per_kloc_first=first["excessPerKloc"], excess_per_kloc_last=last["excessPerKloc"],
               sampled_fraction_min=min((s.get("sampling") or {}).get("fraction", 1) if isinstance(s.get("sampling"), dict) else 1 for s in ss),
               primary_language=top[0], primary_language_share=lang[name]["share"])
    row["complex_share_change_pct"] = rel(row["complex_share_first"], row["complex_share_last"])
    row["excess_per_kloc_change_pct"] = rel(row["excess_per_kloc_first"], row["excess_per_kloc_last"])
    row["lines_change_pct"] = rel(row["lines_first"], row["lines_last"])
    if adopt:
        pre = [s for s in ss if s["date"][:7] < adopt]
        post = [s for s in ss if s["date"][:7] >= adopt]
        if pre and post:
            row["complex_share_at_adoption"] = pre[-1]["complexFunctions"] / pre[-1]["functions"]
            row["complex_share_change_since_adoption_pct"] = rel(row["complex_share_at_adoption"], row["complex_share_last"])
            row["complex_share_change_before_adoption_pct"] = rel(row["complex_share_first"], row["complex_share_at_adoption"])
            row["months_pre"] = len(pre)
            row["months_post"] = len(post)
            # Percentage-point change in the complex-function share per month, before vs since adoption
            def months(a, b):
                return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])
            m_pre = months(first["date"], pre[-1]["date"])
            m_post = months(pre[-1]["date"], last["date"])
            if m_pre >= 3 and m_post >= 3:
                row["pp_per_month_before"] = 100 * (row["complex_share_at_adoption"] - row["complex_share_first"]) / m_pre
                row["pp_per_month_after"] = 100 * (row["complex_share_last"] - row["complex_share_at_adoption"]) / m_post
    snaps.append(row)
write("raw_snapshots.csv", snaps)
out["snapshots"] = {}
for arm in ("all", "dated", "undated"):
    rows = [r for r in snaps if arm == "all" or r["status"] == arm]
    out["snapshots"][arm] = dict(
        n=len(rows),
        complex_share=describe([r["complex_share_change_pct"] for r in rows], seed=7100),
        excess_per_kloc=describe([r["excess_per_kloc_change_pct"] for r in rows], seed=7101),
        lines=describe([r["lines_change_pct"] for r in rows], seed=7102),
        complex_share_first_median=st.median(r["complex_share_first"] for r in rows),
        complex_share_last_median=st.median(r["complex_share_last"] for r in rows),
    )
dated_rows = [r for r in snaps if "complex_share_change_since_adoption_pct" in r]
out["snapshots"]["dated_split"] = dict(
    n=len(dated_rows),
    before_adoption=describe([r["complex_share_change_before_adoption_pct"] for r in dated_rows], seed=7103),
    since_adoption=describe([r["complex_share_change_since_adoption_pct"] for r in dated_rows], seed=7104))
pace = [r for r in snaps if "pp_per_month_after" in r]
diffs = [r["pp_per_month_after"] - r["pp_per_month_before"] for r in pace]
out["snapshots"]["pace"] = dict(n=len(pace), faster_after=sum(d > 0 for d in diffs), slower_after=sum(d < 0 for d in diffs),
                                median_pp_before=st.median(r["pp_per_month_before"] for r in pace),
                                median_pp_after=st.median(r["pp_per_month_after"] for r in pace),
                                median_diff=st.median(diffs), sign_p=__import__("stats_util").sign_test(sum(d > 0 for d in diffs), sum(d != 0 for d in diffs)))
langs = {}
for r in snaps:
    langs.setdefault(r["primary_language"], []).append(r["repo"])
out["languages"] = {k: sorted(v) for k, v in sorted(langs.items(), key=lambda kv: -len(kv[1]))}
out["parser_coverage"] = sorted(((r["repo"], json.load(open(os.path.join(RUNS, r["repo"], "complexity.json")))["snapshots"][-1]["coverage"]["share"]) for r in snaps), key=lambda x: x[1])
# Language segment (TypeScript incl. TSX vs everything else), dated repos, audit before/after changes
ba = list(csv.DictReader(open(os.path.join(BENCH, "data", "metrics.csv"))))
group = {r["repo"]: ("TypeScript" if r["primary_language"] in ("typescript", "tsx") else "Other") for r in snaps}
out["language_segments"] = {}
for k, metric in (("cyc", "cyclomatic delta (per 100 production lines added)"), ("lpc", "production lines added per commit"),
                  ("rw90", "lines rewritten within 90 days")):
    for g in ("TypeScript", "Other"):
        vals = [100 * float(r["relative"]) for r in ba if r["metric"] == metric and r["relative"] and group.get(r["repo"]) == g]
        out["language_segments"][f"{k}_{g}"] = describe(vals, seed=7500)
out["language_other_dated"] = sorted(r["repo"] for r in snaps if r["status"] == "dated" and group[r["repo"]] == "Other")

# ---------------------------------------------------------------- C. within-period AI vs unlabelled
within = []
for name in sorted(MEASURED):
    for fn, key, label in (("complexity.json", "withinPeriodRate", "complexity density"),
                           ("churn.json", "withinPeriod", "rework edits per 100 lines"),
                           ("cost.json", "withinPeriod", "follow-ups per change")):
        w = json.load(open(os.path.join(RUNS, name, fn))).get(key)
        if not w or w.get("aiValue") is None:
            continue
        within.append(dict(repo=name, status="dated" if REPOS[name]["adoption"] else "undated", metric=label,
                           period=w.get("period"), ai_n=w.get("aiN"), unattributed_n=w.get("unattributedN"),
                           ai_value=w.get("aiValue"), unattributed_value=w.get("unattributedValue"),
                           relative_pct=None if w.get("relative") is None else 100 * w["relative"], p=w.get("p"),
                           caveats=" | ".join(w.get("caveats") or [])))
write("raw_within.csv", within)
out["within"] = {}
for j, label in enumerate(("complexity density", "rework edits per 100 lines", "follow-ups per change")):
    rows = [r for r in within if r["metric"] == label and r["relative_pct"] is not None and (r["ai_n"] or 0) >= 20]
    d = describe([r["relative_pct"] for r in rows], seed=7200 + j)
    d["min_ai_n"] = 20
    d["repos_excluded_small_ai_n"] = sum(1 for r in within if r["metric"] == label and (r["ai_n"] or 0) < 20)
    d["significant_higher_ai"] = sum(1 for r in rows if r["p"] is not None and r["p"] <= 0.05 and r["relative_pct"] > 0)
    d["significant_lower_ai"] = sum(1 for r in rows if r["p"] is not None and r["p"] <= 0.05 and r["relative_pct"] < 0)
    d["with_p"] = sum(1 for r in rows if r["p"] is not None)
    out["within"][label] = d
# Same comparison restricted to codebases with an adoption date (after adoption), the report's before/after group
out["within_dated"] = {}
for j, label in enumerate(("complexity density", "rework edits per 100 lines", "follow-ups per change")):
    rows = [r for r in within if r["metric"] == label and r["status"] == "dated" and r["relative_pct"] is not None and (r["ai_n"] or 0) >= 20]
    out["within_dated"][label] = describe([r["relative_pct"] for r in rows], seed=7250 + j)

# ---------------------------------------------------------------- E. AI share vs complexity slope
tr = list(csv.DictReader(open(os.path.join(BENCH, "data", "trends.csv"))))
cyc = [r for r in tr if r["metric"].startswith("cyclomatic delta (per 100") and r["slope_per_month"]]
share = {n: float(r["ai_share"] or 0) for n, r in REPOS.items() if r["ai_share"]}
for label, rows in (("established", [r for r in cyc if r["status"] == "shown"]),
                    ("fitted", [r for r in cyc if r["status"] != "unfitted"])):
    rho, p = spearman_perm([share[r["repo"]] for r in rows], [float(r["slope_per_month"]) for r in rows], seed=7300)
    out[f"ai_share_vs_cyc_slope_{label}"] = dict(n=len(rows), rho=rho, p=p)

# ---------------------------------------------------------------- F. bug-fix classifier precision
lab_path = os.path.join(DATA, "raw_kinds_labelled.csv")
if os.path.exists(lab_path):
    lab = list(csv.DictReader(open(lab_path)))
    yes = sum(r["is_bugfix"] == "yes" for r in lab)
    unclear = sum(r["is_bugfix"] == "unclear" for r in lab)
    out["bugfix_precision"] = dict(n=len(lab), yes=yes, unclear=unclear, no=len(lab) - yes - unclear,
                                   precision_strict=yes / len(lab), precision_lenient=(yes + unclear) / len(lab))

json.dump(out, open(os.path.join(DATA, "raw_results.json"), "w"), indent=1, default=float)


def show(d):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}


for m, d in out["throughput"].items():
    print("TP", m, show(d))
print("reverts", out["reverts_pooled"])
for k, d in out["snapshots"].items():
    print("SNAP", k, json.dumps(d, default=lambda v: round(v, 3))[:600])
for k, d in out["within"].items():
    print("WITHIN", k, show(d))
print("LANG", {k: len(v) for k, v in out["languages"].items()})
print("RHO", out["ai_share_vs_cyc_slope_established"], out["ai_share_vs_cyc_slope_fitted"])
print("PREC", out.get("bugfix_precision"))
