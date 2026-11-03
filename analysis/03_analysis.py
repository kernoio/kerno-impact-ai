"""Cross-repository analysis of the Kerno audit benchmark.

Unit of analysis: the repository. Each dated repository contributes one
before/after % change per metric (as computed by the Kerno audit); we then ask
how those per-repo changes are distributed across repositories.

Inputs:  data/repos.csv, data/before_after.csv, data/trends.csv,
         data/sweep_2026_02.csv, data/sweep_monthly.csv  (from 01/02)
Outputs: data/results_metric_summary.csv  per-metric distribution + tests
         data/results_segments.csv        segment medians
         data/results_trends.csv          trend counts by metric and dated/undated
         data/results_sweep.csv           monthly sweep shares
         data/results.json                every number quoted in the report
Standard library only. Bootstrap/permutation seeds are fixed.
"""
import csv
import json
import math
import os
import random
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
B = 10000  # bootstrap / permutation resamples


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))


def fnum(x):
    return None if x in ("", "None") else float(x)


repos = load("repos.csv")
ba = load("before_after.csv")
tr = load("trends.csv")
sweep_m = load("sweep_monthly.csv")
R = {r["repo"]: r for r in repos}

# Direction each metric is costly in. None = the audit declares it ambiguous.
DIRECTION = {
    "cyclomatic delta (per 100 production lines added)": "up",
    "cyclomatic delta per commit": "up",
    "excess complexity per KLOC": "up",
    "rework edits (per 100 lines added)": "up",
    "lines rewritten within 30 days": "up",
    "lines rewritten within 90 days": "up",
    "follow-ups (per change)": "up",
    "reimplementations (per KLOC added)": "up",
    "share of follow-ups that are repairs": "up",
    "production lines added per commit": None,
    "days to first follow-up": None,
}
GROUP = {
    "cyclomatic delta (per 100 production lines added)": "Code complexity",
    "cyclomatic delta per commit": "Code complexity",
    "excess complexity per KLOC": "Code complexity",
    "production lines added per commit": "Throughput (change size)",
    "rework edits (per 100 lines added)": "Rework and churn",
    "lines rewritten within 30 days": "Rework and churn",
    "lines rewritten within 90 days": "Rework and churn",
    "follow-ups (per change)": "Rework and churn",
    "days to first follow-up": "Rework and churn",
    "reimplementations (per KLOC added)": "Waste (duplication)",
    "share of follow-ups that are repairs": "Rework and churn",
}


# ---------------------------------------------------------------- statistics
def sign_test(k, n):
    """Exact two-sided binomial sign test, H0 p=0.5."""
    if n == 0:
        return None
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def boot_median_ci(xs, seed):
    if len(xs) < 3:
        return (None, None)
    rnd = random.Random(seed)
    meds = sorted(st.median(rnd.choices(xs, k=len(xs))) for _ in range(B))
    return (meds[int(0.025 * B)], meds[int(0.975 * B) - 1])


def quartiles(xs):
    if len(xs) < 2:
        return (None, None)
    q = st.quantiles(xs, n=4, method="inclusive")
    return (q[0], q[2])


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def spearman_perm(x, y, seed):
    rho = spearman(x, y)
    rnd = random.Random(seed)
    yy = list(y)
    hits = 0
    for _ in range(B):
        rnd.shuffle(yy)
        if abs(spearman(x, yy)) >= abs(rho) - 1e-12:
            hits += 1
    return rho, (hits + 1) / (B + 1)


def r(x, d=1):
    return None if x is None else round(x, d)


def describe(changes, direction, seed):
    xs = [c for c in changes if c is not None]
    up = sum(c > 0 for c in xs)
    down = sum(c < 0 for c in xs)
    lo, hi = boot_median_ci(xs, seed)
    q1, q3 = quartiles(xs)
    worse = up if direction == "up" else None
    better = down if direction == "up" else None
    return dict(n=len(xs), rose=up, fell=down, unchanged=len(xs) - up - down,
                worse=worse, better=better,
                median=r(st.median(xs)) if xs else None, q1=r(q1), q3=r(q3),
                mean=r(st.mean(xs)) if xs else None,
                ci_low=r(lo), ci_high=r(hi),
                sign_p=sign_test(up, up + down))


