"""Build the number registry the report is typeset from, and the findings log.

Every number printed in the report is a {{key}} in report/report_template.html.
This script resolves each key from the analysis outputs and records where it
came from; 07_build.py refuses to build if the template uses a key that is not
here. The same registry is written out as ../findings.md.

Output: data/numbers.json, ../findings.md
"""
import csv
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats_util import describe  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
res = json.load(open(os.path.join(DATA, "results.json")))
fc = json.load(open(os.path.join(DATA, "forecast.json")))
seg = list(csv.DictReader(open(os.path.join(DATA, "results_segments.csv"))))
tr = list(csv.DictReader(open(os.path.join(DATA, "trends.csv"))))
repos = {r["repo"]: r for r in csv.DictReader(open(os.path.join(DATA, "repos.csv")))}

REG = {}
SECTIONS = []


def section(name):
    SECTIONS.append((name, []))


def N(key, value, source, caveat=""):
    if key in REG:
        raise SystemExit(f"duplicate key {key}")
    REG[key] = dict(value=value, source=source, caveat=caveat)
    SECTIONS[-1][1].append(key)


MINUS = "−"


def sgn(v, d=0):
    """+12% / −12% with a true minus; d decimals."""
    s = f"{abs(v):.{d}f}"
    return ("+" if v > 0 else MINUS if v < 0 else "") + s + "%"


def p_fmt(p):
    if p is None:
        return "n/a"
    if p < 0.001:
        return "p < 0.001"
    return f"p = {p:.3f}" if p < 0.01 else f"p = {p:.2f}"


def ci(lo, hi):
    return f"{sgn(lo)} to {sgn(hi)}"


def comma(n):
    return f"{int(n):,}"


D = res["dataset"]
MS = res["metric_summary"]
A = "all rows with a ratio"
S = "asserted rows only"
SRC_DS = "03_analysis.py → data/results.json:dataset"
SRC_MS = "03_analysis.py → data/results_metric_summary.csv"

# ---------------------------------------------------------------- dataset
section("Dataset and attribution")
N("repos", str(D["repos"]), SRC_DS, "Matches the PDF header (46 repositories); checked in data/extract_checks.txt")
N("commits", comma(D["commits"]), SRC_DS, "Matches the PDF (201,576); first-parent history of each default branch")
N("authors", comma(D["authors"]), SRC_DS, "Matches the PDF (6,847). Sum over repos; a person active in two repos counts twice")
N("authors_ai", comma(D["authors_with_ai"]), SRC_DS, "Authors with ≥1 attributed commit; summed over repos (may double-count people)")
N("dated", str(D["dated"]), SRC_DS)
N("dated_commits", comma(D["dated_commits"]), SRC_DS)
N("undated", str(D["undated"]), SRC_DS)
N("declined", str(D["declined"]), SRC_DS, "polonel/trudesk; the PDF gives no reason")
N("ai_med", f"{D['ai_share_dated_median']:.1f}%", SRC_DS, "Median attributed share over 30 dated repos. A floor, not a measurement")
N("ai_min", f"{D['ai_share_dated_min']:.1f}%", SRC_DS)
N("ai_max", f"{D['ai_share_dated_max']:.1f}%", SRC_DS)
N("ai_undated_max", f"{D['ai_share_undated_max']:.1f}%", SRC_DS)
N("ai_weighted", f"{D['commit_weighted_ai_share_all']:.1f}%", SRC_DS, "Commit-weighted over all 45 measured repos")
N("adopt_feb26", str(D["adoption_months"]["2026-02"]), SRC_DS, "Detected adoption months cluster")
N("adopt_2025", str(sum(v for k, v in D["adoption_months"].items() if k < "2026")), SRC_DS)
N("adopt_2026", str(sum(v for k, v in D["adoption_months"].items() if k >= "2026")), SRC_DS)
N("rule_step", str(D["adoption_rule"]["step"]), SRC_DS)
N("rule_thresh", str(D["adoption_rule"]["threshold"]), SRC_DS)
N("judge_usd", f"${D['judge_usd']:.2f}", SRC_DS, "LLM judge spend for the whole run, as reported per repo in the PDF")
N("ba_rows", str(sum(D["ba_status"].values())), SRC_DS)
N("ba_asserted", str(D["ba_status"]["asserted"]), SRC_DS)
N("ba_withheld", str(D["ba_status"]["withheld"]), SRC_DS)
N("ba_excluded", str(D["ba_status"]["excluded"]), SRC_DS)
R = D["ba_reasons"]
N("ex_pretrend", str(R["excluded: confounded by a pre-existing trend"]), SRC_DS)
N("ex_arm20", str(R["excluded: an arm under 20"]), SRC_DS)
N("ex_eff5", str(R["excluded: effect under 5%"]), SRC_DS)
N("ex_p05", str(R["excluded: p above 0.05"]), SRC_DS)
N("wh_ci0", str(R["withheld: CI includes 0"]), SRC_DS)
N("trend_series", str(len(tr)), "01_extract.py → data/trends.csv", "Matches '315 of 315 fitted series shown'")
N("trend_established", str(sum(x["status"] == "shown" for x in tr)), "01_extract.py → data/trends.csv",
  "Matches the PDF's 88 established trends")

N("c_sentry", comma(repos["sentry"]["commits"]), "01_extract.py → data/repos.csv")
N("c_djangocms", comma(repos["django-cms"]["commits"]), "01_extract.py → data/repos.csv")

# ---------------------------------------------------------------- per metric
KEYS = {
    "cyc": "cyclomatic delta (per 100 production lines added)",
    "cycc": "cyclomatic delta per commit",
    "exc": "excess complexity per KLOC",
    "lpc": "production lines added per commit",
    "rw30": "lines rewritten within 30 days",
    "rw90": "lines rewritten within 90 days",
    "rwe": "rework edits (per 100 lines added)",
    "fu": "follow-ups (per change)",
    "rep": "share of follow-ups that are repairs",
    "reimp": "reimplementations (per KLOC added)",
    "dff": "days to first follow-up",
}
section("Per-metric before/after, across repositories")
for k, m in KEYS.items():
    a, s = MS[m][A], MS[m][S]
    cav = ("Per-repo % change from the audit; repo is the unit. Median, IQR, bootstrap 95% CI of the median "
           "(10,000 resamples over repos), exact two-sided sign test on rose vs fell.")
    N(f"{k}_n", str(a["n"]), SRC_MS + f" [{m} | all rows]", cav)
    N(f"{k}_rose", str(a["rose"]), SRC_MS + f" [{m} | all rows]")
    N(f"{k}_fell", str(a["fell"]), SRC_MS + f" [{m} | all rows]")
    N(f"{k}_med", sgn(a["median"], 0 if a["median"] == int(a["median"]) else 1),
      SRC_MS + f" [{m} | all rows]")
    N(f"{k}_iqr", f"{sgn(a['q1'])} to {sgn(a['q3'])}", SRC_MS + f" [{m} | all rows]")
    N(f"{k}_ci", ci(a["ci_low"], a["ci_high"]), SRC_MS + f" [{m} | all rows]")
    N(f"{k}_mean", sgn(a["mean"]), SRC_MS + f" [{m} | all rows]", "Mean shown only beside the median; skewed by outliers")
    N(f"{k}_p", p_fmt(a["sign_p"]), SRC_MS + f" [{m} | all rows]")
    N(f"{k}_an", str(s["n"]), SRC_MS + f" [{m} | asserted]", "Rows the audit asserted (passed every gate)")
    N(f"{k}_amed", sgn(s["median"], 0 if s["median"] == int(s["median"]) else 1) if s["median"] is not None else "—", SRC_MS + f" [{m} | asserted]",
      "Reproduces the PDF headline table (p.6–7)")
    N(f"{k}_arose", str(s["rose"]), SRC_MS + f" [{m} | asserted]")
    N(f"{k}_afell", str(s["fell"]), SRC_MS + f" [{m} | asserted]")

