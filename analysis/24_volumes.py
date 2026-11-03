"""Volumes behind the headline percentages: counts, not only rates.

For each codebase with an adoption date, before vs after adoption:
  per engineer-week (active contributor-week, as in 11_raw_commits.py)
    production lines committed            data/raw_throughput_changes.csv
    lines rewritten within 90 days        data/raw_absolute.csv (gross x audit rewrite share)
    lines still in place after 90 days    data/net_lines.csv
    bug-fix commits                       data/raw_absolute.csv
    test-change commits                   data/sprawl_extension_tests.csv
  per month (whole codebase)
    bug-fix commits, test-change commits, all commits  (timeline.json, non-bot, audit window)
  per 1,000 production lines committed
    test-change commits                   data/sprawl_extension_tests.csv
AI-attributed vs unattributed, after adoption (data/raw_followups_size.csv):
    follow-ups per change, median production lines per commit.

Reported as the median level before and after, plus the per-codebase % change
(median, CI, sign test) where a change is meaningful.
Output: data/volumes.json, data/volumes.csv
"""
import csv
import json
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats_util import describe  # noqa: E402

DATA = os.path.join(HERE, "data")
BENCH = os.path.join(HERE, "raw", "zip", "audit-bench")


def load(n):
    return {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, n)))}


def f(x):
    return None if x in ("", "None", None) else float(x)


thr, ab, nl, sx = load("raw_throughput_changes.csv"), load("raw_absolute.csv"), load("net_lines.csv"), load("sprawl_extension_tests.csv")
meta = {r["name"]: r for r in json.load(open(os.path.join(BENCH, "data", "monthly.json")))["repos"]}

rows = []
for name, m in sorted(meta.items()):
    adopt = m["adoption"]
    if not adopt or name not in thr:
        continue
    row = dict(repo=name)
    row["lines_cw_before"], row["lines_cw_after"] = f(thr[name]["prod_lines_per_cw_before"]), f(thr[name]["prod_lines_per_cw_after"])
    if name in ab:
        row["rw90_cw_before"], row["rw90_cw_after"] = f(ab[name]["rewritten90_per_cw_before"]), f(ab[name]["rewritten90_per_cw_after"])
        row["bug_cw_before"], row["bug_cw_after"] = f(ab[name]["bugfix_per_cw_before"]), f(ab[name]["bugfix_per_cw_after"])
    if name in nl:
        row["surv90_cw_before"], row["surv90_cw_after"] = f(nl[name].get("surv90_before")), f(nl[name].get("surv90_after"))
    if name in sx:
        row["test_cw_before"], row["test_cw_after"] = f(sx[name]["tests_per_cw_before"]), f(sx[name]["tests_per_cw_after"])
        row["test_kloc_before"], row["test_kloc_after"] = f(sx[name]["tests_per_kloc_before"]), f(sx[name]["tests_per_kloc_after"])
    # whole-codebase monthly counts
    tl = [c for c in json.load(open(os.path.join(BENCH, "runs", name, "timeline.json")))["commits"]
          if not c["isBot"] and c.get("date") and m["since"][:10] <= c["date"][:10] <= m["until"][:10]]
    months, cnt = defaultdict(set), defaultdict(lambda: defaultdict(int))
    for c in tl:
        per = "after" if c["date"][:7] >= adopt else "before"
        months[per].add(c["date"][:7])
        cnt[per]["all"] += 1
        cnt[per][c["changeKind"]] += 1
    for per in ("before", "after"):
        k = len(months[per])
        row[f"months_{per}"] = k
        for kind, key in (("all", "commits_mo"), ("bugfix", "bug_mo"), ("test", "test_mo")):
            row[f"{key}_{per}"] = cnt[per][kind] / k if k else None
    rows.append(row)

fields = []
for r in rows:
    for k in r:
        if k not in fields:
            fields.append(k)
with open(os.path.join(DATA, "volumes.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)


def level(key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(st.median(vals), 3) if vals else None


def change(key, seed):
    vals = [100 * (r[key + "_after"] / r[key + "_before"] - 1) for r in rows
            if r.get(key + "_before") and r.get(key + "_after") is not None]
    d = describe(vals, seed=seed)
    return dict(n=d["n"], median=round(d["median"], 1), ci=[round(d["ci_low"], 1), round(d["ci_high"], 1)],
                rose=d["rose"], fell=d["fell"], p=round(d["sign_p"], 4))


out = {}
for i, key in enumerate(("lines_cw", "rw90_cw", "surv90_cw", "bug_cw", "test_cw", "test_kloc", "commits_mo", "bug_mo", "test_mo")):
    out[key] = dict(before=level(key + "_before"), after=level(key + "_after"), change=change(key, 9700 + i))
fs = [r for r in csv.DictReader(open(os.path.join(DATA, "raw_followups_size.csv"))) if r["period"] != "all"]
out["ai_followups_per_change"] = round(st.median(float(r["ai_fu_per_change"]) for r in fs if f(r["ai_fu_per_change"]) is not None), 2)
out["un_followups_per_change"] = round(st.median(float(r["un_fu_per_change"]) for r in fs if f(r["un_fu_per_change"]) is not None), 2)
out["ai_median_lines"] = st.median(float(r["ai_median_lines"]) for r in fs if f(r["ai_median_lines"]) is not None)
out["un_median_lines"] = st.median(float(r["un_median_lines"]) for r in fs if f(r["un_median_lines"]) is not None)
json.dump(out, open(os.path.join(DATA, "volumes.json"), "w"), indent=1)
for k, v in out.items():
    print(k, v)
