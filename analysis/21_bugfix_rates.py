"""Bug-fix commits relative to output, and their monthly growth, before vs after adoption.

Bug-fix commits are the audit's changeKind = 'bugfix' (subject-line classifier;
precision checked in data/raw_kinds_labelled.csv). Non-bot commits (merges kept, as most are PR merges)
inside the audit window, as in 11_raw_commits.py.

  per KLOC    bug-fix commits per 1,000 production lines added (complexity.json
              commits), before vs after adoption, % change per codebase
  monthly     steady monthly growth rate of bug-fix commits per month, fitted on
              log counts (months with >= MIN_FIX fixes), as in 17_monthly_rate.py

Codebases: those with an adoption date.
Output: data/bugfix_rates.csv, data/bugfix_rates.json
"""
import csv
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats_util import describe  # noqa: E402

DATA = os.path.join(HERE, "data")
BENCH = os.path.join(HERE, "raw", "zip", "audit-bench")
MIN_MONTHS, MIN_FIX = 4, 5
meta = {r["name"]: r for r in json.load(open(os.path.join(BENCH, "data", "monthly.json")))["repos"]}


def mi(m):
    return int(m[:4]) * 12 + int(m[5:7])


def rate(pts):
    if len(pts) < MIN_MONTHS:
        return None
    xs, ys = [p[0] for p in pts], [math.log(p[1]) for p in pts]
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return None if sxx == 0 else 100 * (math.exp(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx) - 1)


rows = []
for name, m in sorted(meta.items()):
    adopt = m["adoption"]
    run = os.path.join(BENCH, "runs", name)
    if not adopt or not os.path.exists(os.path.join(run, "complexity.json")):
        continue
    lo, hi = m["since"][:7], m["until"][:7]
    tl = [c for c in json.load(open(os.path.join(run, "timeline.json")))["commits"]
          if not c["isBot"] and c.get("date") and m["since"][:10] <= c["date"][:10] <= m["until"][:10]]
    plines = {c["sha"]: c["productionLinesAdded"] for c in json.load(open(os.path.join(run, "complexity.json")))["commits"]}
    fixes, lines, monthly = defaultdict(int), defaultdict(int), defaultdict(int)
    for c in tl:
        per = "after" if c["date"][:7] >= adopt else "before"
        lines[per] += plines.get(c["sha"], 0)
        if c["changeKind"] == "bugfix":
            fixes[per] += 1
            monthly[c["date"][:7]] += 1
    row = dict(repo=name, adoption=adopt, fixes_before=fixes["before"], fixes_after=fixes["after"],
               kloc_before=round(lines["before"] / 1000, 1), kloc_after=round(lines["after"] / 1000, 1))
    k0 = fixes["before"] / (lines["before"] / 1000) if lines["before"] else None
    k1 = fixes["after"] / (lines["after"] / 1000) if lines["after"] else None
    row["per_kloc_before"], row["per_kloc_after"] = k0, k1
    row["per_kloc_change_pct"] = 100 * (k1 / k0 - 1) if k0 and k1 is not None else None
    pts = [(mi(mo), n, mo) for mo, n in sorted(monthly.items()) if n >= MIN_FIX]
    row["monthly_before"] = rate([p for p in pts if p[2] < adopt])
    row["monthly_after"] = rate([p for p in pts if p[2] >= adopt])
    rows.append(row)

with open(os.path.join(DATA, "bugfix_rates.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


def summ(vals, seed):
    vals = [v for v in vals if v is not None]
    d = describe(vals, seed=seed)
    return dict(n=d["n"], median=round(d["median"], 2), ci=[round(d["ci_low"], 2), round(d["ci_high"], 2)],
                rose=d["rose"], fell=d["fell"], p=round(d["sign_p"], 4))


paired = [r for r in rows if r["monthly_before"] is not None and r["monthly_after"] is not None]
out = dict(
    per_kloc_change=summ([r["per_kloc_change_pct"] for r in rows], 9500),
    per_kloc_before_median=st.median(r["per_kloc_before"] for r in rows if r["per_kloc_before"] is not None),
    per_kloc_after_median=st.median(r["per_kloc_after"] for r in rows if r["per_kloc_after"] is not None),
    monthly_before=summ([r["monthly_before"] for r in paired], 9501),
    monthly_after=summ([r["monthly_after"] for r in paired], 9502),
    monthly_diff=summ([r["monthly_after"] - r["monthly_before"] for r in paired], 9503),
)
json.dump(out, open(os.path.join(DATA, "bugfix_rates.json"), "w"), indent=1)
for k, v in out.items():
    print(k, v)