# ---------------------------------------------------------------- sensitivity
section("Sensitivity: dropping thin repositories")
SS = res["sensitivity"]
N("sens_dropped", ", ".join(res["sensitivity_dropped"]), "03_analysis.py → results.json:sensitivity_dropped",
  "Repos with <200 commits or adoption in 2026-08 (after arm of one to two months)")
for k in ("cyc", "rw90", "rw30", "reimp", "rep", "fu", "lpc"):
    d = SS[KEYS[k]]
    N(f"sens_{k}", f"{d['rose']} of {d['n']} rose, median {sgn(d['median'])}, {p_fmt(d['sign_p'])}",
      "03_analysis.py → results.json:sensitivity")

# ---------------------------------------------------------------- segments
section("Segments")
T = res["segment_thresholds"]
N("size_t1", comma(T["size_t1"]), "03_analysis.py → results.json:segment_thresholds", "Commit-count terciles of the 30 dated repos")
N("size_t2", comma(T["size_t2"]), "03_analysis.py → results.json:segment_thresholds")


def segv(segment, group_prefix, metric):
    for x in seg:
        if x["segment"] == segment and x["group"].startswith(group_prefix) and x["metric"] == metric:
            return x
    raise KeyError((segment, group_prefix, metric))


for gk, (sname, prefix) in {"small": ("repo size", "small"), "medium": ("repo size", "medium"),
                            "large": ("repo size", "large"), "aihi": ("AI share", "AI share ≥"),
                            "ailo": ("AI share", "AI share <"), "y25": ("adoption year", "adopted 2025"),
                            "y26": ("adoption year", "adopted 2026")}.items():
    for k in ("cyc", "lpc", "rw90", "fu", "reimp"):
        x = segv(sname, prefix, KEYS[k])
        N(f"seg_{gk}_{k}", f"{sgn(float(x['median']))} ({sgn(float(x['ci_low']))} to {sgn(float(x['ci_high']))}; "
          f"{x['rose']} of {x['n']} rose)", "03_analysis.py → data/results_segments.csv",
          "Median with bootstrap 95% CI; n = 9–15 per group, so intervals are wide")

section("Dose-response: attributed AI share vs change")
for k in ("cyc", "lpc", "rw90", "fu", "reimp"):
    d = res["dose_response_ai_share_vs_change"][KEYS[k]]
    N(f"dose_{k}", f"ρ = {d['rho']:.2f}, {p_fmt(d['p'])}".replace("p = ", "permutation p = "),
      "03_analysis.py → results.json:dose_response_ai_share_vs_change",
      "Spearman across dated repos, 10,000-permutation p. AI share is a floor, so this is attenuated")
N("dose_cyc_rho", f"= {res['dose_response_ai_share_vs_change'][KEYS['cyc']]['rho']:.2f}", "03_analysis.py → results.json:dose_response_ai_share_vs_change",
  "Spearman rho, AI share vs change in complexity density, dated projects")
d = res["trend_ai_share_vs_cyclomatic_slope"]
N("dose_trend", f"ρ = {d['rho']:.2f}, permutation p = {d['p']:.2f}, n = {d['n']}",
  "03_analysis.py → results.json:trend_ai_share_vs_cyclomatic_slope")

# ---------------------------------------------------------------- trends
section("Trends (no adoption date needed)")


def trow(metric, arm):
    return next(x for x in res["trends"] if x["metric"] == metric and x["arm"] == arm)


for k in ("cyc", "lpc", "rwe", "fu", "reimp"):
    for arm in ("all", "dated", "undated"):
        t = trow(KEYS[k], arm)
        p = f"tr_{k}_{arm}"
        N(p + "_fit", str(t["fitted"]), "03_analysis.py → data/results_trends.csv")
        N(p + "_est", str(t["established"]), "03_analysis.py → data/results_trends.csv",
          "Established = audit gates: permutation p ≤ 0.05, ≥5% move, bootstrap keeps sign")
        N(p + "_rose", str(t["rose"]), "03_analysis.py → data/results_trends.csv")
        N(p + "_fell", str(t["fell"]), "03_analysis.py → data/results_trends.csv")
        N(p + "_pos", str(t["fitted_slopes_positive"]), "03_analysis.py → data/results_trends.csv",
          "Sign of every fitted slope, established or not")
_tc = trow(KEYS["cyc"], "all")
N("tr_cyc_all_series", str(_tc["series"]), "03_analysis.py → data/results_trends.csv", "codebases with a complexity-density monthly series")
N("tr_cyc_all_noclear", str(_tc["flat"] + _tc["not_established"]), "03_analysis.py → data/results_trends.csv", "fitted but no clear trend (flat or not established)")
N("tr_cyc_all_unfit", str(_tc["unfitted"]), "03_analysis.py → data/results_trends.csv", "too little monthly data to fit")
import statistics as st  # noqa: E402
for arm, lab in (("measured", "dated"), ("undated", "undated")):
    xs = [float(x["slope_per_month"]) for x in tr if x["metric"] == KEYS["cyc"] and x["status"] != "unfitted"
          and repos[x["repo"]]["status"] == arm]
    N(f"tr_cyc_{lab}_medslope", f"{st.median(xs):+.2f}".replace("-", MINUS), "trends.csv (median of fitted slopes; also fig10)",
      "Units: cyclomatic delta per 100 production lines, per month")

# ---------------------------------------------------------------- sweep
section("Placebo sweep (forced adoption month)")
SW = res["sweep"]
N("sw_months", str(SW["Cyclomatic delta"]["months"]), "02_sweep_bars.py → data/sweep_monthly.csv",
  "Counts recovered from the PDF's vector bars; alignment unique, rounding residual ≤ 0.03 repos (data/sweep_monthly_checks.txt)")
import re as _re  # noqa: E402
_res = [float(x) for x in _re.findall(r"residual ([0-9.]+)", open(os.path.join(DATA, "sweep_monthly_checks.txt")).read())]
N("sw_resid", f"{max(_res):.2f}", "02_sweep_bars.py → data/sweep_monthly_checks.txt", "Largest gap between a bar's height in repositories and the nearest whole number")
N("sw_cyc_wgt", str(SW["Cyclomatic delta"]["months_wrong_gt_right"]), "03_analysis.py → results.json:sweep")
N("sw_cyc_maxright", str(SW["Cyclomatic delta"]["max_right"]), "03_analysis.py → results.json:sweep")
N("sw_cyc_maxwrong", str(SW["Cyclomatic delta"]["max_wrong"]), "03_analysis.py → results.json:sweep")
N("sw_rwe_rgt", str(SW["Rework edits"]["months_right_gt_wrong"]), "03_analysis.py → results.json:sweep")
N("sw_fu_wgt", str(SW["Follow-ups"]["months_wrong_gt_right"]), "03_analysis.py → results.json:sweep")
N("sw_reimp_rgt", str(SW["Reimplementations"]["months_right_gt_wrong"]), "03_analysis.py → results.json:sweep")
N("sw_rep_rgt", str(SW["Repair share"]["months_right_gt_wrong"]), "03_analysis.py → results.json:sweep")
N("sw_cyc_feb", "35", "01_extract.py check vs PDF sweep card (35 wrong / 0 right at 2026-02)")
N("sw_cyc_feb_right", "0", "01_extract.py check vs PDF sweep card")
N("sw_cyc_feb_n", "40", "Adoption date sweep.pdf p.1: '40 of 45 repositories produce at least one verdict at 2026-02'")

# ---------------------------------------------------------------- forecast
section("Forecast")
F = fc[KEYS["cyc"]]
N("fc_base", f"{F['base_level']:.1f}", "04_forecast.py → data/forecast.json", "Median fitted end level, 39 fitted repos")
N("fc_n", str(F["n_fitted"]), "04_forecast.py → data/forecast.json")
N("fc_ai_split", f"{F['ai_share_split']:.1f}%", "04_forecast.py → data/forecast.json",
  "Median AI share of the 39 fitted repos (includes undated repos, hence lower than the dated-only 9.0%)")
