"""Production lines committed, net of rewriting: lines that survive 30 / 90 days.

For each codebase with an adoption date, per active contributor-week:
  gross     = production lines added (data/raw_throughput_changes.csv)
  rewritten = gross x share of added lines rewritten or deleted within N days
              (audit's forward blame measure, data/before_after.csv)
  surviving = gross x (1 - that share)
before vs after adoption, as a % change per codebase.

The rewrite share is only measured per period (the audit samples commits per
period and blames forward), so there is no monthly series to adjust a monthly
growth rate with. Within a period the share is constant, so the monthly growth
rate of surviving lines equals that of gross lines (19_lines_rate.py); the
adjustment changes the before -> after level, which is what this script reports.

Output: data/net_lines.csv, data/net_lines.json
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats_util import describe  # noqa: E402

DATA = os.path.join(HERE, "data")
thr = {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, "raw_throughput_changes.csv")))}
ba = {}
for r in csv.DictReader(open(os.path.join(DATA, "before_after.csv"))):
    ba[(r["repo"], r["metric"])] = r


def f(x):
    return None if x in ("", "None", None) else float(x)


rows = []
for repo, t in sorted(thr.items()):
    g0, g1 = f(t["prod_lines_per_cw_before"]), f(t["prod_lines_per_cw_after"])
    if not g0 or g1 is None:
        continue
    row = dict(repo=repo, gross_before=round(g0, 1), gross_after=round(g1, 1), gross_change_pct=round(100 * (g1 / g0 - 1), 1))
    for n in (30, 90):
        b = ba.get((repo, f"lines rewritten within {n} days"))
        if not b or f(b["before"]) is None or f(b["after"]) is None:
            continue
        s0, s1 = f(b["before"]), f(b["after"])
        row[f"rw{n}_share_before"], row[f"rw{n}_share_after"] = s0, s1
        k0, k1 = g0 * (1 - s0), g1 * (1 - s1)
        row[f"surv{n}_before"], row[f"surv{n}_after"] = round(k0, 1), round(k1, 1)
        row[f"surv{n}_change_pct"] = round(100 * (k1 / k0 - 1), 1)
    rows.append(row)

fields = sorted({k for r in rows for k in r}, key=lambda k: list(max(rows, key=len)).index(k))
with open(os.path.join(DATA, "net_lines.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)


def summ(key, seed):
    d = describe([r[key] for r in rows if r.get(key) is not None], seed=seed)
    return dict(n=d["n"], median=round(d["median"], 1), ci=[round(d["ci_low"], 1), round(d["ci_high"], 1)],
                rose=d["rose"], fell=d["fell"], p=round(d["sign_p"], 4))


out = dict(gross=summ("gross_change_pct", 9400), surviving30=summ("surv30_change_pct", 9401), surviving90=summ("surv90_change_pct", 9402))
json.dump(out, open(os.path.join(DATA, "net_lines.json"), "w"), indent=1)
for k, v in out.items():
    print(k, v)
