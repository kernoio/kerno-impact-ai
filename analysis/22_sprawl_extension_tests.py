"""Codebase size growth, repair vs extension of follow-ups, and whether tests keep up.

A. Codebase size (sprawl). Production lines in the whole tree from the audit's
   snapshots (complexity.json:snapshots[].lines). Per codebase: % growth first to
   last snapshot, and the steady monthly growth rate (log-linear fit on snapshot
   dates). Trend group = codebases with a fitted complexity trend; before/after =
   codebases with an adoption date and >= MIN_SNAPS snapshots on each side.

B. Repair vs extension. Each judged follow-up carries an LLM verdict: repair,
   extension or unrelated (followups.json). As the field guide says, verdicts below
   0.5 confidence are discarded. Shares are of confident verdicts, by the origin
   commit's period (before/after adoption), and after adoption split by whether the
   origin commit is AI-attributed (exposure high/medium) or not.

C. Tests vs changes. Test-change commits (changeKind = 'test') per active
   contributor-week and per 1,000 production lines added, before vs after; and the
   monthly growth rate of test commits next to that of production lines
   (19_lines_rate.py method), so "keeping up" means test commits growing at least as
   fast as code.

D. Lines committed in codebases without an adoption date (from data/lines_rate.csv).

E. Monthly growth of the test-commit share of commits (months with >= 20 commits):
   codebases without an adoption date (trend group, whole window) vs codebases with
   one, before and after adoption. Used to ask whether a trend is new with AI.

Output: data/sprawl_extension_tests.csv (per codebase), data/sprawl_extension_tests.json
"""
import csv
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats_util import describe  # noqa: E402

DATA = os.path.join(HERE, "data")
BENCH = os.path.join(HERE, "raw", "zip", "audit-bench")
MIN_MONTHS, MIN_SNAPS, MIN_CONF, MIN_TEST, MIN_LINES = 4, 3, 0.5, 5, 1000
meta = {r["name"]: r for r in json.load(open(os.path.join(BENCH, "data", "monthly.json")))["repos"]}
FITTED = {r["repo"] for r in csv.DictReader(open(os.path.join(DATA, "trends.csv")))
          if r["metric"].startswith("cyclomatic delta (per 100") and r["status"] != "unfitted"}


def mi(m):
    return int(m[:4]) * 12 + int(m[5:7])


def mfrac(d):
    """Month index with day fraction, for snapshot dates."""
    return int(d[:4]) * 12 + int(d[5:7]) + (int(d[8:10]) - 1) / 30.5


def rate(pts, min_n=MIN_MONTHS):
    pts = [p for p in pts if p[1] > 0]
    if len(pts) < min_n:
        return None
    xs, ys = [p[0] for p in pts], [math.log(p[1]) for p in pts]
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return None if sxx == 0 else 100 * (math.exp(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx) - 1)


def week(d):
    import datetime
    y, w, _ = datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10])).isocalendar()
    return y, w