for name in ("current", "accelerated", "controls"):
    s = F["scenarios"][name]
    N(f"fc_{name}_n", str(s["n"]), "04_forecast.py → data/forecast.json")
    N(f"fc_{name}_slope", f"{s['median_slope']:+.2f}".replace("-", MINUS), "04_forecast.py → data/forecast.json",
      "Median monthly slope, cyclomatic delta per 100 production lines")
    for h in (6, 12, 24):
        lo, hi = s[f"m{h}_range"]
        N(f"fc_{name}_{h}", f"{s[f'm{h}']:.1f} ({lo:.1f}–{hi:.1f})", "04_forecast.py → data/forecast.json",
          "Range = bootstrap 95% CI of the median slope, not the spread of repositories. Linear extrapolation")
        N(f"fc_{name}_{h}_pct", sgn(s[f"m{h}_pct_vs_base"]), "04_forecast.py → data/forecast.json")
        N(f"fc_{name}_{h}_pct_range", f"{sgn(100 * (lo / F['base_level'] - 1))} to {sgn(100 * (hi / F['base_level'] - 1))}",
          "04_forecast.py → data/forecast.json", "range as % change vs today, from the slope interval")
F2 = fc[KEYS["lpc"]]
for name in ("current", "accelerated"):
    s = F2["scenarios"][name]
    for h in (12, 24):
        lo, hi = s[f"m{h}_range"]
        N(f"fcl_{name}_{h}", f"{s[f'm{h}']:.0f} ({lo:.0f}–{hi:.0f})", "04_forecast.py → data/forecast.json",
          "Production lines per commit; linear extrapolation")
N("fcl_base", f"{F2['base_level']:.0f}", "04_forecast.py → data/forecast.json")

# ---------------------------------------------------------------- external
section("External sources (context only; see analysis/external_citations.md)")
EXT = [
    ("x_so_n", "30,000", "Stack Overflow 2026 Developer Survey press release (6 Oct 2026): 'over 30,000 responses'", "Self-selected Stack Overflow audience; unweighted"),
    ("x_so_nouse", "17.2%", "Stack Overflow 2026 press release: 'Only 17.2% say they do not use AI tools'", ""),
    ("x_faros_weekly", "60%", "Faros 2026, p.6", "Developers using AI weekly, up from 40%"),
    ("x_so_use", "82.8%", "Stack Overflow 2026 press release: 100% minus the 17.2% who 'do not use AI tools'", "Derived"),
    ("x_so_assist", "66%", "Stack Overflow 2026 press release: 'Coding assistants or coding agents are used by 66% of respondents'", ""),
    ("x_so_lowrisk", "16.3%", "survey.stackoverflow.co/2026/ai/data/ai-trust: 'I trust it for low-risk work tasks only' 16.3%", "n = 14,304"),
    ("x_so_notrust", "12.3%", "survey.stackoverflow.co/2026/ai/data/ai-trust: 'I do not trust it for most work tasks' 12.3%", "n = 14,304"),
    ("x_so_attrib", "78.7%", "Stack Overflow 2026 press release: '78.7% say that source attribution is important or very important'", ""),
    ("x_so_daily", "73%", "survey.stackoverflow.co/2026/ai: 'use coding assistants and agents daily (73%)'", "n = 10,926 respondents to that question"),
    ("x_so_important", "6.6%", "survey.stackoverflow.co/2026/ai/data/ai-trust: 'I trust it for many tasks, including important work decisions' 6.6%", "n = 14,304"),
    ("x_so_verify", "48%", "survey.stackoverflow.co/2026/ai/data/ai-trust: 'I trust it when I can easily verify the output' 48.0%", "n = 14,304"),
    ("x_cisq_cpsq", "$2.41 trillion", "CISQ, The Cost of Poor Software Quality in the US: A 2022 Report (H. Krasner), p.3", "US estimate for 2022; pre-dates AI coding tools"),
    ("x_cisq_td", "$1.52 trillion", "CISQ 2022 report, p.3–4: 'accumulated software Technical Debt (TD) has grown to ~$1.52 trillion'", "Approximate; pre-AI"),
    ("x_cisq_time", "33%", "CISQ 2022 report, p.4: '13.5 out of 41.1, or 33% of their time'", "Weekly developer hours spent addressing technical debt; cited survey, pre-AI"),
    ("x_gc_share", "24.1%", "GitClear, The Maintainability Gap (June 2026), p.7", "Estimated, heuristic attribution"),
    ("x_gc_dup", "+81%", "GitClear (June 2026), p.3", "Code block duplication, 2023 to 2026 YTD"),
    ("x_gc_refactor", "70%", "GitClear (June 2026), p.3 and p.14", "Moved (refactored) lines, baseline 2023 per p.14"),
    ("x_gc_clone", "57%", "GitClear (June 2026), p.15, citing Mo, Zhang et al. 2023", "Secondary citation"),
    ("x_faros_pr", "+51.3%", "Faros, AI Engineering Report 2026, p.13–14", "Low vs high AI-adoption quarters within teams"),
    ("x_faros_inc", "+242.7%", "Faros 2026, p.20–21", "Incidents per PR; not normalised for PR size (Faros p.21)"),
    ("x_faros_noreview", "+31.3%", "Faros 2026, p.16", "PRs merged with no review"),
    ("x_faros_agentpr", "under 1%", "Faros 2026, p.6", "PRs opened by agents"),
    ("x_faros_accept", "60%", "Faros 2026, p.6", "Acceptance rate of AI-generated code"),
    ("x_scb_erosion", "77%", "SlopCodeBench (arXiv:2603.24755v2), p.1", "Share of agent trajectories where structural erosion rose"),
    ("x_scb_cc10", "3.6 to 23.7", "SlopCodeBench, p.7", "Functions with CC ≥ 10 across a trajectory"),
    ("x_scb_human", "59%", "SlopCodeBench, p.8", "321 human repos more eroded after 2024 than before; authors call the shift small"),
    ("x_rel_fail", "19 versus 5", "Shafique, Miller, Heymann (2026), p.19", "Fuzzing failures, human originals vs AI rewrites"),
    ("x_rel_tests", "1,217 of 1,221", "Shafique, Miller, Heymann (2026), p.13", "Tests passed while 11 options were unimplemented"),
]
for k, v, src, cav in EXT:
    N(k, v, src, cav)


# ---------------------------------------------------------------- raw benchmark data (zip)
section("Raw benchmark data: verification and data quality (10_raw_verify.py, 11_raw_commits.py)")
RAWR = json.load(open(os.path.join(DATA, "raw_results.json")))
q = list(csv.DictReader(open(os.path.join(DATA, "raw_quality.csv"))))
SRC_Q = "11_raw_commits.py → data/raw_quality.csv"
N("rq_bots", comma(sum(int(r["bot_commits"]) for r in q)), SRC_Q, "timeline isBot flag")
N("rq_bot_share", f"{100 * sum(int(r['bot_commits']) for r in q) / sum(int(r['commits']) for r in q):.1f}%", SRC_Q)
N("rq_bot_max", f"{100 * max(float(r['bot_share']) for r in q):.0f}%", SRC_Q, "lightdash (semantic-release-bot)")
N("rq_cx_commits", comma(sum(int(r["complexity_commits"]) for r in q)), SRC_Q, "commits with production-code changes measured for complexity")
N("rq_cx_bots", str(sum(int(r["complexity_commits_from_bots"]) for r in q)), SRC_Q)
N("rq_paths", comma(sum(int(r["production_paths"]) for r in q)), SRC_Q)
N("rq_gen", comma(sum(int(r["production_paths_lock_vendor_generated"]) for r in q)), SRC_Q,
  "Lockfile, vendor/dist or code-generator paths counted as production; manual review: mostly grafana zz_generated and vendure generated-types")
