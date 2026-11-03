"""Do commits that add more complexity get fixed more often later, at the same size?

Design (fixed before looking at results):
  unit       non-bot commits with >= 5 production lines added, every measured repository,
             whole audit window (no adoption split)
  exposure   complexity density of the commit (cyclomatic delta per 100 production lines),
             "high" = above the median density of commits of similar size in the same repo
  size match commits are binned into deciles of production lines added within each repo;
             high and low are compared only inside a bin
  outcome    the commit's lines are later edited (within the audit's 90-day follow-up window)
             by a commit the audit classifies as a bug fix. Follow-ups flagged as sweep,
             revert or hot file are dropped, as in the audit's own rates. Secondary outcome:
             any follow-up edit at all.
  per repo   Mantel-Haenszel risk ratio across size bins (high vs low density)
  across     per-repo % difference, median, bootstrap CI and sign test, as elsewhere;
             repos need >= 20 fix-follow-up events
Caveat: the bug-fix label is the audit's subject-line classifier (70-88% precise on our
hand check) and misses fixes in repos that don't use "fix:" prefixes.

Output: data/raw_complexity_fixes.csv, adds "complexity_fixes" to data/raw_results.json
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
MIN_LINES, BINS, MIN_EVENTS = 5, 10, 20


def mh_rr(strata):
    """Mantel-Haenszel risk ratio. strata: list of (events_hi, n_hi, events_lo, n_lo)."""
    num = sum(a * n0 / (n1 + n0) for a, n1, c, n0 in strata if n1 and n0)
    den = sum(c * n1 / (n1 + n0) for a, n1, c, n0 in strata if n1 and n0)
    return None if not den else num / den


rows = []
for name, meta in sorted(REPOS.items()):
    if meta["status"] not in ("measured", "undated"):
        continue
    run = os.path.join(BENCH, "runs", name)
    tl = json.load(open(os.path.join(run, "timeline.json")))["commits"]
    kind = {c["sha"]: c["changeKind"] for c in tl}
    bots = {c["sha"] for c in tl if c["isBot"]}
    cx = [c for c in json.load(open(os.path.join(run, "complexity.json")))["commits"]
          if c["sha"] not in bots and c["productionLinesAdded"] >= MIN_LINES]
    if len(cx) < 100:
        continue
    fixed, followed = set(), set()
    for f in json.load(open(os.path.join(run, "followups.json")))["followups"]:
        if f["isSweep"] or f["isRevert"] or f["isHotFile"]:
            continue
        followed.add(f["originSha"])
        if kind.get(f["sha"]) == "bugfix":
            fixed.add(f["originSha"])
    cx.sort(key=lambda c: c["productionLinesAdded"])
    k = len(cx)
    strata_fix, strata_any = [], []
    for b in range(BINS):
        part = cx[b * k // BINS:(b + 1) * k // BINS]
        dens = [100 * c["cyclomaticDelta"] / c["productionLinesAdded"] for c in part]
        med = st.median(dens)
        hi = [c for c, d in zip(part, dens) if d > med]
        lo = [c for c, d in zip(part, dens) if d <= med]
        strata_fix.append((sum(c["sha"] in fixed for c in hi), len(hi), sum(c["sha"] in fixed for c in lo), len(lo)))
        strata_any.append((sum(c["sha"] in followed for c in hi), len(hi), sum(c["sha"] in followed for c in lo), len(lo)))
    events = sum(a + c for a, _, c, _ in strata_fix)
    n_hi = sum(n1 for _, n1, _, _ in strata_fix)
    n_lo = sum(n0 for _, _, _, n0 in strata_fix)
    rr_fix, rr_any = mh_rr(strata_fix), mh_rr(strata_any)
    rows.append(dict(repo=name, status="dated" if meta["adoption"] else "undated", commits=k, high=n_hi, low=n_lo,
                     fix_events=events, fix_rate_high=sum(a for a, *_ in strata_fix) / n_hi if n_hi else None,
                     fix_rate_low=sum(c for _, _, c, _ in strata_fix) / n_lo if n_lo else None,
                     rr_fix=rr_fix, rr_any=rr_any,
                     fix_gap_pct=None if rr_fix is None else 100 * (rr_fix - 1),
                     any_gap_pct=None if rr_any is None else 100 * (rr_any - 1)))

with open(os.path.join(DATA, "raw_complexity_fixes.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
use = [r for r in rows if r["fix_events"] >= MIN_EVENTS and r["fix_gap_pct"] is not None]
res = dict(repos=len(use), repos_too_few_events=len(rows) - len(use),
           commits=sum(r["commits"] for r in use), fix_events=sum(r["fix_events"] for r in use),
           fix=describe([r["fix_gap_pct"] for r in use], seed=7600),
           any=describe([r["any_gap_pct"] for r in use], seed=7601),
           fix_rate_high_median=st.median(r["fix_rate_high"] for r in use),
           fix_rate_low_median=st.median(r["fix_rate_low"] for r in use))
allres = json.load(open(os.path.join(DATA, "raw_results.json")))
allres["complexity_fixes"] = res
json.dump(allres, open(os.path.join(DATA, "raw_results.json"), "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=lambda v: round(v, 3)))