rows = []
for name, m in sorted(meta.items()):
    run = os.path.join(BENCH, "runs", name)
    if not os.path.exists(os.path.join(run, "complexity.json")):
        continue
    adopt = m["adoption"]
    cx = json.load(open(os.path.join(run, "complexity.json")))
    row = dict(repo=name, adoption=adopt or "", trend_group=name in FITTED)
    # A. size
    sn = [(s["date"][:10], s["lines"]) for s in cx["snapshots"] if s.get("lines")]
    sn.sort()
    if len(sn) >= 2:
        row["size_first"], row["size_last"] = sn[0][1], sn[-1][1]
        row["size_growth_pct"] = 100 * (sn[-1][1] / sn[0][1] - 1)
        row["size_months"] = round(mfrac(sn[-1][0]) - mfrac(sn[0][0]), 1)
        pts = [(mfrac(d), v, d[:7]) for d, v in sn]
        row["size_rate_all"] = rate(pts, MIN_SNAPS)
        if adopt:
            row["size_rate_before"] = rate([p for p in pts if p[2] < adopt], MIN_SNAPS)
            row["size_rate_after"] = rate([p for p in pts if p[2] >= adopt], MIN_SNAPS)
    # B. repair vs extension
    if adopt:
        fu = json.load(open(os.path.join(run, "followups.json")))["followups"]
        cnt = defaultdict(lambda: defaultdict(int))
        for x in fu:
            j = x.get("judgement")
            if not isinstance(j, dict) or (j.get("confidence") or 0) < MIN_CONF or x.get("isSweep") or x.get("isRevert") or x.get("isHotFile"):
                continue
            per = "after" if x["originDate"][:7] >= adopt else "before"
            cnt[per][j["verdict"]] += 1
            if per == "after":
                arm = "ai" if x.get("originExposure") in ("high", "medium") else "un"
                cnt[arm][j["verdict"]] += 1
        for k in ("before", "after", "ai", "un"):
            tot = sum(cnt[k].values())
            row[f"judged_{k}"] = tot
            row[f"repair_{k}"] = cnt[k]["repair"] / tot if tot else None
            row[f"extension_{k}"] = cnt[k]["extension"] / tot if tot else None
    # C. tests vs changes
    if adopt:
        tl = [c for c in json.load(open(os.path.join(run, "timeline.json")))["commits"]
              if not c["isBot"] and c.get("date") and m["since"][:10] <= c["date"][:10] <= m["until"][:10]]
        pl = {c["sha"]: c["productionLinesAdded"] for c in cx["commits"]}
        tests, lines, cw = defaultdict(int), defaultdict(int), defaultdict(set)
        tmon, lmon = defaultdict(int), defaultdict(int)
        for c in tl:
            per = "after" if c["date"][:7] >= adopt else "before"
            lines[per] += pl.get(c["sha"], 0)
            lmon[c["date"][:7]] += pl.get(c["sha"], 0)
            cw[per].add((c["authorEmail"], week(c["date"])))
            if c["changeKind"] == "test":
                tests[per] += 1
                tmon[c["date"][:7]] += 1
        for per in ("before", "after"):
            row[f"tests_{per}"] = tests[per]
            row[f"tests_per_cw_{per}"] = tests[per] / len(cw[per]) if cw[per] else None
            row[f"tests_per_kloc_{per}"] = tests[per] / (lines[per] / 1000) if lines[per] else None
        tp = [(mi(mo), n, mo) for mo, n in sorted(tmon.items()) if n >= MIN_TEST]
        lp = [(mi(mo), v, mo) for mo, v in sorted(lmon.items()) if v >= MIN_LINES]
        for per, sel in (("before", lambda p: p[2] < adopt), ("after", lambda p: p[2] >= adopt)):
            row[f"test_rate_{per}"] = rate([p for p in tp if sel(p)])
            row[f"line_rate_{per}"] = rate([p for p in lp if sel(p)])
    # E. test-commit share of all commits per month: whole window (all codebases) and after adoption (dated)
    tl_all = [c for c in json.load(open(os.path.join(run, "timeline.json")))["commits"]
              if not c["isBot"] and c.get("date") and m["since"][:10] <= c["date"][:10] <= m["until"][:10]]
    tot, tst = defaultdict(int), defaultdict(int)
    for c in tl_all:
        tot[c["date"][:7]] += 1
        tst[c["date"][:7]] += c["changeKind"] == "test"
    sp = [(mi(mo), tst[mo] / tot[mo], mo) for mo in sorted(tot) if tot[mo] >= 20 and tst[mo] > 0]
    row["test_share_rate_all"] = rate(sp)
    if adopt:
        row["test_share_rate_before"] = rate([p for p in sp if p[2] < adopt])
        row["test_share_rate_after"] = rate([p for p in sp if p[2] >= adopt])
    rows.append(row)

fields = []
for r in rows:
    for k in r:
        if k not in fields:
            fields.append(k)