N("rq_gen_share", f"{100 * sum(int(r['production_paths_lock_vendor_generated']) for r in q) / sum(int(r['production_paths']) for r in q):.1f}%", SRC_Q)
N("rq_outside", str(sum(int(r["dated_outside_window"]) for r in q)), SRC_Q, "author date outside the window (rebased or imported history)")
pc = RAWR["parser_coverage"]
N("rq_cov_low_n", str(sum(1 for _, v in pc if v < 0.9)), "12_raw_analysis.py → raw_results.json:parser_coverage", "projects where < 90% of source files were readable by the complexity parser")
N("rq_cov_min", f"{100 * pc[0][1]:.0f}%", "12_raw_analysis.py → raw_results.json:parser_coverage", pc[0][0])
N("rq_verify_rows", "330", "10_raw_verify.py → data/raw_verify.txt", "PDF-extracted before/after rows identical to raw metrics.csv")
N("rq_verify_trends", "315", "10_raw_verify.py → data/raw_verify.txt")
N("rq_ts", str(len(RAWR["languages"].get("typescript", [])) + len(RAWR["languages"].get("tsx", []))), "12_raw_analysis.py → raw_results.json:languages",
  "primary language by function count in the last snapshot; TSX counted as TypeScript")
N("rq_py", str(len(RAWR["languages"].get("python", []))), "12_raw_analysis.py → raw_results.json:languages")
N("rq_go", str(len(RAWR["languages"].get("go", []))), "12_raw_analysis.py → raw_results.json:languages")
N("rq_js", str(len(RAWR["languages"].get("javascript", []))), "12_raw_analysis.py → raw_results.json:languages")

def dsc(prefix, d, src, cav="", dec=0):
    N(prefix + "_n", str(d["n"]), src, cav)
    N(prefix + "_rose", str(d["rose"]), src)
    N(prefix + "_fell", str(d["fell"]), src)
    N(prefix + "_med", sgn(d["median"], dec), src)
    N(prefix + "_ci", ci(d["ci_low"], d["ci_high"]), src)
    N(prefix + "_p", p_fmt(d["sign_p"]), src)

section("Raw: throughput per active contributor-week, and commit kinds (11_raw_commits.py, 12_raw_analysis.py)")
SRC_T = "12_raw_analysis.py → raw_results.json:throughput (per-repo rows: data/raw_throughput_changes.csv)"
T = RAWR["throughput"]
for k, m in (("tp_team", "active_per_week"), ("tp_commits", "commits_per_cw"), ("tp_pr", "pr_commits_per_cw"),
             ("tp_lines", "prod_lines_per_cw"), ("tp_bug", "bugfix_share"), ("tp_test", "test_share"), ("tp_revert", "revert_share")):
    dsc(k, T[m], SRC_T, "Non-bot commits inside the audit window; contributor-week = distinct author email active in an ISO week")
N("tp_team_before", f"{T['active_per_week']['median_before']:.1f}", SRC_T, "median active contributors per week, before")
N("tp_team_after", f"{T['active_per_week']['median_after']:.1f}", SRC_T)
N("tp_lines_before", f"{T['prod_lines_per_cw']['median_before']:.0f}", SRC_T, "median production lines per contributor-week, before")
N("tp_lines_after", f"{T['prod_lines_per_cw']['median_after']:.0f}", SRC_T)
N("tp_bug_before", f"{100 * T['bugfix_share']['median_before']:.1f}%", SRC_T)
N("tp_bug_after", f"{100 * T['bugfix_share']['median_after']:.1f}%", SRC_T)
N("tp_test_before", f"{100 * T['test_share']['median_before']:.1f}%", SRC_T, "share of commits classified as test changes (changeKind = test)")
N("tp_test_after", f"{100 * T['test_share']['median_after']:.1f}%", SRC_T)
N("tp_revert_zero", str(T["revert_share"]["n_zero_before"]), SRC_T, "repos with no reverts before adoption (no ratio)")
RP = RAWR["reverts_pooled"]
N("rv_before", f"{100 * RP['before']['reverts'] / RP['before']['commits']:.2f}%", "12_raw_analysis.py → raw_results.json:reverts_pooled",
  f"{RP['before']['reverts']} of {RP['before']['commits']:,} commits")
N("rv_after", f"{100 * RP['after']['reverts'] / RP['after']['commits']:.2f}%", "12_raw_analysis.py → raw_results.json:reverts_pooled",
  f"{RP['after']['reverts']} of {RP['after']['commits']:,} commits")
N("hf_before", str(RP["before"]["hotfixes"]), "12_raw_analysis.py → raw_results.json:reverts_pooled", "subjects mentioning hotfix")
N("hf_after", str(RP["after"]["hotfixes"]), "12_raw_analysis.py → raw_results.json:reverts_pooled")
BP = RAWR["bugfix_precision"]
N("bf_n", str(BP["n"]), "12_raw_analysis.py → raw_results.json:bugfix_precision", "hand-labelled by the analyst (an AI model) from subject lines; data/raw_kinds_labelled.csv")
N("bf_prec", f"{100 * BP['precision_strict']:.0f}%", "12_raw_analysis.py → raw_results.json:bugfix_precision")
N("bf_prec_len", f"{100 * BP['precision_lenient']:.0f}%", "12_raw_analysis.py → raw_results.json:bugfix_precision", "counting 'unclear' as correct")
N("bf_unclear", str(BP["unclear"]), "12_raw_analysis.py → raw_results.json:bugfix_precision")
N("bf_no", str(BP["no"]), "12_raw_analysis.py → raw_results.json:bugfix_precision")

section("Raw: whole-codebase complexity snapshots (12_raw_analysis.py)")
SN = RAWR["snapshots"]
SRC_S = "12_raw_analysis.py → raw_results.json:snapshots (per-repo: data/raw_snapshots.csv)"
dsc("sn_all", SN["all"]["complex_share"], SRC_S, "Share of functions with cyclomatic complexity > 10, first vs last snapshot in the window")
dsc("sn_dated", SN["dated"]["complex_share"], SRC_S)
dsc("sn_undated", SN["undated"]["complex_share"], SRC_S)
dsc("sn_exc", SN["all"]["excess_per_kloc"], SRC_S, "Excess complexity per KLOC, whole tree, first vs last snapshot")
dsc("sn_lines", SN["all"]["lines"], SRC_S, "Production lines in the tree, first vs last snapshot")
N("sn_level_first", f"{100 * SN['all']['complex_share_first_median']:.1f}%", SRC_S, "median share of functions above CC 10, first snapshot")
N("sn_level_last", f"{100 * SN['all']['complex_share_last_median']:.1f}%", SRC_S)
PA = SN["pace"]
N("sn_pace_n", str(PA["n"]), SRC_S, "dated repos with >= 3 months of snapshots on each side of adoption")
N("sn_pace_faster", str(PA["faster_after"]), SRC_S)
N("sn_pace_before", f"{PA['median_pp_before']:.3f}", SRC_S, "median percentage-point change in the complex-function share per month, before adoption")
N("sn_pace_after", f"{PA['median_pp_after']:.3f}", SRC_S)
N("sn_pace_p", p_fmt(PA["sign_p"]), SRC_S)
LS = RAWR["language_segments"]
for k in ("cyc_TypeScript", "cyc_Other"):
    d = LS[k]
    N(f"lang_{k.replace('TypeScript', 'ts').replace('Other', 'other')}", f"{sgn(d['median'])} ({d['rose']} of {d['n']} rose)", "12_raw_analysis.py → raw_results.json:language_segments")
N("lang_other_list", ", ".join(RAWR["language_other_dated"]), "12_raw_analysis.py → raw_results.json:language_other_dated")

