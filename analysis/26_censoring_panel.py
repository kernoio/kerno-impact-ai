"""Two robustness checks added 2026-11-02 (fix list items 18 and 19).

A. Recent commits and 90-day measures. The audit's 90-day rework and survival use the
   same commits as its 30-day horizon, so commits from the final 90 days of the window
   are counted at 90 days before 90 days have passed. Per dated codebase: share of
   after-adoption (non-bot) commits within 90 / 30 days of the codebase's last commit.
   Then: does the 90-day rework change hold where that share is low, and does it track it?

B. Fixed set of codebases. Monthly median of complexity density (decision points per 100
   production lines, bots excluded, months >= 1,000 lines) on the two-year per-commit data,
   all codebases vs fixed panels present in nearly every month; growth of the median from
   January 2025 to September 2026 (log-linear fit).

Output: data/censoring_panel.json
"""
import csv, json, math, os, statistics as st, sys, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from stats_util import describe, spearman  # noqa: E402
RUNS = os.path.join(HERE, "raw", "zip", "audit-bench", "runs")
repos = {r["repo"]: r for r in csv.DictReader(open(os.path.join(HERE, "data", "repos.csv")))}
P = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
out = {}

late, late30 = {}, {}
for n, m in repos.items():
    if not m["adoption"] or not os.path.exists(os.path.join(RUNS, n, "timeline.json")):
        continue
    cs = [c for c in json.load(open(os.path.join(RUNS, n, "timeline.json")))["commits"] if c.get("date") and not c["isBot"]]
    end = max(P(c["date"]) for c in cs); after = [c for c in cs if c["date"][:7] >= m["adoption"]]
    late[n] = sum((end - P(c["date"])).days < 90 for c in after) / len(after)
    late30[n] = sum((end - P(c["date"])).days < 30 for c in after) / len(after)
ba = list(csv.DictReader(open(os.path.join(HERE, "raw", "zip", "audit-bench", "data", "metrics.csv"))))
out["late_share_90_median"] = st.median(late.values()); out["late_share_30_median"] = st.median(late30.values())
for metric, key in (("lines rewritten within 90 days", "rw90"), ("lines rewritten within 30 days", "rw30")):
    v = {r["repo"]: 100 * float(r["relative"]) for r in ba if r["metric"] == metric and r["relative"] and r["repo"] in late}
    for lab, cut in (("all", 2), ("lt40", 0.4), ("lt25", 0.25)):
        out[f"{key}_{lab}"] = describe([v[k] for k in v if late[k] < cut], seed=2600)
    ks = sorted(v); out[f"{key}_rho_late"] = spearman([late[k] for k in ks], [v[k] for k in ks])

ser = {}
for n in repos:
    p = os.path.join(RUNS, n)
    if not os.path.exists(os.path.join(p, "complexity.json")):
        continue
    bots = {c["sha"] for c in json.load(open(os.path.join(p, "timeline.json")))["commits"] if c["isBot"]}
    agg = {}
    for c in json.load(open(os.path.join(p, "complexity.json")))["commits"]:
        if c["sha"] in bots or not c.get("date") or not c.get("productionLinesAdded"):
            continue
        a = agg.setdefault(c["date"][:7], [0, 0]); a[0] += c["cyclomaticDelta"]; a[1] += c["productionLinesAdded"]
    ser[n] = {m: 100 * d / l for m, (d, l) in agg.items() if l >= 1000}
core = sorted({m for s in ser.values() for m in s if "2024-10" <= m <= "2026-09"})
def growth(rs):
    pts = []
    for i, m in enumerate(core):
        v = [ser[r][m] for r in rs if m in ser[r]]
        if m >= "2025-01" and v: pts.append((i, math.log(st.median(v))))
    mx = st.mean(x for x, _ in pts); my = st.mean(y for _, y in pts)
    return 100 * (math.exp(sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)) - 1)
out["panel_all_growth"] = growth(list(ser))
for miss in (0, 2, 4):
    panel = [r for r in ser if sum(m not in ser[r] for m in core) <= miss]
    out[f"panel_miss{miss}"] = dict(n=len(panel), growth=growth(panel))
json.dump(out, open(os.path.join(HERE, "data", "censoring_panel.json"), "w"), indent=1, default=float)
print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items() if not isinstance(v, dict) or "growth" in v}, indent=1))
print("rw90 lt40:", {k: out["rw90_lt40"][k] for k in ("n", "median", "fell", "sign_p")})
