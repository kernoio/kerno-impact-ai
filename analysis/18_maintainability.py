"""Maintainability grade per codebase, from the audit's stock complexity measure.

The field guide's stock metric is excess complexity per KLOC: every function above
cyclomatic 10 contributes what it carries above that line, divided by 1,000
production lines (complexity.json:snapshots, summarised in data/raw_snapshots.csv).
Functions above 10 are the ones the Software Engineering Institute's bands rate
moderate risk or worse.

There is no published scale for excess per KLOC, so the grade is relative to this
benchmark: cut-offs are the quartiles of the FIRST snapshot across the codebases,
A = least excess. The same cut-offs grade the LAST snapshot, so a change of grade
is a real move against a fixed scale, not a re-ranking.

Codebases: the ones with a fitted complexity-density trend (trends.csv status
other than 'unfitted'), the report's second base group.

Output: data/maintainability.csv, data/maintainability.json
"""
import csv
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats_util import describe  # noqa: E402

DATA = os.path.join(HERE, "data")
CYC = "cyclomatic delta (per 100 production lines added)"
trend = {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, "trends.csv"))) if r["metric"] == CYC and r["status"] != "unfitted"}
snaps = {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, "raw_snapshots.csv")))}
repos = sorted(set(trend) & set(snaps))

first = sorted(float(snaps[r]["excess_per_kloc_first"]) for r in repos)


def quantile(xs, q):
    k = (len(xs) - 1) * q
    lo = int(k)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (k - lo)


cuts = [quantile(first, q) for q in (0.25, 0.5, 0.75)]


def grade(v):
    return "ABCD"[sum(v > c for c in cuts)]


rows = []
for r in repos:
    s = snaps[r]
    ef, el = float(s["excess_per_kloc_first"]), float(s["excess_per_kloc_last"])
    cf, cl = float(s["complex_share_first"]), float(s["complex_share_last"])
    t = trend[r]
    rows.append(dict(repo=r, status=s["status"], first=s["first"], last=s["last"],
                     excess_first=round(ef, 2), excess_last=round(el, 2), excess_change_pct=round(100 * (el / ef - 1), 1) if ef else None,
                     complex_share_first=round(cf, 4), complex_share_last=round(cl, 4),
                     grade_first=grade(ef), grade_last=grade(el),
                     trend_status=t["status"], trend_slope=t["slope_per_month"]))
rows.sort(key=lambda x: (x["grade_last"], x["excess_last"]))
with open(os.path.join(DATA, "maintainability.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

worse = [x for x in rows if x["grade_last"] > x["grade_first"]]
better = [x for x in rows if x["grade_last"] < x["grade_first"]]
ex = describe([x["excess_change_pct"] for x in rows if x["excess_change_pct"] is not None], seed=9200)
cs = describe([100 * (x["complex_share_last"] / x["complex_share_first"] - 1) for x in rows if x["complex_share_first"]], seed=9201)
out = dict(
    n=len(rows), cuts=[round(c, 2) for c in cuts],
    grade_counts_first={g: sum(x["grade_first"] == g for x in rows) for g in "ABCD"},
    grade_counts_last={g: sum(x["grade_last"] == g for x in rows) for g in "ABCD"},
    moved_worse=[f'{x["repo"]} {x["grade_first"]}→{x["grade_last"]}' for x in worse],
    moved_better=[f'{x["repo"]} {x["grade_first"]}→{x["grade_last"]}' for x in better],
    excess_change=dict(median=round(ex["median"], 1), ci=[round(ex["ci_low"], 1), round(ex["ci_high"], 1)], rose=ex["rose"], fell=ex["fell"], p=ex["sign_p"]),
    complex_share_change=dict(median=round(cs["median"], 1), ci=[round(cs["ci_low"], 1), round(cs["ci_high"], 1)], rose=cs["rose"], fell=cs["fell"], p=cs["sign_p"]),
    complex_share_first_median=st.median(x["complex_share_first"] for x in rows),
    complex_share_last_median=st.median(x["complex_share_last"] for x in rows),
    excess_first_median=st.median(x["excess_first"] for x in rows),
    excess_last_median=st.median(x["excess_last"] for x in rows),
)
json.dump(out, open(os.path.join(DATA, "maintainability.json"), "w"), indent=1, ensure_ascii=False)
for k, v in out.items():
    print(k, v)