section("Raw: AI-labelled vs unlabelled commits in the same period (12_raw_analysis.py, 13_raw_followups_size.py)")
W = RAWR["within"]
SRC_W = "12_raw_analysis.py → raw_results.json:within (audit withinPeriod rows: data/raw_within.csv)"
dsc("wi_cyc", W["complexity density"], SRC_W, "Projects with >= 20 AI-labelled commits; after period for dated repos, whole window for undated")
dsc("wi_rw", W["rework edits per 100 lines"], SRC_W)
dsc("wi_fu", W["follow-ups per change"], SRC_W)
N("wi_fu_sig_hi", str(W["follow-ups per change"]["significant_higher_ai"]), SRC_W, "projects where the audit's own test is p <= 0.05, AI-labelled higher")
N("wi_fu_sig_lo", str(W["follow-ups per change"]["significant_lower_ai"]), SRC_W)
WD = RAWR["within_dated"]
SRC_WD = "12_raw_analysis.py → raw_results.json:within_dated (codebases with an adoption date, after adoption)"
dsc("wd_fu", WD["follow-ups per change"], SRC_WD, "AI-attributed vs unattributed, same codebase and period")
dsc("wd_cyc", WD["complexity density"], SRC_WD)
FSD = RAWR["followups_size_dated"]
SRC_FD = "13_raw_followups_size.py → raw_results.json:followups_size_dated"
dsc("fd_size", FSD["median_lines"], SRC_FD, "median production lines per commit, AI-attributed vs unattributed")
dsc("fd_lines", FSD["fu_per_100_lines"], SRC_FD, "follow-ups per 100 lines, AI-attributed vs unattributed")
dsc("fd_change", FSD["fu_per_change"], SRC_FD)
FS = RAWR["followups_size"]
SRC_F = "13_raw_followups_size.py → raw_results.json:followups_size (data/raw_followups_size.csv)"
dsc("fs_change", FS["fu_per_change"], SRC_F, "recomputed from raw follow-up rows; excludes sweeps, reverts, hot files")
dsc("fs_lines", FS["fu_per_100_lines"], SRC_F, "follow-ups per 100 production lines added")
dsc("fs_size", FS["median_lines"], SRC_F, "median production lines added per commit, AI-labelled vs unlabelled")
d = RAWR["ai_share_vs_cyc_slope_established"]
N("rho_est", f"ρ = {d['rho']:.2f}, n = {d['n']}", "12_raw_analysis.py → raw_results.json", "matches benchmark README (+0.04)")
d = RAWR["ai_share_vs_cyc_slope_fitted"]
N("rho_fit", f"ρ = {d['rho']:.2f}, n = {d['n']}", "12_raw_analysis.py → raw_results.json")

section("Raw: complexity vs later bug fixes, size-matched (14_raw_complexity_fixes.py)")
CF = RAWR["complexity_fixes"]
SRC_CF = "14_raw_complexity_fixes.py → raw_results.json:complexity_fixes (per repo: data/raw_complexity_fixes.csv)"
N("cf_repos", str(CF["repos"]), SRC_CF, "repos with >= 20 bug-fix follow-up events")
N("cf_commits", comma(CF["commits"]), SRC_CF, "non-bot commits with >= 5 production lines")
N("cf_events", comma(CF["fix_events"]), SRC_CF)
dsc("cf_fix", CF["fix"], SRC_CF, "Mantel-Haenszel risk ratio within size deciles, high vs low complexity density; outcome = later edit by a bug-fix commit within 90 days")
dsc("cf_any", CF["any"], SRC_CF, "same design, outcome = any later follow-up edit")

# Same test on the report's trend group only (codebases with a fitted complexity trend)
_fit = {x["repo"] for x in csv.DictReader(open(os.path.join(DATA, "trends.csv"))) if x["metric"].startswith("cyclomatic delta (per 100") and x["status"] != "unfitted"}
_cf = [float(x["fix_gap_pct"]) for x in csv.DictReader(open(os.path.join(DATA, "raw_complexity_fixes.csv")))
       if x["repo"] in _fit and int(x["fix_events"]) >= 20 and x["fix_gap_pct"] not in ("", "None")]
dsc("cft_fix", describe(_cf, seed=7600), "06_numbers.py from data/raw_complexity_fixes.csv (trend group, >= 20 fix events)",
    "Mantel-Haenszel risk ratio within size deciles, restricted to codebases with a fitted complexity trend")

section("Raw: absolute volumes per engineer (15_raw_absolute.py)")
AB = RAWR["absolute"]
SRC_AB = "15_raw_absolute.py → raw_results.json:absolute (per repo: data/raw_absolute.csv)"
dsc("ab_bug", AB["bugfix_per_cw"], SRC_AB, "bug-fix share x commits per contributor-week, before vs after adoption")
dsc("ab_rw30", AB["rewritten30_per_cw"], SRC_AB, "estimate: audit rewrite share x production lines per contributor-week")
dsc("ab_rw90", AB["rewritten90_per_cw"], SRC_AB, "estimate: audit rewrite share x production lines per contributor-week")

section("Shares of all commits analysed (16_commit_shares.py)")
CS = json.load(open(os.path.join(DATA, "commit_shares.json")))
for k in ("dated", "undated", "trend_rise", "trend_fall", "trend_none", "trend_nodata", "cyc_rose", "cyc_fell", "lpc_rose",
          "rw90_fell", "tp_lines_rose", "tp_test_rose", "trend_fitted", "ab_rw30_rose", "ab_rw90_rose", "ab_bug_rose", "sn_rose"):
    v = CS[k]
    N(f"cs_{k}", f"{100 * v['share_of_all']:.0f}%" if v["share_of_all"] >= 0.01 or v["share_of_all"] == 0 else "under 1%",
      "16_commit_shares.py → data/commit_shares.json",
      f"{v['codebases']} codebases, {v['commits']:,} of {CS['total_commits']:,} commits")
N("n_dated_commits", f"{CS['dated']['commits']:,}", "16_commit_shares.py → data/commit_shares.json", "commits in the codebases with an AI adoption date")
N("n_trend_commits", f"{CS['trend_fitted']['commits']:,}", "16_commit_shares.py → data/commit_shares.json", "commits in the codebases with a fitted complexity trend")
N("n_trend_repos", str(CS['trend_fitted']['codebases']), "16_commit_shares.py → data/commit_shares.json")
N("cs_dated_exact", f"{100 * CS['dated']['share_of_all']:.1f}%", "16_commit_shares.py → data/commit_shares.json")
N("cs_undated_exact", f"{100 * CS['undated']['share_of_all']:.1f}%", "16_commit_shares.py → data/commit_shares.json")

section("Monthly growth rate of complexity density (17_monthly_rate.py)")
MR = json.load(open(os.path.join(DATA, "monthly_rate.json")))
SRC_MR = "17_monthly_rate.py → data/monthly_rate.json (per project: data/monthly_rate.csv)"
for k, key in (("mr_before", "before"), ("mr_after", "after"), ("mr_undated", "undated_whole_window"), ("mr_all", "whole_window")):
    d = MR[key]
    N(k + "_n", str(d["n"]), SRC_MR, MR["method"] if k == "mr_before" else "")
    N(k + "_med", sgn(d["median"], 1), SRC_MR, "steady monthly growth rate, exp(slope of log density) - 1; median across projects")
    N(k + "_ci", f"{sgn(d['ci'][0], 1)} to {sgn(d['ci'][1], 1)}", SRC_MR)
    N(k + "_rose", str(d["rose"]), SRC_MR)
    N(k + "_fell", str(d["fell"]), SRC_MR)
    N(k + "_p", p_fmt(d["p"]), SRC_MR)
