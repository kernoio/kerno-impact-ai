"""Absolute volumes per engineer: are there more fixes and more rewrites in total?

Shares can fall while totals rise, because each engineer now ships more code.
Per dated repository, before vs after the adoption month:
  bug-fix commits per contributor-week = bug-fix share x commits per contributor-week
                                         (both from data/raw_throughput.csv)
  lines rewritten within 30 / 90 days per contributor-week (estimate)
      = audit's rewrite share (data/before_after.csv) x production lines per contributor-week.
      The audit measures the share on a sample of commits, so this is an estimate.

Output: data/raw_absolute.csv, adds "absolute" to data/raw_results.json
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # run with python3 -I
from stats_util import describe

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
tp = list(csv.DictReader(open(os.path.join(DATA, "raw_throughput.csv"))))
ba = {(r["repo"], r["metric"]): r for r in csv.DictReader(open(os.path.join(DATA, "before_after.csv")))}
by = {}
for r in tp:
    by.setdefault(r["repo"], {})[r["period"]] = r


def f(x):
    return float(x) if x not in ("", None) else None


rows = []
for repo, d in sorted(by.items()):
    if "before" not in d or "after" not in d:
        continue
    b, a = d["before"], d["after"]
    row = dict(repo=repo)
    fb = f(b["bugfix_share"]) * f(b["commits_per_cw"])
    fa = f(a["bugfix_share"]) * f(a["commits_per_cw"])
    row["bugfix_per_cw_before"], row["bugfix_per_cw_after"] = fb, fa
    row["bugfix_per_cw_change_pct"] = 100 * (fa / fb - 1) if fb else None
    for win in ("30", "90"):
        x = ba.get((repo, f"lines rewritten within {win} days"))
        rb, ra = (f(x["before"]), f(x["after"])) if x else (None, None)
        lb, la = f(b["prod_lines_per_cw"]), f(a["prod_lines_per_cw"])
        ok = rb and lb and ra is not None
        row[f"rewritten{win}_per_cw_before"] = rb * lb if ok else None
        row[f"rewritten{win}_per_cw_after"] = ra * la if ok else None
        row[f"rewritten{win}_per_cw_change_pct"] = 100 * ((ra * la) / (rb * lb) - 1) if ok else None
    rows.append(row)

with open(os.path.join(DATA, "raw_absolute.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
res = {k: describe([r[k + "_change_pct"] for r in rows], seed=7700 + i)
       for i, k in enumerate(("bugfix_per_cw", "rewritten30_per_cw", "rewritten90_per_cw"))}
allres = json.load(open(os.path.join(DATA, "raw_results.json")))
allres["absolute"] = res
json.dump(allres, open(os.path.join(DATA, "raw_results.json"), "w"), indent=1, default=float)
for k, d in res.items():
    print(k, {a: (round(v, 3) if isinstance(v, float) else v) for a, v in d.items()})
