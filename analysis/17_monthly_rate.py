"""Average monthly growth rate of complexity density, before vs after AI adoption.

For each project, complexity density per month = sum of cyclomatic-delta numerators
over sum of production-line denominators across all three attribution arms
(raw/zip/audit-bench/data/monthly.json, written by the audit's monthly.py), kept
inside the audit window. We fit log(density) on month index by least squares and
report exp(slope) - 1: the steady monthly rate that best fits the series.

Whole window: projects with a fitted complexity trend (trends.csv) and >= MIN_MONTHS usable months.
Before / after: dated projects with >= MIN_MONTHS usable months on each side of
the adoption month (month < adoption = before, as the audit splits it).
Months with no production lines or zero density are dropped (log undefined).

Output: data/monthly_rate.csv, data/monthly_rate.json
"""
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats_util import describe  # noqa: E402

DATA = os.path.join(HERE, "data")
SRC = os.path.join(HERE, "raw", "zip", "audit-bench", "data", "monthly.json")
MIN_MONTHS = 4
MIN_DEN = 1000  # production lines in a month; thinner months are too noisy

doc = json.load(open(SRC))
# The report's trend base: codebases with a fitted complexity-density trend
FITTED = {r["repo"] for r in csv.DictReader(open(os.path.join(DATA, "trends.csv")))
          if r["metric"].startswith("cyclomatic delta (per 100") and r["status"] != "unfitted"}
keys = [m["key"] for m in doc["metrics"]]


def mi(m):
    y, mo = m.split("-")
    return int(y) * 12 + int(mo)


def rate(points):
    if len(points) < MIN_MONTHS:
        return None
    xs = [p[0] for p in points]
    ys = [math.log(p[1]) for p in points]
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return 100 * (math.exp(b) - 1)


def build(min_den, min_months):
  global MIN_MONTHS
  MIN_MONTHS = min_months
  rows = []
  for r in doc["repos"]:
      lo, hi = r["since"][:7], r["until"][:7]
      ser = r["series"].get("complexity")
      if not ser:
          continue
      pts = []
      for m, v in zip(r["months"], ser):
          if v is None or not (lo <= m <= hi):
              continue
          num = v[0] + v[3] + v[6]
          den = v[1] + v[4] + v[7]
          if den >= min_den and num > 0:
              pts.append((mi(m), num / den, m))
      adopt = r["adoption"]
      before = [p for p in pts if adopt and p[2] < adopt]
      after = [p for p in pts if adopt and p[2] >= adopt]
      rows.append(dict(repo=r["name"], adoption=adopt or "", months=len(pts),
                       rate_all=rate(pts), months_before=len(before), months_after=len(after),
                       rate_before=rate(before) if adopt else None,
                       rate_after=rate(after) if adopt else None))
  MIN_MONTHS = 4
  return rows


rows = build(MIN_DEN, MIN_MONTHS)
with open(os.path.join(DATA, "monthly_rate.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)


def summ(vals, seed):
    vals = [v for v in vals if v is not None]
    d = describe(vals, seed=seed)
    return dict(n=d["n"], median=round(d["median"], 2), ci=[round(d["ci_low"], 2), round(d["ci_high"], 2)],
                rose=d["rose"], fell=d["fell"], p=round(d["sign_p"], 3))


paired = [x for x in rows if x["rate_before"] is not None and x["rate_after"] is not None]
out = dict(
    method=f"log-linear fit per project; months with >= {MIN_DEN} production lines; >= {MIN_MONTHS} months per fit",
    whole_window=summ([x["rate_all"] for x in rows if x["repo"] in FITTED], 9100),
    dated_whole_window=summ([x["rate_all"] for x in rows if x["adoption"]], 9101),
    before=summ([x["rate_before"] for x in paired], 9102),
    after=summ([x["rate_after"] for x in paired], 9103),
    after_minus_before=summ([x["rate_after"] - x["rate_before"] for x in paired], 9104),
    after_all_dated=summ([x["rate_after"] for x in rows if x["rate_after"] is not None], 9105),
    undated_whole_window=summ([x["rate_all"] for x in rows if not x["adoption"] and x["repo"] in FITTED], 9106),
)
# Sensitivity: thinner/thicker month filters and longer minimum fits
sens = []
for den, mm in ((1, 4), (1000, 3), (1000, 6), (5000, 4)):
    rr = build(den, mm)
    pp = [x for x in rr if x["rate_before"] is not None and x["rate_after"] is not None]
    sens.append(dict(min_lines=den, min_months=mm, after=summ([x["rate_after"] for x in pp], 9110),
                     before=summ([x["rate_before"] for x in pp], 9111),
                     diff=summ([x["rate_after"] - x["rate_before"] for x in pp], 9112)))
out["sensitivity"] = sens
out["paired_n"] = len(paired)
out["paired_before_months_median"] = st.median(x["months_before"] for x in paired)
out["paired_after_months_median"] = st.median(x["months_after"] for x in paired)
json.dump(out, open(os.path.join(DATA, "monthly_rate.json"), "w"), indent=1)
for k, v in out.items():
    print(k, v)