d = MR["after_minus_before"]
N("mr_diff_med", f"{sgn(d['median'], 1)[:-1]} points", SRC_MR, "paired: after rate minus before rate, percentage points per month")
N("mr_diff_ci", f"{sgn(d['ci'][0], 1)[:-1]} to {sgn(d['ci'][1], 1)[:-1]} points", SRC_MR)
N("mr_diff_rose", str(d["rose"]), SRC_MR)
N("mr_diff_p", p_fmt(d["p"]), SRC_MR)
N("mr_months_before", f"{MR['paired_before_months_median']:g}", SRC_MR, "median usable months before adoption")
N("mr_months_after", f"{MR['paired_after_months_median']:g}", SRC_MR, "median usable months after adoption")
SV = MR["sensitivity"]
N("mr_sens_n", str(len(SV)), SRC_MR, "; ".join(f"≥{x['min_lines']} lines/month, ≥{x['min_months']} months: after {x['after']['median']:+.2f}% ({p_fmt(x['after']['p'])}), before {x['before']['median']:+.2f}% ({p_fmt(x['before']['p'])}), diff {p_fmt(x['diff']['p'])}" for x in SV))
N("mr_sens_after_range", f"{sgn(min(x['after']['median'] for x in SV), 1)} to {sgn(max(x['after']['median'] for x in SV), 1)}", SRC_MR, "after-adoption median across sensitivity variants")
N("mr_sens_after_allclear", "yes" if all(x["after"]["p"] <= 0.05 for x in SV) else "no", SRC_MR)
N("mr_sens_diff_anyclear", "yes" if any(x["diff"]["p"] <= 0.05 for x in SV) else "no", SRC_MR)
N("mr_after_annual", sgn(100 * ((1 + MR["after"]["median"] / 100) ** 12 - 1), 0), SRC_MR, "median monthly rate compounded over 12 months")

section("Maintainability grade from excess complexity per KLOC (18_maintainability.py)")
MT = json.load(open(os.path.join(DATA, "maintainability.json")))
SRC_MT = "18_maintainability.py → data/maintainability.json (per project: data/maintainability.csv)"
N("mt_n", str(MT["n"]), SRC_MT, "codebases with a fitted complexity trend and whole-tree snapshots")
N("mt_cuts", " / ".join(f"{c:.1f}" for c in MT["cuts"]), SRC_MT, "quartiles of first-snapshot excess per KLOC: A ≤ c1 < B ≤ c2 < C ≤ c3 < D")
for g in "ABCD":
    N(f"mt_{g.lower()}_first", str(MT["grade_counts_first"][g]), SRC_MT)
    N(f"mt_{g.lower()}_last", str(MT["grade_counts_last"][g]), SRC_MT)
N("mt_worse", str(len(MT["moved_worse"])), SRC_MT, "; ".join(MT["moved_worse"]))
N("mt_better", str(len(MT["moved_better"])), SRC_MT, "; ".join(MT["moved_better"]))
N("mt_same", str(MT["n"] - len(MT["moved_worse"]) - len(MT["moved_better"])), SRC_MT)
N("mt_two_worse", str(sum(1 for m in MT["moved_worse"] if ord(m[-1]) - ord(m[-3]) >= 2)), SRC_MT, "moved two or more grades")
for k, key in (("mt_exc", "excess_change"), ("mt_cs", "complex_share_change")):
    d = MT[key]
    N(k + "_med", sgn(d["median"]), SRC_MT, "first vs last whole-tree snapshot")
    N(k + "_ci", f"{sgn(d['ci'][0])} to {sgn(d['ci'][1])}", SRC_MT)
    N(k + "_rose", str(d["rose"]), SRC_MT)
    N(k + "_fell", str(d["fell"]), SRC_MT)
    N(k + "_p", p_fmt(d["p"]), SRC_MT)
N("mt_cs_first", f"{100 * MT['complex_share_first_median']:.1f}%", SRC_MT, "median share of functions above cyclomatic 10")
N("mt_cs_last", f"{100 * MT['complex_share_last_median']:.1f}%", SRC_MT)
N("mt_exc_first", f"{MT['excess_first_median']:.1f}", SRC_MT, "median excess complexity per 1,000 production lines")
N("mt_exc_last", f"{MT['excess_last_median']:.1f}", SRC_MT)

section("Lines committed, net lines, bug-fix and test rates, codebase size (19-22)")


def sm(prefix, d, src, cav="", dec=1, points=False):
    fmt = (lambda v: sgn(v, dec)[:-1] + " points") if points else (lambda v: sgn(v, dec))
    N(prefix + "_n", str(d["n"]), src, cav)
    N(prefix + "_med", fmt(d["median"]), src)
    N(prefix + "_ci", f"{fmt(d['ci'][0]).replace(' points', '')} to {fmt(d['ci'][1])}", src)
    N(prefix + "_rose", str(d["rose"]), src)
    N(prefix + "_fell", str(d["fell"]), src)
    N(prefix + "_p", p_fmt(d["p"]), src)


LR = json.load(open(os.path.join(DATA, "lines_rate.json")))
S19 = "19_lines_rate.py → data/lines_rate.json"
sm("lr_before", LR["lines"]["before"], S19, "monthly growth of production lines committed, before adoption")
sm("lr_after", LR["lines"]["after"], S19, "monthly growth of production lines committed, after adoption")
sm("lr_diff", LR["lines"]["after_minus_before"], S19, "after minus before, percentage points", points=True)
sm("lr_all", LR["lines"]["whole_window_trend_group"], S19, "whole window, trend group")
sm("lra_after", LR["per_author"]["after"], S19, "monthly growth of production lines per active author, after adoption")
sm("lra_before", LR["per_author"]["before"], S19)
N("lr_after_annual", sgn(100 * ((1 + LR["lines"]["after"]["median"] / 100) ** 12 - 1), 0), S19, "median monthly rate compounded over 12 months")
NL = json.load(open(os.path.join(DATA, "net_lines.json")))
S20 = "20_net_lines.py → data/net_lines.json"
sm("nl90", NL["surviving90"], S20, "production lines per contributor-week surviving 90 days, before vs after", 0)
sm("nl30", NL["surviving30"], S20, "", 0)
BR = json.load(open(os.path.join(DATA, "bugfix_rates.json")))
S21 = "21_bugfix_rates.py → data/bugfix_rates.json"
sm("bk_kloc", BR["per_kloc_change"], S21, "bug-fix commits per 1,000 production lines added; falls mechanically as commits get bigger", 0)
sm("bk_rate_before", BR["monthly_before"], S21, "monthly growth of bug-fix commits")
sm("bk_rate_after", BR["monthly_after"], S21)
sm("bk_rate_diff", BR["monthly_diff"], S21, points=True)
SX = json.load(open(os.path.join(DATA, "sprawl_extension_tests.json")))
S22 = "22_sprawl_extension_tests.py → data/sprawl_extension_tests.json"
sm("sz_growth", SX["size"]["growth"], S22, "production lines in the whole tree, first vs last snapshot, trend group", 0)
N("sz_months", f"{SX['size']['months_median']:g}", S22, "median months between first and last snapshot")
N("sz_first", f"{SX['size']['first_median'] / 1000:.0f}k", S22, "median production lines, first snapshot")
N("sz_last", f"{SX['size']['last_median'] / 1000:.0f}k", S22, "median production lines, last snapshot")
sm("sz_rate", SX["size"]["rate_all"], S22, "monthly growth of the whole tree")
sm("sz_rate_before", SX["size"]["rate_before"], S22)
sm("sz_rate_after", SX["size"]["rate_after"], S22)
sm("sz_rate_diff", SX["size"]["rate_diff"], S22, points=True)
J = SX["judged"]
N("ext_before", f"{100 * J['extension_before_median']:.0f}%", S22, "median share of confident follow-up verdicts that are extensions")
N("ext_after", f"{100 * J['extension_after_median']:.0f}%", S22)
N("rep_before_lvl", f"{100 * J['repair_before_median']:.0f}%", S22, "median share of confident follow-up verdicts that are repairs")
N("rep_after_lvl", f"{100 * J['repair_after_median']:.0f}%", S22)
sm("ext_chg", J["extension_change"], S22, "", 0)
sm("repx_chg", J["repair_change"], S22, "our recount from verdicts; audit's own figure is rep_med", 0)
N("aij_n", str(J["ai_n"]), S22, "codebases with >= 10 confident verdicts in each arm after adoption")
N("aij_rep_ai", f"{100 * J['repair_ai_median']:.0f}%", S22)
N("aij_rep_un", f"{100 * J['repair_un_median']:.0f}%", S22)
N("aij_ext_ai", f"{100 * J['extension_ai_median']:.0f}%", S22)
N("aij_ext_un", f"{100 * J['extension_un_median']:.0f}%", S22)
N("aij_rep_p", p_fmt(J["repair_ai_gap"]["p"]), S22)
N("aij_ext_p", p_fmt(J["extension_ai_gap"]["p"]), S22)
TS = SX["tests"]
sm("tc_cw", TS["per_cw_change"], S22, "test-change commits per active contributor-week, before vs after", 0)
sm("tc_kloc", TS["per_kloc_change"], S22, "test-change commits per 1,000 production lines added", 0)
sm("tc_rate_after", TS["test_rate_after"], S22, "monthly growth of test commits after adoption")
sm("tc_line_after", TS["line_rate_after_same"], S22, "monthly growth of production lines, same codebases")
sm("tc_gap", TS["test_minus_line_after"], S22, "test growth minus line growth, percentage points", points=True)
sm("tsr_undated", SX["test_share_rate_undated"], S22, "monthly growth of test-commit share, no adoption date, whole window")
sm("tsr_before", SX["test_share_rate_before"], S22)
sm("tsr_after", SX["test_share_rate_after"], S22)
sm("lr_undated", SX["lines_undated"], S22, "monthly growth of production lines committed, no adoption date, whole window")