with open(os.path.join(DATA, "sprawl_extension_tests.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)


def summ(vals, seed):
    vals = [v for v in vals if v is not None]
    d = describe(vals, seed=seed)
    return dict(n=d["n"], median=round(d["median"], 2), ci=[round(d["ci_low"], 2), round(d["ci_high"], 2)],
                rose=d["rose"], fell=d["fell"], p=round(d["sign_p"], 4))


def chg(r, a, b):
    return 100 * (r[b] / r[a] - 1) if r.get(a) and r.get(b) is not None else None


def med(vals):
    vals = [v for v in vals if v is not None]
    return st.median(vals) if vals else None


trend = [r for r in rows if r["trend_group"]]
dated = [r for r in rows if r["adoption"]]
sz_pair = [r for r in dated if r.get("size_rate_before") is not None and r.get("size_rate_after") is not None]
rx = [r for r in dated if r.get("repair_before") is not None and r.get("repair_after") is not None]
ai = [r for r in dated if r.get("judged_ai", 0) >= 10 and r.get("judged_un", 0) >= 10]
tr_pair = [r for r in dated if r.get("test_rate_before") is not None and r.get("test_rate_after") is not None]
lr = {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, "lines_rate.csv")))}
out = dict(
    size=dict(
        growth=summ([r.get("size_growth_pct") for r in trend], 9600),
        months_median=med(r.get("size_months") for r in trend),
        first_median=med(r.get("size_first") for r in trend), last_median=med(r.get("size_last") for r in trend),
        rate_all=summ([r.get("size_rate_all") for r in trend], 9601),
        rate_before=summ([r["size_rate_before"] for r in sz_pair], 9602),
        rate_after=summ([r["size_rate_after"] for r in sz_pair], 9603),
        rate_diff=summ([r["size_rate_after"] - r["size_rate_before"] for r in sz_pair], 9604),
    ),
    judged=dict(
        repair_before_median=med(r["repair_before"] for r in rx), repair_after_median=med(r["repair_after"] for r in rx),
        extension_before_median=med(r["extension_before"] for r in rx), extension_after_median=med(r["extension_after"] for r in rx),
        repair_change=summ([chg(r, "repair_before", "repair_after") for r in rx], 9610),
        extension_change=summ([chg(r, "extension_before", "extension_after") for r in rx], 9611),
        judged_median_before=med(r["judged_before"] for r in rx), judged_median_after=med(r["judged_after"] for r in rx),
        ai_n=len(ai),
        repair_ai_median=med(r["repair_ai"] for r in ai), repair_un_median=med(r["repair_un"] for r in ai),
        extension_ai_median=med(r["extension_ai"] for r in ai), extension_un_median=med(r["extension_un"] for r in ai),
        repair_ai_gap=summ([100 * (r["repair_ai"] - r["repair_un"]) for r in ai], 9612),
        extension_ai_gap=summ([100 * (r["extension_ai"] - r["extension_un"]) for r in ai], 9613),
    ),
    tests=dict(
        per_cw_change=summ([chg(r, "tests_per_cw_before", "tests_per_cw_after") for r in dated], 9620),
        per_kloc_change=summ([chg(r, "tests_per_kloc_before", "tests_per_kloc_after") for r in dated], 9621),
        per_kloc_before_median=med(r.get("tests_per_kloc_before") for r in dated),
        per_kloc_after_median=med(r.get("tests_per_kloc_after") for r in dated),
        test_rate_before=summ([r["test_rate_before"] for r in tr_pair], 9622),
        test_rate_after=summ([r["test_rate_after"] for r in tr_pair], 9623),
        line_rate_after_same=summ([r["line_rate_after"] for r in tr_pair], 9624),
        test_minus_line_after=summ([r["test_rate_after"] - r["line_rate_after"] for r in tr_pair if r["line_rate_after"] is not None], 9625),
    ),
    test_share_rate_undated=summ([r.get("test_share_rate_all") for r in trend if not r["adoption"]], 9640),
    test_share_rate_before=summ([r["test_share_rate_before"] for r in dated if r.get("test_share_rate_before") is not None and r.get("test_share_rate_after") is not None], 9641),
    test_share_rate_after=summ([r["test_share_rate_after"] for r in dated if r.get("test_share_rate_before") is not None and r.get("test_share_rate_after") is not None], 9642),
    lines_undated=summ([float(lr[r]["lines_all"]) for r in lr if lr[r]["adoption"] == "" and r in FITTED and lr[r]["lines_all"] not in ("", "None")], 9630),
    lines_per_author_undated=summ([float(lr[r]["per_author_all"]) for r in lr if lr[r]["adoption"] == "" and r in FITTED and lr[r]["per_author_all"] not in ("", "None")], 9631),
)
json.dump(out, open(os.path.join(DATA, "sprawl_extension_tests.json"), "w"), indent=1)
for k, v in out.items():
    if isinstance(v, dict) and "n" not in v:
        for a, b in v.items():
            print(k, a, b)
    else:
        print(k, v)
