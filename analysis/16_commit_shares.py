"""Anchor headline results to the whole dataset: share of all commits analysed.

Each headline result is a count of codebases out of whichever group a test can
use (30 with an adoption date, 44 with a trend, ...). Readers find the changing
denominators hard to follow, so for each headline we also report the share of
ALL commits analysed (201,576 across 46 codebases) that sit in the codebases
the result applies to, plus the share sitting in codebases the test could not
assess. The two shares and "the rest" always add to 100% of the dataset.

Output: data/commit_shares.json
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
repos = {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, "repos.csv")))}
commits = {k: int(v["commits"]) for k, v in repos.items() if v["commits"] not in ("", "None")}
TOTAL = sum(commits.values())
ba = list(csv.DictReader(open(os.path.join(DATA, "before_after.csv"))))
tr = list(csv.DictReader(open(os.path.join(DATA, "trends.csv"))))
thr = list(csv.DictReader(open(os.path.join(DATA, "raw_throughput_changes.csv"))))
ab = list(csv.DictReader(open(os.path.join(DATA, "raw_absolute.csv"))))


def f(x):
    return None if x in ("", "None", None) else float(x)


def share(names):
    return sum(commits.get(n, 0) for n in names) / TOTAL


def ba_split(metric, up_is=True):
    rows = {x["repo"]: f(x["change_pct"]) for x in ba if x["metric"] == metric}
    yes = [r for r, v in rows.items() if v is not None and (v > 0 if up_is else v < 0)]
    assessed = [r for r, v in rows.items() if v is not None]
    return yes, assessed


out = {"total_commits": TOTAL, "codebases": len(repos)}
groups = {
    "dated": [k for k, v in repos.items() if v["status"] == "measured"],
    "undated": [k for k, v in repos.items() if v["status"] == "undated"],
}
cyc = "cyclomatic delta (per 100 production lines added)"
trend_rows = {x["repo"]: x for x in tr if x["metric"] == cyc}
groups["trend"] = list(trend_rows)
groups["trend_rise"] = [r for r, x in trend_rows.items() if x["status"] == "shown" and f(x["slope_per_month"]) > 0]
groups["trend_fall"] = [r for r, x in trend_rows.items() if x["status"] == "shown" and f(x["slope_per_month"]) < 0]
groups["trend_none"] = [r for r, x in trend_rows.items() if x["status"] in ("flat", "unestablished", "withheld")]
groups["trend_fitted"] = [r for r, x in trend_rows.items() if x["status"] != "unfitted"]
groups["trend_nodata"] = [r for r, x in trend_rows.items() if x["status"] == "unfitted"]
groups["cyc_rose"], _ = ba_split(cyc, True)
groups["cyc_fell"], _ = ba_split(cyc, False)
groups["lpc_rose"], _ = ba_split("production lines added per commit", True)
groups["rw90_fell"], _ = ba_split("lines rewritten within 90 days", False)
groups["tp_lines_rose"] = [x["repo"] for x in thr if f(x["prod_lines_per_cw_change_pct"]) and f(x["prod_lines_per_cw_change_pct"]) > 0]
groups["tp_test_rose"] = [x["repo"] for x in thr if f(x["test_share_change_pct"]) and f(x["test_share_change_pct"]) > 0]
groups["ab_rw30_rose"] = [x["repo"] for x in ab if f(x["rewritten30_per_cw_change_pct"]) and f(x["rewritten30_per_cw_change_pct"]) > 0]
groups["ab_rw90_rose"] = [x["repo"] for x in ab if f(x["rewritten90_per_cw_change_pct"]) and f(x["rewritten90_per_cw_change_pct"]) > 0]
groups["ab_bug_rose"] = [x["repo"] for x in ab if f(x["bugfix_per_cw_change_pct"]) and f(x["bugfix_per_cw_change_pct"]) > 0]
snaps = list(csv.DictReader(open(os.path.join(DATA, "raw_snapshots.csv"))))
groups["sn_rose"] = [x["repo"] for x in snaps if f(x["complex_share_change_pct"]) and f(x["complex_share_change_pct"]) > 0]
for k, names in groups.items():
    out[k] = dict(codebases=len(names), commits=sum(commits.get(n, 0) for n in names), share_of_all=round(share(names), 4))
json.dump(out, open(os.path.join(DATA, "commit_shares.json"), "w"), indent=1)
for k, v in out.items():
    print(k, v)