section("Median before/after levels (from data/before_after.csv)")
_ba = list(csv.DictReader(open(os.path.join(DATA, "before_after.csv"))))


def _lvl(metric, side):
    import statistics as _st
    return _st.median(float(r[side]) for r in _ba if r["metric"] == metric and r[side] not in ("", "None"))


SRC_BA = "data/before_after.csv (audit before/after rows), median across codebases with an adoption date"
N("cyc_lvl_before", f"{_lvl('cyclomatic delta (per 100 production lines added)', 'before'):.1f}", SRC_BA, "decision points per 100 production lines added")
N("cyc_lvl_after", f"{_lvl('cyclomatic delta (per 100 production lines added)', 'after'):.1f}", SRC_BA)
N("rw90_lvl_before", f"{100 * _lvl('lines rewritten within 90 days', 'before'):.1f}%", SRC_BA, "share of added lines rewritten or deleted within 90 days")
N("rw90_lvl_after", f"{100 * _lvl('lines rewritten within 90 days', 'after'):.1f}%", SRC_BA)

section("Month-by-month complexity around adoption (23_monthly_series.py)")
MSJ = json.load(open(os.path.join(DATA, "monthly_series.json")))
MSR = {int(r["rel_month"]): r for r in csv.DictReader(open(os.path.join(DATA, "monthly_series.csv")))}
S23 = "23_monthly_series.py → data/monthly_series.csv"
N("ms_codebases", str(MSJ["codebases"]), S23, "codebases with an adoption date and >= 3 baseline months; index 100 = own mean of months -6..-1")
for k in (-12, -8, -1, 0, 1, 6, 7, 9):
    tag = f"m{abs(k)}" if k < 0 else f"p{k}"
    N(f"ms_{tag}", f"{float(MSR[k]['median']):.0f}", S23, f"median index at month {k:+d}")
    N(f"ms_{tag}_n", MSR[k]["n"], S23)
    N(f"ms_{tag}_pct", sgn(float(MSR[k]["median"]) - 100), S23, f"median % change vs own pre-adoption average, month {k:+d}")

section("Volumes behind the percentages (24_volumes.py)")
VO = json.load(open(os.path.join(DATA, "volumes.json")))
S24 = "24_volumes.py → data/volumes.json (per codebase: data/volumes.csv)"
for key, dec in (("lines_cw", 0), ("rw90_cw", 0), ("surv90_cw", 0), ("bug_cw", 2), ("test_cw", 2), ("test_kloc", 2), ("commits_mo", 0), ("bug_mo", 0), ("test_mo", 0)):
    v = VO[key]
    N(f"vol_{key}_before", f"{v['before']:,.{dec}f}", S24, "median level before adoption")
    N(f"vol_{key}_after", f"{v['after']:,.{dec}f}", S24, "median level after adoption")
    sm(f"vol_{key}", v["change"], S24, "per-codebase % change, before vs after", 0)
N("vol_test_lines_per_before", f"{1000 / VO['test_kloc']['before']:,.0f}", S24, "production lines committed per test-change commit (1,000 / median per KLOC)")
N("vol_test_lines_per_after", f"{1000 / VO['test_kloc']['after']:,.0f}", S24)
N("vol_ai_fu", f"{VO['ai_followups_per_change']:.2f}", S24, "median follow-ups per change, AI-attributed commits, after adoption")
N("vol_un_fu", f"{VO['un_followups_per_change']:.2f}", S24, "median follow-ups per change, unattributed commits, after adoption")
N("vol_ai_lines", f"{VO['ai_median_lines']:.0f}", S24, "median production lines per AI-attributed commit")
N("vol_un_lines", f"{VO['un_median_lines']:.0f}", S24, "median production lines per unattributed commit")
N("mr_ratio", f"{MR['after']['median'] / MR['before']['median']:.1f}", "17_monthly_rate.py → data/monthly_rate.json",
  "ratio of median monthly growth after vs before adoption; the before rate and the step-up are not statistically clear")

section("Method parameters (stated in kerno-audit-benchmark.pdf p.3-5, or set in our scripts)")
PDFM = "kerno-audit-benchmark.pdf p.3–5"
for k, v, src in [
    ("m_arm", "20", PDFM + " (n ≥ 20 per arm)"),
    ("m_events", "5", PDFM + " (≥ 5 events in the numerator)"),
    ("m_effect", "5%", PDFM + " (minimum movement)"),
    ("m_alpha", "0.05", PDFM + " (significance level)"),
    ("m_thresh", "25%", PDFM + " (absolute adoption threshold)"),
    ("m_trend_months", "8", PDFM + " (≥ 8 qualifying months to fit a trend)"),
    ("m_trend_obs", "5", PDFM + " (≥ 5 observations per month)"),
    ("m_window_rw", "30 and 90 days", "before_after.csv metric names"),
    ("m_boot", "10,000", "03_analysis.py / 04_forecast.py (B = 10000)"),
    ("m_sens_commits", "200", "03_analysis.py sensitivity rule"),
    ("m_metrics", str(len(KEYS)), "before_after.csv: distinct metrics"),
    ("m_sweep_metrics", "5", "Adoption date sweep.pdf p.1"),
    ("m_horizon", "12 and 24 months", "04_forecast.py HORIZONS"),
    ("x_cc_low", "1–10", "Software Engineering Institute risk categories, as published in Klocwork documentation (help.klocwork.com, McCabe Cyclomatic Complexity): low risk"),
    ("x_cc_mod", "11–20", "SEI categories (Klocwork documentation): moderate risk"),
    ("x_cc_high", "21–50", "SEI categories (Klocwork documentation): high risk"),
    ("x_cc_untest", "51", "SEI categories (Klocwork documentation): '51 and greater: an untestable program of very high risk'"),
    ("x_ms_systems", "five", "Nagappan, Ball, Zeller, 'Mining metrics to predict component failures', ICSE 2006 (MSR-TR-2005-149): five Microsoft systems"),
    ("x_mccabe", "10", "McCabe, T. J. (1976). A Complexity Measure. IEEE Transactions on Software Engineering, SE-2(4)"),
]:
    N(k, v, src)