# --------------------------------------------------------- per-metric summary
out = {}
summary_rows = []
for i, (metric, direction) in enumerate(DIRECTION.items()):
    rows = [x for x in ba if x["metric"] == metric]
    allc = [fnum(x["change_pct"]) for x in rows]
    asserted = [fnum(x["change_pct"]) for x in rows if x["status"] == "asserted"]
    reasons = {}
    for x in rows:
        if x["status"] != "asserted":
            key = x["status"] + ": " + (x["reason"] or "")
            reasons[key] = reasons.get(key, 0) + 1
    for subset, vals in (("all rows with a ratio", allc), ("asserted rows only", asserted)):
        d = describe(vals, direction, seed=1000 + i)
        d.update(metric=metric, group=GROUP[metric], subset=subset,
                 direction="costly when up" if direction else "no declared direction",
                 rows=len(rows), status_counts=json.dumps(reasons))
        summary_rows.append(d)
        out.setdefault("metric_summary", {}).setdefault(metric, {})[subset] = d

fields = ["group", "metric", "subset", "direction", "rows", "n", "rose", "fell", "unchanged", "worse", "better",
          "median", "q1", "q3", "mean", "ci_low", "ci_high", "sign_p", "status_counts"]
with open(os.path.join(DATA, "results_metric_summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for d in summary_rows:
        w.writerow({k: d[k] for k in fields})

# Reproduce the PDF's own headline table (p.6-7) from the extracted rows
repro = {}
for metric in DIRECTION:
    a = [fnum(x["change_pct"]) for x in ba if x["metric"] == metric and x["status"] == "asserted"]
    repro[metric] = dict(asserted=len(a), median=r(st.median(a)) if a else None)
out["pdf_headline_reproduction"] = repro

# ------------------------------------------------------------ sensitivity
# Drop repos with <200 commits in window or adoption in the final two months
# (after arm of roughly a month or two): redash, Infisical, vendure.
drop = {x["repo"] for x in repos if x["status"] == "measured"
        and (int(x["commits"]) < 200 or x["adoption"] >= "2026-08")}
out["sensitivity_dropped"] = sorted(drop)
sens = {}
for i, (metric, direction) in enumerate(DIRECTION.items()):
    vals = [fnum(x["change_pct"]) for x in ba if x["metric"] == metric and x["repo"] not in drop]
    sens[metric] = describe(vals, direction, seed=2000 + i)
out["sensitivity"] = sens

# ------------------------------------------------------------ segments
dated = [x for x in repos if x["status"] == "measured"]
commits_sorted = sorted(int(x["commits"]) for x in dated)
t1, t2 = commits_sorted[len(dated) // 3 - 1], commits_sorted[2 * len(dated) // 3 - 1]
ai_med = st.median(float(x["ai_share_pct"]) for x in dated)


def size_seg(x):
    c = int(x["commits"])
    return "small (≤%d commits)" % t1 if c <= t1 else ("medium" if c <= t2 else "large (>%d commits)" % t2)


SEGMENTS = {
    "repo size": size_seg,
    "AI share": lambda x: "AI share ≥ median (%.1f%%)" % ai_med if float(x["ai_share_pct"]) >= ai_med
    else "AI share < median",
    "adoption year": lambda x: "adopted 2025" if x["adoption"] < "2026" else "adopted 2026",
}
KEY_METRICS = ["cyclomatic delta (per 100 production lines added)", "production lines added per commit",
               "lines rewritten within 30 days", "lines rewritten within 90 days", "follow-ups (per change)",
               "reimplementations (per KLOC added)", "share of follow-ups that are repairs"]
seg_rows = []
for sname, fn in SEGMENTS.items():
    for metric in KEY_METRICS:
        groups = {}
        for x in ba:
            if x["metric"] == metric and fnum(x["change_pct"]) is not None:
                groups.setdefault(fn(R[x["repo"]]), []).append(fnum(x["change_pct"]))
        for g, vals in sorted(groups.items()):
            d = describe(vals, DIRECTION[metric], seed=3000)
            seg_rows.append(dict(segment=sname, group=g, metric=metric, n=d["n"], rose=d["rose"], fell=d["fell"],
                                 median=d["median"], q1=d["q1"], q3=d["q3"], ci_low=d["ci_low"], ci_high=d["ci_high"]))
with open(os.path.join(DATA, "results_segments.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(seg_rows[0].keys()))
    w.writeheader()
    w.writerows(seg_rows)
out["segment_thresholds"] = dict(size_t1=t1, size_t2=t2, ai_share_median=ai_med)
out["segments"] = seg_rows

# Dose-response: does a bigger attributed share go with a bigger change?
dose = {}
for j, metric in enumerate(KEY_METRICS):
    pairs = [(float(R[x["repo"]]["ai_share_pct"]), fnum(x["change_pct"])) for x in ba
             if x["metric"] == metric and fnum(x["change_pct"]) is not None]
    rho, p = spearman_perm([a for a, _ in pairs], [b for _, b in pairs], seed=4000 + j)
    dose[metric] = dict(n=len(pairs), rho=round(rho, 3), p=round(p, 4))
out["dose_response_ai_share_vs_change"] = dose

# ------------------------------------------------------------ trends
status_of = {x["repo"]: x["status"] for x in repos}
trend_rows = []
for metric in DIRECTION:
    for arm in ("dated", "undated", "all"):
        rows = [x for x in tr if x["metric"] == metric
                and (arm == "all" or (status_of[x["repo"]] == "measured") == (arm == "dated"))]
        fitted = [x for x in rows if x["status"] != "unfitted"]
        est = [x for x in rows if x["status"] == "shown"]
        trend_rows.append(dict(metric=metric, arm=arm, series=len(rows), fitted=len(fitted),
                               established=len(est),
                               rose=sum(fnum(x["slope_per_month"]) > 0 for x in est),
                               fell=sum(fnum(x["slope_per_month"]) < 0 for x in est),
                               flat=sum(x["status"] == "flat" for x in rows),
                               not_established=sum(x["status"] in ("unestablished", "withheld") for x in rows),
                               unfitted=len(rows) - len(fitted),
                               fitted_slopes_positive=sum(fnum(x["slope_per_month"]) > 0 for x in fitted),
                               fitted_slopes_negative=sum(fnum(x["slope_per_month"]) < 0 for x in fitted)))
with open(os.path.join(DATA, "results_trends.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trend_rows[0].keys()))
    w.writeheader()
    w.writerows(trend_rows)
out["trends"] = trend_rows

# Trend dose-response across all fitted repos: AI share vs cyclomatic slope
cyc = [x for x in tr if x["metric"] == "cyclomatic delta (per 100 production lines added)" and x["status"] != "unfitted"]
rho, p = spearman_perm([float(R[x["repo"]]["ai_share_pct"]) for x in cyc],
                       [fnum(x["slope_per_month"]) for x in cyc], seed=5000)
out["trend_ai_share_vs_cyclomatic_slope"] = dict(n=len(cyc), rho=round(rho, 3), p=round(p, 4))

# ------------------------------------------------------------ sweep
sw = {}
for x in sweep_m:
    sw.setdefault(x["metric"], {}).setdefault(x["month"], {})[x["direction"]] = int(x["count"])
sweep_rows = []
for metric, months in sw.items():
    for month, d in sorted(months.items()):
        tot = d["wrong"] + d["right"]
        sweep_rows.append(dict(metric=metric, month=month, wrong=d["wrong"], right=d["right"],
                               share_wrong=round(d["wrong"] / tot, 3) if tot else None))
with open(os.path.join(DATA, "results_sweep.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sweep_rows[0].keys()))
    w.writeheader()
    w.writerows(sweep_rows)
out["sweep"] = {}
for metric, months in sw.items():
    rows = [x for x in sweep_rows if x["metric"] == metric]
    out["sweep"][metric] = dict(
        months=len(rows),
        months_wrong_gt_right=sum(x["wrong"] > x["right"] for x in rows),
        months_right_gt_wrong=sum(x["right"] > x["wrong"] for x in rows),
        max_wrong=max(x["wrong"] for x in rows), max_right=max(x["right"] for x in rows),
        right_from_2025_06=[x["right"] for x in rows if x["month"] >= "2025-06"],
    )

# ------------------------------------------------------------ dataset facts
out["dataset"] = dict(
    repos=len(repos), commits=sum(int(x["commits"] or 0) for x in repos),
    authors=sum(int(x["authors"] or 0) for x in repos),
    authors_with_ai=sum(int(x["authors_with_ai"] or 0) for x in repos),
    dated=len(dated), dated_commits=sum(int(x["commits"]) for x in dated),
    undated=sum(x["status"] == "undated" for x in repos),
    declined=sum(x["status"] == "declined" for x in repos),
    ai_share_dated_median=ai_med,
    ai_share_dated_min=min(float(x["ai_share_pct"]) for x in dated),
    ai_share_dated_max=max(float(x["ai_share_pct"]) for x in dated),
    ai_share_undated_max=max(float(x["ai_share_pct"]) for x in repos if x["status"] == "undated"),
    commit_weighted_ai_share_all=round(sum(float(x["ai_share_pct"] or 0) * int(x["commits"] or 0) for x in repos)
                                       / sum(int(x["commits"] or 0) for x in repos), 2),
    adoption_months={m: sum(x["adoption"] == m for x in dated) for m in sorted({x["adoption"] for x in dated})},
    adoption_rule={k: sum(x["rule"] == k for x in dated) for k in ("step", "threshold")},
    judge_usd=round(sum(float(x["judge_usd"] or 0) for x in repos), 4),
    ba_status={s: sum(x["status"] == s for x in ba) for s in ("asserted", "withheld", "excluded")},
    ba_reasons={},
)
for x in ba:
    if x["status"] != "asserted":
        k = x["status"] + ": " + x["reason"]
        out["dataset"]["ba_reasons"][k] = out["dataset"]["ba_reasons"].get(k, 0) + 1

with open(os.path.join(DATA, "results.json"), "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

# ------------------------------------------------------------ console digest
print(json.dumps(out["dataset"], indent=1, ensure_ascii=False))
print("\nPER METRIC (all rows | asserted)")
for metric in DIRECTION:
    a = out["metric_summary"][metric]["all rows with a ratio"]
    s = out["metric_summary"][metric]["asserted rows only"]
    print(f"{metric[:48]:48} all n={a['n']:2} up={a['rose']:2} dn={a['fell']:2} med={a['median']} "
          f"IQR=[{a['q1']},{a['q3']}] CI=[{a['ci_low']},{a['ci_high']}] p={a['sign_p'] and round(a['sign_p'],4)} | "
          f"asserted n={s['n']} up={s['rose']} dn={s['fell']} med={s['median']}")
print("\nSENSITIVITY (dropped %s)" % out["sensitivity_dropped"])
for metric, d in sens.items():
    print(f"{metric[:48]:48} n={d['n']} up={d['rose']} dn={d['fell']} med={d['median']} p={d['sign_p'] and round(d['sign_p'],4)}")
print("\nDOSE", json.dumps(dose, indent=0))
print("TREND DOSE", out["trend_ai_share_vs_cyclomatic_slope"])
print("\nTRENDS")
for t in trend_rows:
    print(t)
print("\nSWEEP", json.dumps(out["sweep"], indent=0))
