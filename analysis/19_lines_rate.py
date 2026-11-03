"""Average monthly growth rate of production lines committed, before vs after AI adoption.

Same method as 17_monthly_rate.py. For each codebase and month inside the audit
window: production lines added (complexity.json commits, non-bot), the number of
active non-bot authors, and lines per active author. Fit log(value) on month index
by least squares; report exp(slope) - 1, the steady monthly rate.

Before / after: codebases with an adoption date and >= MIN_MONTHS usable months on
each side (month < adoption = before). Whole window: codebases with a fitted
complexity trend (trends.csv), the report's trend group. Months with fewer than
MIN_LINES production lines are dropped as too thin.

Output: data/lines_rate.csv, data/lines_rate.json
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
MIN_MONTHS, MIN_LINES = 4, 1000
meta = {r["name"]: r for r in json.load(open(os.path.join(BENCH, "data", "monthly.json")))["repos"]}
FITTED = {r["repo"] for r in csv.DictReader(open(os.path.join(DATA, "trends.csv")))
          if r["metric"].startswith("cyclomatic delta (per 100") and r["status"] != "unfitted"}


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
    run = os.path.join(BENCH, "runs", name)
    if not os.path.exists(os.path.join(run, "complexity.json")):
        continue
    tl = json.load(open(os.path.join(run, "timeline.json")))["commits"]
    who = {c["sha"]: c["authorEmail"] for c in tl if not c["isBot"]}
    lines, authors = defaultdict(int), defaultdict(set)
    for c in json.load(open(os.path.join(run, "complexity.json")))["commits"]:
        mo = c["date"][:7]
        if c["sha"] not in who or not (m["since"][:7] <= mo <= m["until"][:7]):
            continue
        lines[mo] += c["productionLinesAdded"]
        authors[mo].add(who[c["sha"]])
    months = sorted(mo for mo in lines if lines[mo] >= MIN_LINES)
    adopt = m["adoption"]
    row = dict(repo=name, adoption=adopt or "", months=len(months))
    for key, val in (("lines", lambda mo: lines[mo]), ("per_author", lambda mo: lines[mo] / len(authors[mo]))):
        pts = [(mi(mo), val(mo), mo) for mo in months]
        row[key + "_all"] = rate(pts)
        row[key + "_before"] = rate([p for p in pts if adopt and p[2] < adopt]) if adopt else None
        row[key + "_after"] = rate([p for p in pts if adopt and p[2] >= adopt]) if adopt else None
    rows.append(row)

with open(os.path.join(DATA, "lines_rate.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


def summ(vals, seed):
    vals = [v for v in vals if v is not None]
    d = describe(vals, seed=seed)
    return dict(n=d["n"], median=round(d["median"], 2), ci=[round(d["ci_low"], 2), round(d["ci_high"], 2)],
                rose=d["rose"], fell=d["fell"], p=round(d["sign_p"], 3))


out = {}
for i, key in enumerate(("lines", "per_author")):
    paired = [x for x in rows if x[key + "_before"] is not None and x[key + "_after"] is not None]
    out[key] = dict(
        whole_window_trend_group=summ([x[key + "_all"] for x in rows if x["repo"] in FITTED], 9300 + 10 * i),
        before=summ([x[key + "_before"] for x in paired], 9301 + 10 * i),
        after=summ([x[key + "_after"] for x in paired], 9302 + 10 * i),
        after_minus_before=summ([x[key + "_after"] - x[key + "_before"] for x in paired], 9303 + 10 * i),
    )
json.dump(out, open(os.path.join(DATA, "lines_rate.json"), "w"), indent=1)
for k, v in out.items():
    for a, b in v.items():
        print(k, a, b)