json.dump(REG, open(os.path.join(DATA, "numbers.json"), "w"), indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- findings.md
L = ["# Findings log — Kerno 2026: The Impact of AI on Code Quality", "",
     "Generated by `analysis/06_numbers.py`; do not edit by hand. Every number the report prints is a key below, "
     "substituted into the template by `analysis/07_build.py`, which fails on any key not listed here.", "",
     "Rebuild everything: `cd analysis && python3 01_extract.py && python3 02_sweep_bars.py && python3 03_analysis.py "
     "&& python3 04_forecast.py && python3 10_raw_verify.py && python3 11_raw_commits.py && python3 12_raw_analysis.py "
     "&& python3 13_raw_followups_size.py && python3 14_raw_complexity_fixes.py && python3 15_raw_absolute.py && python3 16_commit_shares.py && python3 05_charts.py && python3 06_numbers.py && python3 07_build.py`", "",
     "## Standing caveats", "",
     "- **Source data.** The raw benchmark output (kerno-audit-benchmark-2026-10.zip, extracted to `analysis/raw/zip/`) is the source of truth; "
     "the two summary PDFs were verified against it (`analysis/data/raw_verify.txt`). Hashes in `analysis/raw/source-pdf-sha256.txt`. "
     "Still not computable: PR lead time, test coverage, test-to-source line ratio, maintainability index, defects and incidents.",
     "- **Attribution is a floor.** AI share counts only commits that name an agent; unlabelled commits are 'unknown', not human.",
     "- **Observational.** Before/after splits are confounded by anything else that changed at the same time; the placebo sweep "
     "shows complexity rising at every forced boundary.",
     "- **Unit of analysis is the repository**, so a 35,000-commit repo and a 500-commit repo count equally.", "",
     "## Things flagged as surprising", "",
     "1. Complexity per line rose whichever adoption month is forced (sweep: costly-way repos outnumber cheaper-way in "
     f"{REG['sw_cyc_wgt']['value']} of {REG['sw_months']['value']} forced months). The rise is not specific to adoption.",
     f"2. Undated repositories (attributed AI share ≤ {REG['ai_undated_max']['value']}) show the same rising complexity slope.",
     f"3. Follow-ups per change: the asserted-only median is {REG['fu_amed']['value']} (n = {REG['fu_an']['value']}), "
     f"but across all {REG['fu_n']['value']} repos it is {REG['fu_med']['value']} with CI {REG['fu_ci']['value']} — "
     "the audit's headline figure reflects which rows passed its gates.",
     f"4. Rework edits: the asserted median of {REG['rwe_amed']['value']} rests on {REG['rwe_an']['value']} repositories; across "
     f"all {REG['rwe_n']['value']} it is {REG['rwe_med']['value']} ({REG['rwe_p']['value']}). Kerno's earlier draft "
     "'Quality Bankruptcy' quoted 'rework +94%'; that figure should not be reused.",
     f"5. Rewriting of recent code fell: lines rewritten within 90 days fell in {REG['rw90_fell']['value']} of "
     f"{REG['rw90_n']['value']} repos.", "",
     "## New from the raw benchmark data (zip) — for review", "",
     f"6. The PDFs match the raw data exactly ({REG['rq_verify_rows']['value']} before/after rows, {REG['rq_verify_trends']['value']} trends; data/raw_verify.txt).",
     f"7. Whole-codebase share of functions above CC 10 rose in {REG['sn_all_rose']['value']} of {REG['sn_all_n']['value']} projects "
     f"({REG['sn_level_first']['value']} → {REG['sn_level_last']['value']} median). Faster after adoption in {REG['sn_pace_faster']['value']} of "
     f"{REG['sn_pace_n']['value']} dated projects, but {REG['sn_pace_p']['value']}: a hint, not a finding.",
     f"8. Output per contributor-week rose: production lines {REG['tp_lines_med']['value']} (CI {REG['tp_lines_ci']['value']}), PR-linked commits "
     f"{REG['tp_pr_med']['value']}; team size did not change consistently ({REG['tp_team_med']['value']}, {REG['tp_team_p']['value']}).",
     f"9. AI-labelled commits get {REG['fs_change_med']['value']} more follow-ups per change but are {REG['fs_size_med']['value']} larger; "
     f"per 100 lines the gap is {REG['fs_lines_med']['value']} ({REG['fs_lines_p']['value']}). Mostly a size effect.",
     f"10. Test-change commits rose from {REG['tp_test_before']['value']} to {REG['tp_test_after']['value']} of commits (median); bug-fix share "
     f"unchanged; reverts {REG['rv_before']['value']} → {REG['rv_after']['value']}.",
     f"11. Bug-fix classifier precision {REG['bf_prec']['value']}–{REG['bf_prec_len']['value']} on {REG['bf_n']['value']} commits, labelled by the "
     "analyst (an AI model) from subjects only; recall depends on conventional-commit prefixes.",
     f"12. The README's ρ = +0.04 (AI share vs complexity slope) uses the {REG['rho_est']['value'].split('n = ')[1]} clear trends; across all fitted "
     f"trends it is {REG['rho_fit']['value']}. Neither is significant.",
     f"13. Complexity vs later bug fixes (size-matched, 90 days): {REG['cf_fix_med']['value']} (CI {REG['cf_fix_ci']['value']}), "
     f"{REG['cf_fix_rose']['value']} up / {REG['cf_fix_fell']['value']} down across {REG['cf_repos']['value']} projects. No near-term link; reported as a null result.",
     f"14. Shares vs totals: the share of new lines rewritten fell ({REG['rw90_med']['value']}), but estimated rewritten lines per engineer-week "
     f"rose a median {REG['ab_rw90_med']['value']} (CI {REG['ab_rw90_ci']['value']}) and bug-fix commits per engineer-week {REG['ab_bug_med']['value']} "
     f"(CI {REG['ab_bug_ci']['value']}). Both lean up; neither is statistically clear (review comments 7 and 8). Dropped from the report on 2026-10-26.",
     f"15. Monthly growth of complexity density (17_monthly_rate.py): before adoption {REG['mr_before_med']['value']} ({REG['mr_before_p']['value']}), after "
     f"{REG['mr_after_med']['value']} ({REG['mr_after_p']['value']}), n = {REG['mr_after_n']['value']}; step-up {REG['mr_diff_med']['value']} ({REG['mr_diff_p']['value']}), "
     f"not clear in any of {REG['mr_sens_n']['value']} sensitivity variants. SURPRISE flagged to user: within-codebase rise before adoption is not clear; codebases "
     f"without an adoption date rise {REG['mr_undated_med']['value']} ({REG['mr_undated_p']['value']}). The user's '5x' is a ratio of two medians, one not clear; not used.",
     f"16. Maintainability grade (18_maintainability.py): benchmark-quartile grades on excess complexity per KLOC; {REG['mt_worse']['value']} of {REG['mt_n']['value']} "
     f"moved worse, {REG['mt_better']['value']} better. Reliability not graded: complexity does not predict 90-day fixes ({REG['cft_fix_med']['value']}, {REG['cft_fix_p']['value']}).",
     f"17. Denominators restricted to two groups (2026-10-26): 30 dated codebases for before/after; {REG['n_trend_repos']['value']} trend codebases for trends. "
     f"Within-period AI comparison recomputed on dated codebases only: follow-ups {REG['wd_fu_med']['value']} ({REG['wd_fu_p']['value']}), size {REG['fd_size_med']['value']}.",
     f"18. Report restructured to the user's five questions (2026-10-27). New: lines committed {REG['lr_before_med']['value']} -> {REG['lr_after_med']['value']} a month "
     f"(19_lines_rate.py); surviving-90-day output {REG['nl90_med']['value']} (20_net_lines.py); codebase size {REG['sz_growth_med']['value']} over {REG['sz_months']['value']} months; "
     f"extension share {REG['ext_before']['value']} -> {REG['ext_after']['value']} ({REG['ext_chg_p']['value']}); test commits per engineer {REG['tc_cw_med']['value']} (22_sprawl_extension_tests.py).",
     f"19. SURPRISE flagged to user: codebases without an adoption date also show rising lines committed ({REG['lr_undated_med']['value']} a month) and test share "
     f"({REG['tsr_undated_med']['value']}), so no trend is unique to AI adoption. Bug fixes per KLOC {REG['bk_kloc_med']['value']} is a commit-size artefact; not a headline.", "",
     ]
for name, keys in SECTIONS:
    L += [f"## {name}", "", "| Key | Value | Source | Caveat |", "|---|---|---|---|"]
    for k in keys:
        e = REG[k]
        L.append(f"| `{k}` | {e['value']} | {e['source']} | {e['caveat']} |")
    L.append("")
open(os.path.join(HERE, "..", "findings.md"), "w").write("\n".join(L))
print(f"{len(REG)} numbers registered")
