"""Size check on the AI-labelled vs unlabelled follow-up gap.

The audit's within-period comparison (cost.json:withinPeriod) finds AI-labelled
commits get more follow-ups per change. AI-labelled commits might simply be
bigger, and a bigger change has more lines to revisit. Here we recompute, from
the raw rows, follow-ups per change AND per 100 production lines added, for
AI-labelled (exposure high/medium) vs unlabelled origin commits, in the same
period the audit used (after adoption for dated repos, the whole window for
undated ones). Follow-up records flagged as sweep, revert or hot file are
dropped, as the audit does for its headline rates.

Output: data/raw_followups_size.csv, adds "followups_size" to data/raw_results.json
"""
import csv
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # run with python3 -I
from stats_util import describe

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BENCH = os.path.join(HERE, "raw", "zip", "audit-bench")
REPOS = {r["name"]: r for r in csv.DictReader(open(os.path.join(BENCH, "data", "repositories.csv")))}

rows = []
for name, meta in sorted(REPOS.items()):
    if meta["status"] not in ("measured", "undated"):
        continue
    run = os.path.join(BENCH, "runs", name)
    adopt = meta["adoption"] or None
    bots = {c["sha"] for c in json.load(open(os.path.join(run, "timeline.json")))["commits"] if c["isBot"]}
    cx = json.load(open(os.path.join(run, "complexity.json")))["commits"]
    origin = {}
    for c in cx:
        if c["sha"] in bots or (adopt and c["date"][:7] < adopt):
            continue
        origin[c["sha"]] = dict(ai=c["exposure"] != "unknown", lines=c["productionLinesAdded"], n=0)
    for f in json.load(open(os.path.join(run, "followups.json")))["followups"]:
        o = origin.get(f["originSha"])
        if o is None or f["isSweep"] or f["isRevert"] or f["isHotFile"]:
            continue
        o["n"] += 1
    arms = {}
    for o in origin.values():
        a = arms.setdefault(o["ai"], dict(changes=0, lines=0, fu=0, sizes=[]))
        a["changes"] += 1
        a["lines"] += o["lines"]
        a["fu"] += o["n"]
        a["sizes"].append(o["lines"])
    ai, un = arms.get(True), arms.get(False)
    if not ai or not un or ai["changes"] < 20 or not ai["lines"] or not un["lines"]:
        continue
    r = dict(repo=name, period="after" if adopt else "all", ai_changes=ai["changes"], un_changes=un["changes"],
             ai_fu_per_change=ai["fu"] / ai["changes"], un_fu_per_change=un["fu"] / un["changes"],
             ai_fu_per_100_lines=100 * ai["fu"] / ai["lines"], un_fu_per_100_lines=100 * un["fu"] / un["lines"],
             ai_median_lines=st.median(ai["sizes"]), un_median_lines=st.median(un["sizes"]))
    for k in ("fu_per_change", "fu_per_100_lines", "median_lines"):
        u = r["un_" + k]
        r[k + "_gap_pct"] = None if not u else 100 * (r["ai_" + k] / u - 1)
    rows.append(r)

with open(os.path.join(DATA, "raw_followups_size.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
res = {k: describe([r[k + "_gap_pct"] for r in rows], seed=7400 + i)
       for i, k in enumerate(("fu_per_change", "fu_per_100_lines", "median_lines"))}
allres = json.load(open(os.path.join(DATA, "raw_results.json")))
allres["followups_size"] = res
# Codebases with an adoption date only (after adoption), the report's before/after group
allres["followups_size_dated"] = {k: describe([r[k + "_gap_pct"] for r in rows if r["period"] != "all"], seed=7450 + i)
                                  for i, k in enumerate(("fu_per_change", "fu_per_100_lines", "median_lines"))}
json.dump(allres, open(os.path.join(DATA, "raw_results.json"), "w"), indent=1, default=float)
for k, d in res.items():
    print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in d.items()})
