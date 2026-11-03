"""Commit-level measures from the raw benchmark (runs/<repo>/timeline.json, complexity.json).

Per repository:
  data quality  bot and merge commits, commits dated outside the window, change kinds
  throughput    per active contributor-week, before vs after the adoption month:
                commits, PR-linked commits, production lines added
  team size     mean active (non-bot) contributors per week
  kinds         share of commits the audit classifies as bugfix / test, and the
                share whose subject is a revert or mentions a hotfix

Definitions (also in the report):
  active contributor-week  one distinct non-bot author email with >= 1 commit in an ISO week
  before / after           commit date's month < / >= the audit's adoption month,
                           restricted to the audit window [since, until]
  bot                      timeline isBot flag (set by the audit)

Output: data/raw_quality.csv, data/raw_throughput.csv (one row per repo x period),
        data/raw_kinds_sample.csv (seeded sample of 100 'bugfix' commits for hand review)
"""
import csv
import datetime as dt
import json
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RUNS = os.path.join(HERE, "raw", "zip", "audit-bench", "runs")
REPOS = {r["name"]: r for r in csv.DictReader(open(os.path.join(HERE, "raw", "zip", "audit-bench", "data", "repositories.csv")))}

# Paths that should never count as production code
NONPROD = re.compile(r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|go\.sum|composer\.lock|Gemfile\.lock|uv\.lock)$"
                     r"|(^|/)(vendor|vendored|third_party|node_modules)/|\.min\.(js|css)$|(^|/)dist/"
                     r"|zz_generated|_pb2(_grpc)?\.py$|\.pb\.go$|(^|/)generated[-_./]|[-_.]generated\.[a-z]+$|(^|/)__generated__/", re.I)
REVERT = re.compile(r"^\s*(\[?revert\b|revert:)", re.I)
HOTFIX = re.compile(r"\bhot[\s-]?fix", re.I)


def week(d):
    y, w, _ = d.isocalendar()
    return (y, w)


quality, through, bugfix_pool = [], [], []
for name in sorted(REPOS):
    meta = REPOS[name]
    if meta["status"] not in ("measured", "undated"):
        continue
    tl = json.load(open(os.path.join(RUNS, name, "timeline.json")))
    cx = json.load(open(os.path.join(RUNS, name, "complexity.json")))
    since, until = meta["since"], meta["until"]
    adopt = meta["adoption"] or None
    prod_lines = {c["sha"]: c["productionLinesAdded"] for c in cx.get("commits", [])}
    commits = tl["commits"]

    n = len(commits)
    bots = sum(c["isBot"] for c in commits)
    merges = sum(c["isMerge"] for c in commits)
    no_date = sum(not c.get("date") for c in commits)
    outside = sum(1 for c in commits if c.get("date") and not (since <= c["date"][:10] <= until))
    kinds = {}
    for c in commits:
        kinds[c["changeKind"]] = kinds.get(c["changeKind"], 0) + 1
    bot_shas = {c["sha"] for c in commits if c["isBot"]}
    prod_paths = [p for c in commits for p in c.get("productionFiles", [])]
    nonprod = [p for p in prod_paths if NONPROD.search(p)]
    quality.append(dict(repo=name, status="dated" if adopt else "undated", commits=n, bot_commits=bots,
                        bot_share=round(bots / n, 4), merge_commits=merges, missing_date=no_date,
                        dated_outside_window=outside, outside_share=round(outside / n, 4),
                        pr_linked=sum(c.get("prNumber") is not None for c in commits),
                        complexity_commits=len(prod_lines), complexity_commits_from_bots=sum(sh in bot_shas for sh in prod_lines),
                        production_paths=len(prod_paths), production_paths_lock_vendor_generated=len(nonprod),
                        nonprod_examples="; ".join(sorted(set(nonprod))[:3]),
                        **{f"kind_{k}": v for k, v in sorted(kinds.items())}))

    if not adopt:
        continue
    periods = {"before": [], "after": []}
    for c in commits:
        if c["isBot"] or not c.get("date") or not (since <= c["date"][:10] <= until):
            continue
        periods["before" if c["date"][:7] < adopt else "after"].append(c)
    for per, cs in periods.items():
        if not cs:
            continue
        cw = {}
        for c in cs:
            d = dt.date.fromisoformat(c["date"][:10])
            cw.setdefault(week(d), set()).add(c["authorEmail"].lower())
        contributor_weeks = sum(len(v) for v in cw.values())
        # Calendar weeks in the period, including weeks with no commits
        start = dt.date.fromisoformat(since if per == "before" else adopt + "-01")
        end = dt.date.fromisoformat(adopt + "-01") - dt.timedelta(days=1) if per == "before" else dt.date.fromisoformat(until)
        cal_weeks = len({week(start + dt.timedelta(days=i)) for i in range((end - start).days + 1)})
        k = len(cs)
        through.append(dict(
            repo=name, period=per, commits=k, calendar_weeks=cal_weeks, contributor_weeks=contributor_weeks,
            active_per_week=round(contributor_weeks / cal_weeks, 3),
            commits_per_cw=round(k / contributor_weeks, 4),
            pr_commits_per_cw=round(sum(c.get("prNumber") is not None for c in cs) / contributor_weeks, 4),
            prod_lines_per_cw=round(sum(prod_lines.get(c["sha"], 0) for c in cs) / contributor_weeks, 2),
            bugfix_share=round(sum(c["changeKind"] == "bugfix" for c in cs) / k, 4),
            test_share=round(sum(c["changeKind"] == "test" for c in cs) / k, 4),
            revert_share=round(sum(bool(REVERT.search(c["subject"] or "")) for c in cs) / k, 5),
            hotfix_share=round(sum(bool(HOTFIX.search(c["subject"] or "")) for c in cs) / k, 5),
            ai_share=round(sum(c["exposure"] != "unknown" for c in cs) / k, 4),
        ))
        for c in cs:
            if c["changeKind"] == "bugfix":
                bugfix_pool.append((name, c["sha"], c["subject"], c["exposure"]))
    print(name, {p: len(v) for p, v in periods.items()})


def write(fn, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(DATA, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


write("raw_quality.csv", quality)
write("raw_throughput.csv", through)
rnd = random.Random(20261022)
sample = rnd.sample(bugfix_pool, 100)
with open(os.path.join(DATA, "raw_kinds_sample.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["repo", "sha", "subject", "exposure"])
    w.writerows(sample)
print("bugfix pool", len(bugfix_pool))
