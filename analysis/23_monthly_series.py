"""Month-by-month complexity density around AI adoption (event time).

For each codebase with an adoption date: monthly complexity density (cyclomatic
delta per 100 production lines added) from raw/zip/audit-bench/data/monthly.json,
inside the audit window, months with >= MIN_DEN production lines (as in
17_monthly_rate.py). Months are re-labelled relative to the adoption month
(0 = adoption month). Each codebase is indexed to its own baseline, the mean of
months -6..-1 (needs >= BASE_MIN of them), so codebases at different levels can
be compared: 100 = the six months before adoption.

Per relative month we report the median index, the interquartile range and how
many codebases contribute. Months with fewer than MIN_N codebases are dropped.

Output: data/monthly_series.csv, data/monthly_series.json
"""
import csv
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SRC = os.path.join(HERE, "raw", "zip", "audit-bench", "data", "monthly.json")
MIN_DEN, BASE_MIN, MIN_N = 1000, 3, 10

doc = json.load(open(SRC))


def mi(m):
    return int(m[:4]) * 12 + int(m[5:7])


per_rel = {}
used = 0
for r in doc["repos"]:
    adopt = r["adoption"]
    ser = r["series"].get("complexity")
    if not adopt or not ser:
        continue
    lo, hi = r["since"][:7], r["until"][:7]
    dens = {}
    for m, v in zip(r["months"], ser):
        if v is None or not (lo <= m <= hi):
            continue
        num, den = v[0] + v[3] + v[6], v[1] + v[4] + v[7]
        if den >= MIN_DEN:
            dens[mi(m) - mi(adopt)] = num / den
    base = [dens[k] for k in range(-6, 0) if k in dens]
    if len(base) < BASE_MIN or st.mean(base) <= 0:
        continue
    b = st.mean(base)
    used += 1
    for k, v in dens.items():
        per_rel.setdefault(k, []).append(100 * v / b)


def q(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    i = int(k)
    return xs[i] + (xs[min(i + 1, len(xs) - 1)] - xs[i]) * (k - i)


rows = []
for k in sorted(per_rel):
    xs = per_rel[k]
    if len(xs) >= MIN_N:
        rows.append(dict(rel_month=k, n=len(xs), median=round(st.median(xs), 1), q1=round(q(xs, 0.25), 1), q3=round(q(xs, 0.75), 1)))
with open(os.path.join(DATA, "monthly_series.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

pre = [x for x in rows if x["rel_month"] < 0]
post = [x for x in rows if x["rel_month"] >= 0]
out = dict(codebases=used, months=[rows[0]["rel_month"], rows[-1]["rel_month"]],
           pre_first=pre[0], pre_last=pre[-1], post_last=post[-1],
           post_median_of_medians=round(st.median(x["median"] for x in post), 1),
           pre_median_of_medians=round(st.median(x["median"] for x in pre), 1),
           last3_post=round(st.mean(x["median"] for x in post[-3:]), 1))
json.dump(out, open(os.path.join(DATA, "monthly_series.json"), "w"), indent=1)
print(out)
for x in rows:
    print(x)
