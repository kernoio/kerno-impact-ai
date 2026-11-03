"""12- and 24-month linear projections under three scenarios.

Method (one paragraph, as stated in the report): for each metric we take every
repository whose monthly series the audit could fit (status other than
'unfitted'), read its fitted end level and its slope per month, and project
level + slope x months. The cross-repository median is the central value; the
range is a bootstrap 95% interval of that median over repositories. Scenarios
differ only in which slopes are used:
  current      all fitted repositories
  accelerated  repositories at or above the median attributed AI share of the
               fitted set (an observed, higher-adoption group, not a model)
  controls     the slowest-moving quarter of repositories (slopes at or below
               the 25th percentile in the costly direction): an illustrative
               bound for "teams that already hold the line", with no in-sample
               evidence that any control produces it
Levels are floored at zero for rate metrics. Rework is deliberately not
projected: its median level is ~0.1 per 100 lines and falling, so a straight
line reaches the zero floor inside the horizon in several scenarios, which is
an artefact of the method rather than a forecast. Linear extrapolation of 8-30
monthly points is a weak method and is labelled as such in the report.

Output: data/forecast.csv, data/forecast.json
"""
import csv
import json
import os
import random
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
B = 10000

repos = {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, "repos.csv")))}
tr = list(csv.DictReader(open(os.path.join(DATA, "trends.csv"))))

METRICS = {
    "cyclomatic delta (per 100 production lines added)": "up",
    "production lines added per commit": None,
}
HORIZONS = (6, 12, 24)


def boot_ci(xs, seed):
    rnd = random.Random(seed)
    meds = sorted(st.median(rnd.choices(xs, k=len(xs))) for _ in range(B))
    return meds[int(0.025 * B)], meds[int(0.975 * B) - 1]


rows, out = [], {}
for mi, (metric, costly) in enumerate(METRICS.items()):
    fitted = [x for x in tr if x["metric"] == metric and x["status"] != "unfitted"]
    for x in fitted:
        x["_ai"] = float(repos[x["repo"]]["ai_share_pct"])
        x["_slope"] = float(x["slope_per_month"])
        x["_end"] = float(x["end"])
    ai_med = st.median(x["_ai"] for x in fitted)
    signed = sorted(x["_slope"] if costly != "down" else -x["_slope"] for x in fitted)
    q1 = st.quantiles(signed, n=4, method="inclusive")[0]
    scen = {
        "current": fitted,
        "accelerated": [x for x in fitted if x["_ai"] >= ai_med],
        "controls": [x for x in fitted if x["_slope"] <= q1],
    }
    base_level = st.median(x["_end"] for x in fitted)
    out[metric] = dict(n_fitted=len(fitted), ai_share_split=ai_med, base_level=round(base_level, 3),
                       slope_q1=round(q1, 4), scenarios={})
    for si, (name, group) in enumerate(scen.items()):
        slopes = [x["_slope"] for x in group]
        ends = [x["_end"] for x in group]
        med_s = st.median(slopes)
        lo_s, hi_s = boot_ci(slopes, seed=6000 + 10 * mi + si)
        d = dict(n=len(group), median_slope=round(med_s, 4), slope_ci=[round(lo_s, 4), round(hi_s, 4)],
                 group_level=round(st.median(ends), 3))
        for h in HORIZONS:
            # Projection starts from the all-repo median level so scenarios are comparable
            def proj(s):
                v = base_level + s * h
                return max(0.0, v) if costly else v
            d[f"m{h}"] = round(proj(med_s), 2)
            d[f"m{h}_range"] = [round(proj(lo_s), 2), round(proj(hi_s), 2)]
            d[f"m{h}_pct_vs_base"] = round(100 * (proj(med_s) / base_level - 1), 1) if base_level else None
            rows.append(dict(metric=metric, scenario=name, n=len(group), base_level=round(base_level, 3),
                             median_slope=round(med_s, 4), slope_ci_low=round(lo_s, 4), slope_ci_high=round(hi_s, 4),
                             horizon_months=h, projected=round(proj(med_s), 2),
                             range_low=round(proj(lo_s), 2), range_high=round(proj(hi_s), 2)))
        out[metric]["scenarios"][name] = d

with open(os.path.join(DATA, "forecast.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
json.dump(out, open(os.path.join(DATA, "forecast.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
