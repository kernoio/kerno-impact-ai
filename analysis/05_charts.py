"""Render every report figure as SVG into ../charts/ from the CSVs in data/.

Standard library only. Colours: red = costly direction, blue = cheaper
direction, grey = no declared direction / not asserted (palette validated with
the dataviz validator; red/green failed deutan separation, so blue replaces
green). Direction is always also carried by a text label or sign, never by
colour alone.
"""
import csv
import json
import math
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CHARTS = os.path.join(HERE, "..", "charts")
os.makedirs(CHARTS, exist_ok=True)

RED, BLUE, GREY = "#B8432F", "#2F6DB5", "#8A8A84"
RED_T, BLUE_T, GREY_T = "#E8C4BC", "#BFD2EA", "#D9D6CE"
INK, MUTED, RULE, PAPER, ACCENT = "#16181C", "#6B6B66", "#D9D6CE", "#FAF8F3", "#FF00DB"
SANS = "Inter, Helvetica, Arial, sans-serif"
MONO = "'IBM Plex Mono', Menlo, monospace"
W = 680


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))


def f(x):
    return None if x in ("", "None", None) else float(x)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=11, fill=INK, anchor="start", weight=400, family=SANS, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" {extra}>{esc(s)}</text>')


def line(x1, y1, x2, y2, stroke=RULE, width=1, extra=""):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" {extra}/>'


def svg(h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<rect width="{W}" height="{h}" fill="{PAPER}"/>{"".join(body)}</svg>')


def save(name, h, body, title):
    with open(os.path.join(CHARTS, name), "w") as fh:
        fh.write(svg(h, body, title))


def pct(v, d=0):
    if round(abs(v), d) == 0:
        return "0%"
    s = f"{abs(v):.{d}f}%"
    return ("+" if v > 0 else "−" if v < 0 else "") + s


repos = {r["repo"]: r for r in load("repos.csv")}
ba = load("before_after.csv")
tr = load("trends.csv")
summ = load("results_metric_summary.csv")
sweep = load("results_sweep.csv")
res = json.load(open(os.path.join(DATA, "results.json")))
fc = json.load(open(os.path.join(DATA, "forecast.json")))

LABEL = {
    "cyclomatic delta (per 100 production lines added)": "Complexity density (per 100 lines)",
    "excess complexity per KLOC": "Excess complexity per 1,000 lines",
    "lines rewritten within 30 days": "Lines rewritten within 30 days",
    "lines rewritten within 90 days": "Lines rewritten within 90 days",
    "rework edits (per 100 lines added)": "Rework edits per 100 lines",
    "follow-ups (per change)": "Follow-ups per change",
    "share of follow-ups that are repairs": "Share of follow-ups that are fixes",
    "reimplementations (per KLOC added)": "Reimplementations per 1,000 lines",
    "production lines added per commit": "Lines per commit",
    "days to first follow-up": "Days to first follow-up",
    "cyclomatic delta per commit": "Complexity added per commit",
}
AMBIG = {"production lines added per commit", "days to first follow-up"}


def colour(metric, v):
    if metric in AMBIG or v == 0:
        return GREY
    return RED if v > 0 else BLUE


# ---------------------------------------------------------------- Figure 1
# Strip plot: per-repo change for each metric, median + bootstrap CI.
ORDER = ["cyclomatic delta (per 100 production lines added)", "excess complexity per KLOC",
         "production lines added per commit", "lines rewritten within 30 days", "lines rewritten within 90 days",
         "rework edits (per 100 lines added)", "follow-ups (per change)", "share of follow-ups that are repairs",
         "reimplementations (per KLOC added)", "days to first follow-up"]
LO, HI = -100, 300
x0, x1 = 250, W - 90


def sx(v):
    return x0 + (max(LO, min(HI, v)) - LO) / (HI - LO) * (x1 - x0)


rowh = 34
top = 40
h = top + rowh * len(ORDER) + 54
b = []
for t in (-100, 0, 100, 200, 300):
    b.append(line(sx(t), top - 8, sx(t), top + rowh * len(ORDER), RULE if t else MUTED, 1))
    b.append(text(sx(t), top - 14, pct(t), 9, MUTED, "middle", family=MONO))
for i, m in enumerate(ORDER):
    y = top + rowh * i + rowh / 2
    s = next(x for x in summ if x["metric"] == m and x["subset"] == "all rows with a ratio")
    b.append(text(8, y - 2, LABEL[m], 11, INK, weight=500))
    dirn = "no good or bad direction" if m in AMBIG else f"{s['rose']} rose · {s['fell']} fell"
    b.append(text(8, y + 11, f"n={s['n']} · {dirn}", 9, MUTED, family=MONO))
    vals = sorted(f(x["change_pct"]) for x in ba if x["metric"] == m and f(x["change_pct"]) is not None)
    for k, v in enumerate(vals):
        jit = ((k * 7) % 5 - 2) * 2.2
        c = colour(m, v)
        b.append(f'<circle cx="{sx(v):.1f}" cy="{y + jit:.1f}" r="3.4" fill="{c}" fill-opacity="0.55" stroke="{PAPER}" stroke-width="1"/>')
        if v > HI:
            b.append(f'<path d="M{sx(v) + 5:.1f},{y + jit - 3:.1f} l4,3 l-4,3z" fill="{c}"/>')
    lo, hi, med = f(s["ci_low"]), f(s["ci_high"]), f(s["median"])
    b.append(f'<rect x="{sx(lo):.1f}" y="{y - 9:.1f}" width="{sx(hi) - sx(lo):.1f}" height="18" rx="3" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    b.append(line(sx(med), y - 11, sx(med), y + 11, INK, 2.2))
    b.append(text(W - 8, y + 4, pct(med, 0 if med == int(med) else 1), 10.5, INK, "end", 600, MONO))
b.append(text(8, h - 30, "Each dot is one codebase (30 codebases with an adoption date). Black tick: median.", 9, MUTED, family=MONO))
b.append(text(8, h - 18, "Box: 95% confidence interval of the median. Values above +300% sit at the right edge with an arrow.", 9, MUTED, family=MONO))
b.append(text(8, h - 6, "Red = got worse · blue = got better · grey = no good or bad direction.", 9, MUTED, family=MONO))
b.append(text(W - 8, top - 14, "median", 9, MUTED, "end", family=MONO))
save("fig01_all_metrics_strip.svg", h, b, "Per-repository change after the detected adoption month, every metric")


# ---------------------------------------------------------------- dumbbell helper
def dumbbell(name, metric, title, unit_fmt, xmax=None, ambiguous=False, note=""):
    rows = [x for x in ba if x["metric"] == metric and f(x["before"]) is not None and f(x["after"]) is not None]
    rows.sort(key=lambda x: (f(x["change_pct"]) if f(x["change_pct"]) is not None else 0))
    xmax = xmax or max(max(f(x["before"]), f(x["after"])) for x in rows) * 1.05
    a0, a1 = 150, W - 130
    rh = 11
    tp = 30
    hh = tp + rh * len(rows) + 46

    def X(v):
        return a0 + min(v, xmax) / xmax * (a1 - a0)

    body = []
    ticks = 5
    for k in range(ticks + 1):
        t = xmax * k / ticks
        body.append(line(X(t), tp - 6, X(t), tp + rh * len(rows), RULE, 1))
        body.append(text(X(t), tp - 10, unit_fmt(t), 9, MUTED, "middle", family=MONO))
    for i, x in enumerate(rows):
        y = tp + rh * i + rh / 2
        bv, av, ch = f(x["before"]), f(x["after"]), f(x["change_pct"])
        c = GREY if ambiguous or ch is None else colour(metric, ch)
        status = x["status"]
        body.append(text(a0 - 10, y + 3.5, x["repo"], 9.5, INK, "end", family=SANS))
        body.append(line(X(bv), y, X(av), y, c, 2.2, 'stroke-linecap="round"'))
        body.append(f'<circle cx="{X(bv):.1f}" cy="{y:.1f}" r="3.6" fill="{PAPER}" stroke="{c}" stroke-width="1.6"/>')
        body.append(f'<circle cx="{X(av):.1f}" cy="{y:.1f}" r="3.6" fill="{c}"/>')
        lab = (pct(ch) if ch is not None else "—")
        body.append(text(a1 + 22, y + 3.5, lab, 9.5, INK, "start", 500, MONO))
        verdict = {"asserted": "passed", "withheld": "inconclusive", "excluded": "excluded"}[status]
        body.append(text(W - 6, y + 3.5, verdict, 8.5, MUTED if status != "asserted" else INK, "end", family=MONO))
    body.append(text(a1 + 22, tp - 10, "change", 9, MUTED, family=MONO))
    body.append(text(W - 6, tp - 10, "audit verdict", 9, MUTED, "end", family=MONO))
    fy = tp + rh * len(rows) + 20
    body.append(f'<circle cx="14" cy="{fy - 3}" r="3.6" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>')
    body.append(text(22, fy, "before", 9, MUTED, family=MONO))
    body.append(f'<circle cx="72" cy="{fy - 3}" r="3.6" fill="{INK}"/>')
    body.append(text(80, fy, "after the adoption date", 9, MUTED, family=MONO))
    if note:
        body.append(text(8, fy + 16, note, 9, MUTED, family=MONO))
    save(name, hh, body, title)


dumbbell("fig02_cyclomatic_dumbbell.svg", "cyclomatic delta (per 100 production lines added)",
         "Cyclomatic delta per 100 production lines, before and after, 30 repositories", lambda t: f"{t:.0f}", 14,
         note="New decision points per 100 lines of production code. Red = got worse, blue = got better. Axis cut off at 14.")
dumbbell("fig06_lines_per_commit_dumbbell.svg", "production lines added per commit",
         "Lines per commit (median), before and after", lambda t: f"{t:.0f}", 100, ambiguous=True,
         note="Grey: change size has no good or bad direction. Median lines per commit in each period; axis cut off at 100.")
dumbbell("fig07_rewritten90_dumbbell.svg", "lines rewritten within 90 days",
         "Share of lines rewritten within 90 days, before and after", lambda t: f"{t * 100:.0f}%", 0.4,
         note="Share of new lines rewritten or deleted within 90 days. Red = got worse, blue = got better.")
dumbbell("fig08_reimplementations_dumbbell.svg", "reimplementations (per KLOC added)",
         "Reimplementations per KLOC added, before and after", lambda t: f"{t:.2f}", 0.75,
         note="Judged by an LLM: a change that rebuilt a feature the codebase already had. Red = got worse, blue = got better.")

# ---------------------------------------------------------------- Figure 3: sweep small multiples
SW = ["Cyclomatic delta", "Rework edits", "Follow-ups", "Reimplementations", "Repair share"]
SWLAB = {"Cyclomatic delta": "Complexity density (per 100 lines)", "Rework edits": "Rework edits per 100 lines",
         "Follow-ups": "Follow-ups per change", "Reimplementations": "Reimplementations per 1,000 lines",
         "Repair share": "Share of follow-ups that are fixes"}
adopt = res["dataset"]["adoption_months"]
pw, ph = 320, 150
body = []
for k, m in enumerate(SW):
    ox = 10 + (k % 2) * (pw + 20)
    oy = 10 + (k // 2) * (ph + 26)
    rows = [x for x in sweep if x["metric"] == m]
    mx = 36
    base = oy + 22 + (ph - 40) / 2
    scale = ((ph - 40) / 2) / mx
    body.append(text(ox, oy + 10, SWLAB[m], 10.5, INK, weight=600))
    body.append(line(ox, base, ox + pw, base, MUTED, 1))
    bw = (pw - 20) / len(rows)
    for i, x in enumerate(rows):
        bx = ox + 10 + i * bw
        wr, rt = int(x["wrong"]), int(x["right"])
        if x["month"] == "2026-02":
            body.append(f'<rect x="{bx - 1:.1f}" y="{oy + 18:.1f}" width="{bw:.1f}" height="{ph - 32:.1f}" fill="{GREY_T}" fill-opacity="0.5"/>')
        if wr:
            body.append(f'<rect x="{bx + 1:.1f}" y="{base - wr * scale:.1f}" width="{bw - 3:.1f}" height="{wr * scale:.1f}" rx="1.5" fill="{RED}"/>')
        if rt:
            body.append(f'<rect x="{bx + 1:.1f}" y="{base + 1:.1f}" width="{bw - 3:.1f}" height="{rt * scale:.1f}" rx="1.5" fill="{BLUE}"/>')
        if x["month"] in ("2025-01", "2025-07", "2026-01", "2026-07"):
            body.append(text(bx + bw / 2, oy + ph - 2, x["month"], 8, MUTED, "middle", family=MONO))
    peak_w = max(rows, key=lambda x: int(x["wrong"]))
    peak_r = max(rows, key=lambda x: int(x["right"]))
    body.append(text(ox + pw, oy + 24, f"max {peak_w['wrong']} worse", 8.5, RED, "end", family=MONO))
    body.append(text(ox + pw, oy + ph - 14, f"max {peak_r['right']} better", 8.5, BLUE, "end", family=MONO))
# legend panel in the empty sixth slot
lx, ly = 10 + pw + 20, 10 + 2 * (ph + 26)
body.append(f'<rect x="{lx}" y="{ly + 14}" width="10" height="10" fill="{RED}"/>')
body.append(text(lx + 16, ly + 23, "codebases that got worse", 9.5, INK))
body.append(f'<rect x="{lx}" y="{ly + 32}" width="10" height="10" fill="{BLUE}"/>')
body.append(text(lx + 16, ly + 41, "codebases that got better", 9.5, INK))
body.append(f'<rect x="{lx}" y="{ly + 50}" width="10" height="10" fill="{GREY_T}"/>')
body.append(text(lx + 16, ly + 59, "February 2026 (also printed as numbers)", 9.5, INK))
body.append(text(lx, ly + 84, "x-axis: the adoption date applied to all 45", 9, MUTED, family=MONO))
body.append(text(lx, ly + 97, "codebases, Dec 2024 to Jul 2026. Results the", 9, MUTED, family=MONO))
body.append(text(lx, ly + 110, "audit couldn't call are not counted.", 9, MUTED, family=MONO))
body.append(text(lx, ly + 123, "Counts read from the bar heights in the PDF.", 9, MUTED, family=MONO))
save("fig03_sweep_small_multiples.svg", 10 + 3 * (ph + 26), body,
     "Placebo sweep: repositories moving each way when one adoption month is forced on all")

# ---------------------------------------------------------------- Figure 4: adoption month histogram
months = []
y, mo = 2025, 6
while (y, mo) <= (2026, 8):
    months.append(f"{y}-{mo:02d}")
    mo += 1
    if mo == 13:
        y, mo = y + 1, 1
hh = 130
body = []
bx0, bw = 40, (W - 60) / len(months)
mx = max(adopt.values())
for i, m in enumerate(months):
    v = adopt.get(m, 0)
    x = bx0 + i * bw
    hgt = v / mx * 64
    if v:
        body.append(f'<rect x="{x + 2:.1f}" y="{90 - hgt:.1f}" width="{bw - 4:.1f}" height="{hgt:.1f}" rx="3" fill="{ACCENT if m == "2026-02" else INK}"/>')
        body.append(text(x + bw / 2, 84 - hgt, v, 10, INK, "middle", 600, MONO))
    body.append(text(x + bw / 2, 106, m[2:].replace("-", "/"), 8.5, MUTED, "middle", family=MONO))
body.append(line(bx0, 90, W - 20, 90, MUTED))
body.append(text(bx0, 126, "Adoption month, 30 codebases (27 dated by the step rule, 3 by the 25% rule).", 9, MUTED, family=MONO))
save("fig04_adoption_months.svg", hh, body, "Detected adoption months cluster in February 2026")

# ---------------------------------------------------------------- Figure 5: asserted vs all rows
rows = []
for m in ORDER:
    a = next(x for x in summ if x["metric"] == m and x["subset"] == "all rows with a ratio")
    s = next(x for x in summ if x["metric"] == m and x["subset"] == "asserted rows only")
    rows.append((m, a, s))
a0, a1 = 260, W - 30
LO5, HI5 = -60, 160


def X5(v):
    return a0 + (max(LO5, min(HI5, v)) - LO5) / (HI5 - LO5) * (a1 - a0)


rh, tp = 28, 34
hh = tp + rh * len(rows) + 36
body = []
for t in (-50, 0, 50, 100):
    body.append(line(X5(t), tp - 6, X5(t), tp + rh * len(rows), MUTED if t == 0 else RULE))
    body.append(text(X5(t), tp - 12, pct(t), 9, MUTED, "middle", family=MONO))
for i, (m, a, s) in enumerate(rows):
    y = tp + rh * i + rh / 2
    body.append(text(8, y + 4, LABEL[m], 10.5, INK))
    av = f(a["median"])
    body.append(f'<circle cx="{X5(av):.1f}" cy="{y:.1f}" r="4.5" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>')
    if s["n"] != "0":
        sv = f(s["median"])
        body.append(line(X5(av), y, X5(sv), y, GREY, 1.5))
        body.append(f'<circle cx="{X5(sv):.1f}" cy="{y:.1f}" r="4.5" fill="{colour(m, sv)}"/>')
        right = sv >= av and X5(sv) < a1 - 90
        body.append(text(X5(sv) + (8 if right else -8), y - 6, f"{pct(sv, 0 if sv == int(sv) else 1)} (n={s['n']})", 8.5, INK,
                         "start" if right else "end", family=MONO))
    else:
        body.append(text(X5(av) + 8, y - 6, "no passing results", 8.5, MUTED, family=MONO))
fy = tp + rh * len(rows) + 18
body.append(f'<circle cx="14" cy="{fy - 3}" r="4.5" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>')
body.append(text(22, fy, "median across all codebases (n = 28–30)", 9, MUTED, family=MONO))
body.append(f'<circle cx="340" cy="{fy - 3}" r="4.5" fill="{GREY}"/>')
body.append(text(348, fy, "median of results that passed the audit's checks", 9, MUTED, family=MONO))
save("fig05_asserted_vs_all.svg", hh, body, "Filtering to asserted rows changes the median for several metrics")

# ---------------------------------------------------------------- Figure 9: AI share vs cyclomatic change
m = "cyclomatic delta (per 100 production lines added)"
pts = [(float(repos[x["repo"]]["ai_share_pct"]), f(x["change_pct"]), x["repo"]) for x in ba
       if x["metric"] == m and f(x["change_pct"]) is not None]
a0, a1, t0, t1 = 60, W - 20, 20, 250
hh = 312


def PX(v):
    return a0 + v / 45 * (a1 - a0)


def PY(v):
    return t1 - (max(-50, min(420, v)) + 50) / 470 * (t1 - t0)


body = []
for t in (0, 100, 200, 300, 400):
    body.append(line(a0, PY(t), a1, PY(t), MUTED if t == 0 else RULE))
    body.append(text(a0 - 6, PY(t) + 3, pct(t), 9, MUTED, "end", family=MONO))
for t in (0, 10, 20, 30, 40):
    body.append(text(PX(t), t1 + 14, f"{t}%", 9, MUTED, "middle", family=MONO))
for ai, ch, rp in pts:
    body.append(f'<circle cx="{PX(ai):.1f}" cy="{PY(ch):.1f}" r="4" fill="{colour(m, ch)}" fill-opacity="0.75" stroke="{PAPER}" stroke-width="1.2"/>')
    if ch > 200 or ai > 40 or ch < 0:
        edge = ai > 40
        body.append(text(PX(ai) + (-7 if edge else 7), PY(ch) + (-5 if rp in ("prefect", "infisical") else 9 if rp in ("rallly", "plane") else 3), rp, 8.5, MUTED,
                         "end" if edge else "start", family=MONO))
d = res["dose_response_ai_share_vs_change"][m]
body.append(text(8, t1 + 32, "x: share of commits that name an AI tool (a minimum). y: change in complexity density.", 9, MUTED, family=MONO))
body.append(text(8, t1 + 45, f"Spearman ρ = {d['rho']:.2f}, permutation p = {d['p']:.2f}, n = {d['n']} codebases.", 9, MUTED, family=MONO))
save("fig09_ai_share_vs_cyclomatic.svg", hh, body, "Attributed AI share against the change in complexity per line")

# ---------------------------------------------------------------- Figure 10: trend slopes dated vs undated
m = "cyclomatic delta (per 100 production lines added)"
fitted = [x for x in tr if x["metric"] == m and x["status"] != "unfitted"]
a0, a1 = 130, W - 30
hh = 162
lo, hi = -0.3, 0.6


def SX(v):
    return a0 + (max(lo, min(hi, v)) - lo) / (hi - lo) * (a1 - a0)


body = []
for t in (-0.2, 0, 0.2, 0.4, 0.6):
    body.append(line(SX(t), 20, SX(t), 110, MUTED if t == 0 else RULE))
    body.append(text(SX(t), 124, f"{t:+.1f}".replace("-", "−"), 9, MUTED, "middle", family=MONO))
for j, (arm, lab) in enumerate((("measured", "dated"), ("undated", "undated"))):
    y = 45 + j * 45
    xs = [x for x in fitted if repos[x["repo"]]["status"] == arm]
    lab = f"{lab} ({len(xs)} with a trend)"
    body.append(text(8, y + 4, lab, 10.5, INK, weight=500))
    for k, x in enumerate(xs):
        v = f(x["slope_per_month"])
        est = x["status"] == "shown"
        c = (RED if v > 0 else BLUE) if est else GREY
        body.append(f'<circle cx="{SX(v):.1f}" cy="{y + ((k * 5) % 5 - 2) * 2.5:.1f}" r="4" fill="{c}" fill-opacity="{0.85 if est else 0.5}" stroke="{PAPER}" stroke-width="1"/>')
    med = st.median(f(x["slope_per_month"]) for x in xs)
    body.append(line(SX(med), y - 12, SX(med), y + 12, INK, 2.2))
body.append(text(8, 142, "Monthly change in complexity density, one dot per codebase. Tick: median.", 8.5, MUTED, family=MONO))
body.append(text(8, 155, "Coloured: clear trend (p ≤ 0.05, ≥ 5% change, direction holds when resampled). Grey: trend not clear.", 8.5, MUTED, family=MONO))
save("fig10_trend_slopes.svg", hh, body, "Complexity-per-line slopes, dated and undated repositories")

# ---------------------------------------------------------------- Figure 11: forecast
m = "cyclomatic delta (per 100 production lines added)"
F = fc[m]
a0, a1, t0, t1 = 60, W - 185, 20, 230
hh = 284
ymin, ymax = 4, 16


def FX(mo):
    return a0 + mo / 24 * (a1 - a0)


def FY(v):
    return t1 - (v - ymin) / (ymax - ymin) * (t1 - t0)


body = []
for t in range(4, 17, 2):
    body.append(line(a0, FY(t), a1, FY(t), RULE))
    body.append(text(a0 - 6, FY(t) + 3, t, 9, MUTED, "end", family=MONO))
for mo in (0, 6, 12, 18, 24):
    body.append(text(FX(mo), t1 + 14, f"+{mo} mo" if mo else "now", 9, MUTED, "middle", family=MONO))
base = F["base_level"]
SC = [("accelerated", RED, "Faster adoption"), ("current", INK, "Current trend"), ("controls", BLUE, "With quality controls (illustrative)")]
label_y = {"accelerated": FY(F["scenarios"]["accelerated"]["m24"]) - 14, "current": FY(F["scenarios"]["current"]["m24"]) + 16,
           "controls": FY(F["scenarios"]["controls"]["m24"]) + 3}
for name, c, lab in SC:
    s = F["scenarios"][name]
    lo_s, hi_s = s["slope_ci"]
    pts_hi = " ".join(f"{FX(mo):.1f},{FY(base + hi_s * mo):.1f}" for mo in range(0, 25, 2))
    pts_lo = " ".join(f"{FX(mo):.1f},{FY(max(0, base + lo_s * mo)):.1f}" for mo in range(24, -1, -2))
    body.append(f'<polygon points="{pts_hi} {pts_lo}" fill="{c}" fill-opacity="0.10"/>')
    body.append(line(FX(0), FY(base), FX(24), FY(base + s["median_slope"] * 24), c, 2))
    body.append(text(a1 + 8, label_y[name], f"{lab}", 9, c, weight=600))
    body.append(text(a1 + 8, label_y[name] + 12, f"{s['m24']:.1f} ({s['m24_range'][0]:.1f}–{s['m24_range'][1]:.1f})", 9, MUTED, family=MONO))
body.append(f'<circle cx="{FX(0):.1f}" cy="{FY(base):.1f}" r="4" fill="{INK}"/>')
body.append(text(FX(0) + 8, FY(base) + 14, f"median fitted level today: {base:.2f}", 9, MUTED, family=MONO))
body.append(text(8, hh - 20, "New decision points per 100 lines. Line: median monthly slope × months, from today's median level.", 8.5, MUTED, family=MONO))
body.append(text(8, hh - 8, "Band: 95% interval for that median slope (not the spread between codebases). Straight-line projection. 24-month values at right.", 8.5, MUTED, family=MONO))
save("fig11_forecast.svg", hh, body, "Projected complexity per line under three scenarios, 24 months")


# ---------------------------------------------------------------- raw-data figures
import sys  # noqa: E402
sys.path.insert(0, HERE)
from stats_util import describe  # noqa: E402


def strip(name, rows, title, notes, lo=-100, hi=300, rh=34):
    """rows: (label, sublabel, values, direction) with direction 'up_bad', 'up_good' or None."""
    sx0, sx1 = 260, W - 90

    def X(v):
        return sx0 + (max(lo, min(hi, v)) - lo) / (hi - lo) * (sx1 - sx0)

    tp = 40
    hh = tp + rh * len(rows) + 14 + 12 * len(notes)
    body = []
    step = 50 if hi - lo <= 200 else 100
    for t in range(lo, hi + 1, step):
        body.append(line(X(t), tp - 8, X(t), tp + rh * len(rows), MUTED if t == 0 else RULE))
        body.append(text(X(t), tp - 14, pct(t), 9, MUTED, "middle", family=MONO))
    body.append(text(W - 8, tp - 14, "median", 9, MUTED, "end", family=MONO))
    for i, (lab, sub, vals, dirn) in enumerate(rows):
        y = tp + rh * i + rh / 2
        vals = sorted(v for v in vals if v is not None)
        d = describe(vals, seed=8000 + i)
        body.append(text(8, y - 2, lab, 11, INK, weight=500))
        body.append(text(8, y + 11, f"n={d['n']} · {d['rose']} rose · {d['fell']} fell" + (f" · {sub}" if sub else ""), 9, MUTED, family=MONO))

        def col(v):
            if dirn is None or v == 0:
                return GREY
            return (RED if v > 0 else BLUE) if dirn == "up_bad" else (BLUE if v > 0 else RED)
        for k, v in enumerate(vals):
            jit = ((k * 7) % 5 - 2) * 2.2
            body.append(f'<circle cx="{X(v):.1f}" cy="{y + jit:.1f}" r="3.4" fill="{col(v)}" fill-opacity="0.55" stroke="{PAPER}" stroke-width="1"/>')
            if v > hi:
                body.append(f'<path d="M{X(v) + 5:.1f},{y + jit - 3:.1f} l4,3 l-4,3z" fill="{col(v)}"/>')
        body.append(f'<rect x="{X(d["ci_low"]):.1f}" y="{y - 9:.1f}" width="{X(d["ci_high"]) - X(d["ci_low"]):.1f}" height="18" rx="3" fill="none" stroke="{INK}" stroke-width="1.2"/>')
        body.append(line(X(d["median"]), y - 11, X(d["median"]), y + 11, INK, 2.2))
        body.append(text(W - 8, y + 4, pct(d["median"]), 10.5, INK, "end", 600, MONO))
    for j, n_ in enumerate(notes):
        body.append(text(8, tp + rh * len(rows) + 22 + 12 * j, n_, 9, MUTED, family=MONO))
    save(name, hh, body, title)


thr = load("raw_throughput_changes.csv")
strip("fig13_throughput_strip.svg", [
    ("Active contributors per week", "team size check", [f(r["active_per_week_change_pct"]) for r in thr], None),
    ("Commits per contributor-week", "", [f(r["commits_per_cw_change_pct"]) for r in thr], None),
    ("PR-linked commits per contributor-week", "", [f(r["pr_commits_per_cw_change_pct"]) for r in thr], None),
    ("Production lines per contributor-week", "", [f(r["prod_lines_per_cw_change_pct"]) for r in thr], None),
], "Output per contributor, before vs after the adoption date",
    ["Each dot is one codebase (30 with an adoption date). Black tick: median. Box: 95% confidence interval of the median.",
     "Non-bot commits only. Values above +300% sit at the right edge with an arrow."])

# Early quality signals: what share of work is fixing, undoing or testing, before vs after adoption
FITTED = {x["repo"] for x in tr if x["metric"] == "cyclomatic delta (per 100 production lines added)" and x["status"] != "unfitted"}
cfx = [r for r in load("raw_complexity_fixes.csv") if int(r["fix_events"]) >= 20 and f(r["fix_gap_pct"]) is not None and r["repo"] in FITTED]
strip("fig18_quality_signals.svg", [
    ("Share of commits that are bug fixes", "", [f(r["bugfix_share_change_pct"]) for r in thr], "up_bad"),
    ("Share of commits that are reverts", "", [f(r["revert_share_change_pct"]) for r in thr], "up_bad"),
    ("Share of commits that change tests", "", [f(r["test_share_change_pct"]) for r in thr], "up_good"),
    ("Complex vs simpler commits fixed in 90 days", "same size", [f(r["fix_gap_pct"]) for r in cfx], "up_bad"),
], "Bug fixes, reverts, tests and early fixes to complex code",
    ["Rows 1-3: % change per codebase, before vs after adoption (30 with an adoption date;",
     "reverts: those with reverts before adoption). Red = worse, blue = better.",
     "Row 4: how much more often high- than low-complexity commits of the same size get a",
     "bug fix within 90 days (codebases with a trend, at least 20 fix events). Box: 95% CI."])

fs = load("raw_followups_size.csv")
wi = [r for r in load("raw_within.csv") if r["metric"] == "complexity density" and f(r["relative_pct"]) is not None and int(r["ai_n"] or 0) >= 20]
strip("fig14_ai_vs_unlabelled.svg", [
    ("Follow-ups per change", "", [f(r["fu_per_change_gap_pct"]) for r in fs], "up_bad"),
    ("Lines per commit", "size", [f(r["median_lines_gap_pct"]) for r in fs], None),
    ("Follow-ups per 100 lines", "size-adjusted", [f(r["fu_per_100_lines_gap_pct"]) for r in fs], "up_bad"),
    ("Complexity density", "", [f(r["relative_pct"]) for r in wi], "up_bad"),
], "AI-labelled commits compared with unlabelled commits in the same project and period",
    ["Each dot is one project (>= 20 AI-labelled commits), same project and period. Black tick: median.",
     "Unlabelled is not the same as human-written, so these gaps are likely understated."], lo=-100, hi=200, rh=27)

# Share of functions above complexity 10, first vs last snapshot, all measured projects
sn = load("raw_snapshots.csv")
sn.sort(key=lambda r: f(r["complex_share_change_pct"]) or 0)
a0, a1 = 150, W - 130
rh, tp = 11.5, 30
hh = tp + rh * len(sn) + 50
xmax = 0.07
body = []


def SX2(v):
    return a0 + min(v, xmax) / xmax * (a1 - a0)


for k in range(8):
    t = xmax * k / 7
    body.append(line(SX2(t), tp - 6, SX2(t), tp + rh * len(sn), RULE))
    body.append(text(SX2(t), tp - 10, f"{t * 100:.0f}%", 9, MUTED, "middle", family=MONO))
for i, r in enumerate(sn):
    y = tp + rh * i + rh / 2
    b, a, ch = f(r["complex_share_first"]), f(r["complex_share_last"]), f(r["complex_share_change_pct"])
    c = colour("x", ch) if ch is not None else GREY
    body.append(text(a0 - 10, y + 3.5, r["repo"] + ("" if r["status"] == "dated" else " ·"), 9, INK, "end"))
    body.append(line(SX2(b), y, SX2(a), y, c, 2, 'stroke-linecap="round"'))
    body.append(f'<circle cx="{SX2(b):.1f}" cy="{y:.1f}" r="3.2" fill="{PAPER}" stroke="{c}" stroke-width="1.5"/>')
    body.append(f'<circle cx="{SX2(a):.1f}" cy="{y:.1f}" r="3.2" fill="{c}"/>')
    body.append(text(a1 + 22, y + 3.5, pct(ch) if ch is not None else "—", 9, INK, "start", 500, MONO))
fy = tp + rh * len(sn) + 18
body.append(f'<circle cx="14" cy="{fy - 3}" r="3.4" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>')
body.append(text(22, fy, "first snapshot in the window", 9, MUTED, family=MONO))
body.append(f'<circle cx="190" cy="{fy - 3}" r="3.4" fill="{INK}"/>')
body.append(text(198, fy, "last snapshot (Oct 2026). · = undated project", 9, MUTED, family=MONO))
body.append(text(8, fy + 16, "Share of all functions in the codebase with cyclomatic complexity above 10. Red = rose, blue = fell. Axis cut off at 7%.", 9, MUTED, family=MONO))
save("fig12_complex_functions.svg", hh, body, "Share of functions above complexity 10, first vs last snapshot, 45 projects")


# ---------------------------------------------------------------- At a glance (executive summary)
raw = json.load(open(os.path.join(DATA, "raw_results.json")))


def summ_row(metric):
    x = next(r for r in summ if r["metric"] == metric and r["subset"] == "all rows with a ratio")
    return f(x["median"]), f(x["ci_low"]), f(x["ci_high"]), int(x["n"])


def raw_row(d):
    return d["median"], d["ci_low"], d["ci_high"], d["n"]


G = [  # label, (median, lo, hi, n), direction: 'up_bad' / 'up_good' / None
    ("Complexity density (per 100 lines)", summ_row("cyclomatic delta (per 100 production lines added)"), "up_bad"),
    ("Excess complexity per KLOC", summ_row("excess complexity per KLOC"), "up_bad"),
    ("Lines per commit", summ_row("production lines added per commit"), None),
    ("Production lines per contributor-week", raw_row(raw["throughput"]["prod_lines_per_cw"]), None),
    ("Lines rewritten within 90 days", summ_row("lines rewritten within 90 days"), "up_bad"),
    ("Share of follow-ups that are repairs", summ_row("share of follow-ups that are repairs"), "up_bad"),
    ("Reimplementations per KLOC added", summ_row("reimplementations (per KLOC added)"), "up_bad"),
    ("Follow-ups per change", summ_row("follow-ups (per change)"), "up_bad"),
    ("Share of commits that are bug fixes", raw_row(raw["throughput"]["bugfix_share"]), "up_bad"),
    ("Test-change commits per contributor-week", (lambda d: (d["median"], d["ci"][0], d["ci"][1], d["n"]))(
        json.load(open(os.path.join(DATA, "sprawl_extension_tests.json")))["tests"]["per_cw_change"]), "up_good"),
]
a0, a1 = 270, W - 70
lo_, hi_ = -50, 125


def GX(v):
    return a0 + (max(lo_, min(hi_, v)) - lo_) / (hi_ - lo_) * (a1 - a0)


rh, tp = 27, 30
hh = tp + rh * len(G) + 34
body = []
for t in (-50, 0, 50, 100):
    body.append(line(GX(t), tp - 6, GX(t), tp + rh * len(G), MUTED if t == 0 else RULE))
    body.append(text(GX(t), tp - 11, pct(t), 9, MUTED, "middle", family=MONO))
for i, (lab, (med, lo, hi, n), dirn) in enumerate(G):
    y = tp + rh * i + rh / 2
    clear = lo > 0 or hi < 0
    c = GREY if (dirn is None or not clear) else (RED if (med > 0) == (dirn == "up_bad") else BLUE)
    body.append(text(8, y + 4, lab, 10.5, INK))
    body.append(line(GX(lo), y, GX(hi), y, c, 3, 'stroke-linecap="round" stroke-opacity="0.45"'))
    if hi > hi_:
        body.append(f'<path d="M{GX(hi_) + 3:.1f},{y - 4:.1f} l5,4 l-5,4z" fill="{c}" fill-opacity="0.6"/>')
    body.append(f'<circle cx="{GX(med):.1f}" cy="{y:.1f}" r="5" fill="{c}" stroke="{PAPER}" stroke-width="1.5"/>')
    body.append(text(W - 8, y + 4, pct(med, 1 if abs(med * 2 - round(med * 2)) < 1e-9 and med != int(med) else 0), 10.5, INK, "end", 600, MONO))
body.append(text(8, hh - 14, "Dot: median change per codebase with an adoption date, before vs after that date.", 8.5, MUTED, family=MONO))
body.append(text(8, hh - 2, "Bar: 95% confidence interval. Red = worse, blue = better, grey = no direction or not statistically clear.", 8.5, MUTED, family=MONO))
save("fig00_at_a_glance.svg", hh, body, "Headline changes at a glance")

# ---------------------------------------------------------------- Stack Overflow 2026 trust question
SO = [("For many tasks, including important decisions", 6.6), ("For many tasks, but not important decisions", 16.3),
      ("When I can easily verify the output", 48.0), ("For low-risk tasks only", 16.3),
      ("Not for most work tasks", 12.3), ("Not sure / don't use AI", 0.5)]
a0, a1 = 290, W - 60
rh, tp = 21, 8
hh = tp + rh * len(SO) + 30
body = []
for i, (lab, v) in enumerate(SO):
    y = tp + rh * i
    body.append(text(a0 - 10, y + rh / 2 + 4, lab, 10.5, INK, "end"))
    w_ = v / 50 * (a1 - a0)
    hl = lab.startswith("When I can")
    body.append(f'<rect x="{a0}" y="{y + 5}" width="{max(w_, 2):.1f}" height="{rh - 10}" rx="3" fill="{INK if hl else GREY}"/>')
    body.append(text(a0 + w_ + 6, y + rh / 2 + 4, f"{v:.1f}%", 10.5, INK, "start", 600 if hl else 400, MONO))
body.append(text(8, hh - 6, "\"How much do you trust the output from AI tools or AI agents as part of your workflow?\" n = 14,304.", 8.5, MUTED, family=MONO))
save("fig15_so_trust.svg", hh, body, "How developers trust AI output, Stack Overflow 2026")


# Narrow (one-column) version of the trust chart for the introduction
SO_N = [("Incl. important decisions", 6.6), ("Many tasks, not important ones", 16.3),
        ("When I can easily verify it", 48.0), ("Low-risk tasks only", 16.3),
        ("Not for most work", 12.3), ("Not sure / no AI", 0.5)]
NW = 330
a0, a1 = 150, NW - 46
rh, tp = 13, 1
hh = tp + rh * len(SO_N) + 3
body = []
for i, (lab, v) in enumerate(SO_N):
    y = tp + rh * i
    hl = lab.startswith("When I can")
    body.append(text(a0 - 7, y + rh / 2 + 3.5, lab, 9.5, INK, "end", 600 if hl else 400))
    w_ = v / 50 * (a1 - a0)
    body.append(f'<rect x="{a0}" y="{y + 4}" width="{max(w_, 1.5):.1f}" height="{rh - 8}" rx="2.5" fill="{INK if hl else GREY}"/>')
    body.append(text(a0 + w_ + 5, y + rh / 2 + 3.5, f"{v:.1f}%", 9.5, INK, "start", 600 if hl else 400, MONO))
with open(os.path.join(CHARTS, "fig15_so_trust_narrow.svg"), "w") as fh:
    fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {NW} {hh}" width="{NW}" height="{hh}" role="img" '
             f'aria-label="How much developers trust AI output"><title>How much developers trust AI output, Stack Overflow 2026</title>'
             f'<rect width="{NW}" height="{hh}" fill="{PAPER}"/>{"".join(body)}</svg>')


# ---------------------------------------------------------------- Finding 1: every codebase's complexity trend, one tile each
m = "cyclomatic delta (per 100 production lines added)"
rows_ = [x for x in tr if x["metric"] == m]
order = {"shown": 0, "unestablished": 1, "flat": 1, "withheld": 1, "unfitted": 2}
def tile_status(x):
    if x["status"] == "shown":
        return "rise" if f(x["slope_per_month"]) > 0 else "fall"
    return "none" if x["status"] != "unfitted" else "nodata"
rows_.sort(key=lambda x: ({"rise": 0, "fall": 1, "none": 2, "nodata": 3}[tile_status(x)], -(f(x["slope_per_month"]) or 0)))
cols, tw, th, gap = 6, 106, 30, 4
x0, y0 = 4, 4
nrows = (len(rows_) + cols - 1) // cols
hh = y0 + nrows * (th + gap) + 40
body = []
fill = {"rise": RED, "fall": BLUE, "none": GREY_T, "nodata": PAPER}
ink = {"rise": "#FFFFFF", "fall": "#FFFFFF", "none": INK, "nodata": MUTED}
for i, x in enumerate(rows_):
    st_ = tile_status(x)
    cx, cy = x0 + (i % cols) * (tw + gap), y0 + (i // cols) * (th + gap)
    stroke = f' stroke="{RULE}" stroke-width="1"' if st_ == "nodata" else ""
    body.append(f'<rect x="{cx}" y="{cy}" width="{tw}" height="{th}" rx="3" fill="{fill[st_]}"{stroke}/>')
    body.append(text(cx + tw / 2, cy + th / 2 + 4, x["repo"], 9.5, ink[st_], "middle", 500))
counts = {k: sum(tile_status(x) == k for x in rows_) for k in ("rise", "fall", "none", "nodata")}
ly = hh - 22
items = [("rise", f"clear rise ({counts['rise']})"), ("fall", f"clear fall ({counts['fall']})"),
         ("none", f"no clear trend ({counts['none']})"), ("nodata", f"too little data ({counts['nodata']})")]
lx = 4
for k, lab in items:
    stroke = f' stroke="{RULE}" stroke-width="1"' if k == "nodata" else ""
    body.append(f'<rect x="{lx}" y="{ly - 9}" width="11" height="11" rx="2" fill="{fill[k]}"{stroke}/>')
    body.append(text(lx + 16, ly, lab, 9.5, INK))
    lx += 165
body.append(text(4, hh - 4, "Each tile is one codebase. Clear = permutation p ≤ 0.05, ≥ 5% change over the window, direction holds when resampled.", 8.5, MUTED, family=MONO))
save("fig16_trend_tiles.svg", hh, body, "Complexity trend for every codebase")


# ---------------------------------------------------------------- Dataset: the two bases every result uses
cs = json.load(open(os.path.join(DATA, "commit_shares.json")))
T = cs["total_commits"]
a0, a1 = 10, W - 10
bases = [("dated", INK, "Before/after comparisons", f"{cs['dated']['codebases']} codebases with an AI adoption date"),
         ("trend_fitted", "#4A5060", "Trends and growth rates", f"{cs['trend_fitted']['codebases']} codebases with enough monthly history for a trend")]
hh = 30 + 62 * len(bases)
body = [text(a0, 16, f"All {T:,} commits across {cs['codebases']} codebases", 10.5, INK, weight=600)]
for i, (k, c, use, lab) in enumerate(bases):
    y = 28 + 62 * i
    w_ = (a1 - a0) * cs[k]["commits"] / T
    body.append(f'<rect x="{a0}" y="{y}" width="{a1 - a0}" height="30" rx="3" fill="{RULE}" fill-opacity="0.5"/>')
    body.append(f'<rect x="{a0}" y="{y}" width="{w_:.1f}" height="30" rx="3" fill="{c}"/>')
    body.append(text(a0 + 10, y + 20, f"{cs[k]['commits']:,} commits", 11.5, "#FFFFFF", weight=700, family=MONO))
    body.append(text(a0 + 2, y + 45, f"{use}: {lab}", 9.5, INK, weight=500))
save("fig17_dataset.svg", hh, body, "The two groups of codebases every result is based on")

# ---------------------------------------------------------------- Top 10 complexity risers, before vs after adoption
CYCM = "cyclomatic delta (per 100 production lines added)"
top = sorted([r for r in ba if r["metric"] == CYCM and r["status"] == "asserted" and f(r["change_pct"]) is not None],
             key=lambda r: -f(r["change_pct"]))[:10]
a0, a1 = 170, W - 80
vmax = max(f(r["after"]) for r in top) * 1.08
rh, tp = 26, 34


def TX(v):
    return a0 + v / vmax * (a1 - a0)


hh = tp + rh * len(top) + 30
body = []
for t in range(0, int(vmax) + 1, 2):
    body.append(line(TX(t), tp - 8, TX(t), tp + rh * len(top), MUTED if t == 0 else RULE))
    body.append(text(TX(t), tp - 14, str(t), 9, MUTED, "middle", family=MONO))
body.append(text(W - 8, tp - 14, "change", 9, MUTED, "end", family=MONO))
for i, r in enumerate(top):
    y = tp + rh * i + rh / 2
    b0, b1 = f(r["before"]), f(r["after"])
    body.append(text(8, y + 4, r["repo"], 11, INK, weight=500))
    body.append(line(TX(b0), y, TX(b1), y, RED_T, 5))
    body.append(f'<circle cx="{TX(b0):.1f}" cy="{y:.1f}" r="4.5" fill="{PAPER}" stroke="{GREY}" stroke-width="1.8"/>')
    body.append(f'<circle cx="{TX(b1):.1f}" cy="{y:.1f}" r="4.5" fill="{RED}"/>')
    body.append(text(W - 8, y + 4, pct(f(r["change_pct"])), 10.5, RED, "end", 600, MONO))
body.append(text(8, tp + rh * len(top) + 20, "Open circle: before adoption. Filled: after. Decision points added per 100 new production lines.", 9, MUTED, family=MONO))
save("fig19_top_risers.svg", hh, body, "Top 10 complexity risers before and after AI adoption")

# ---------------------------------------------------------------- Maintainability grade heatmap
mt = load("maintainability.csv")
mt.sort(key=lambda r: (r["grade_last"], -ord(r["grade_first"]), float(r["excess_last"])))
GRADE = {"A": ("#DCE7F4", INK), "B": ("#F3E4D6", INK), "C": ("#E2A08F", INK), "D": (RED, "#FFFFFF")}
cols = [("Start", 190), ("End", 250), ("Excess per KLOC", 410), ("Functions above 10", 570)]
rh, tp = 13.5, 40
hh = tp + rh * len(mt) + 34
body = [text(220, tp - 22, "Maintainability grade", 8.5, MUTED, "middle", family=MONO),
        text(cols[2][1], tp - 22, "start → end", 8.5, MUTED, "middle", family=MONO),
        text(cols[3][1], tp - 22, "start → end", 8.5, MUTED, "middle", family=MONO)]
for lab, x in cols:
    body.append(text(x, tp - 8, lab, 9, MUTED, "middle", family=MONO))
for i, r in enumerate(mt):
    y = tp + rh * i
    body.append(text(8, y + 10, r["repo"] + ("" if r["status"] == "dated" else " ·"), 9.5, INK))
    for g, x in ((r["grade_first"], cols[0][1]), (r["grade_last"], cols[1][1])):
        bg, fg = GRADE[g]
        body.append(f'<rect x="{x - 26}" y="{y + 1}" width="52" height="{rh - 2}" fill="{bg}"/>')
        body.append(text(x, y + 10, g, 9, fg, "middle", 600, MONO))
    mv = ord(r["grade_last"]) - ord(r["grade_first"])
    if mv:
        body.append(text(cols[1][1] + 32, y + 10, ("▲" if mv > 0 else "▼") * abs(mv), 8, RED if mv > 0 else BLUE, family=MONO))
    body.append(text(cols[2][1], y + 10, f'{float(r["excess_first"]):.1f} → {float(r["excess_last"]):.1f}', 9, INK, "middle", family=MONO))
    body.append(text(cols[3][1], y + 10, f'{100 * float(r["complex_share_first"]):.1f}% → {100 * float(r["complex_share_last"]):.1f}%', 9, INK, "middle", family=MONO))
mtj = json.load(open(os.path.join(DATA, "maintainability.json")))
c1, c2, c3 = mtj["cuts"]
yb = tp + rh * len(mt) + 16
x = 8
for g, rng in (("A", f"≤ {c1:.1f}"), ("B", f"{c1:.1f}–{c2:.1f}"), ("C", f"{c2:.1f}–{c3:.1f}"), ("D", f"> {c3:.1f}")):
    bg, fg = GRADE[g]
    body.append(f'<rect x="{x}" y="{yb - 9}" width="14" height="12" fill="{bg}"/>')
    body.append(text(x + 7, yb + 1, g, 8.5, fg, "middle", 600, MONO))
    body.append(text(x + 19, yb + 1, rng, 8.5, MUTED, family=MONO))
    x += 92
body.append(text(x + 6, yb + 1, "▲ grade worse  ▼ better  · no adoption date", 8.5, MUTED, family=MONO))
save("fig20_maintainability.svg", hh, body, "Maintainability grade for each codebase, start and end of the window")

# ---------------------------------------------------------------- Monthly growth rates before vs after adoption (complexity, lines)
def rate_pairs(name, csvname, bcol, acol, lo_, hi_, step, title, note):
    pr = [r for r in load(csvname) if r[bcol] not in ("", "None") and r[acol] not in ("", "None")]
    pr.sort(key=lambda r: float(r[acol]))
    a0, a1 = 170, W - 30
    rh, tp = 14, 34

    def MX(v):
        return a0 + (max(lo_, min(hi_, v)) - lo_) / (hi_ - lo_) * (a1 - a0)

    hh = tp + rh * len(pr) + 30
    body = []
    for t in range(lo_, hi_ + 1, step):
        body.append(line(MX(t), tp - 8, MX(t), tp + rh * len(pr), MUTED if t == 0 else RULE))
        body.append(text(MX(t), tp - 14, pct(t), 9, MUTED, "middle", family=MONO))
    for i, r in enumerate(pr):
        y = tp + rh * i + rh / 2
        b0, b1 = float(r[bcol]), float(r[acol])
        body.append(text(8, y + 4, r["repo"], 9.5, INK))
        body.append(line(MX(b0), y, MX(b1), y, RED_T if b1 > b0 else BLUE_T, 3))
        body.append(f'<circle cx="{MX(b0):.1f}" cy="{y:.1f}" r="3.6" fill="{PAPER}" stroke="{GREY}" stroke-width="1.6"/>')
        body.append(f'<circle cx="{MX(b1):.1f}" cy="{y:.1f}" r="3.6" fill="{RED if b1 > 0 else BLUE}"/>')
    body.append(text(8, tp + rh * len(pr) + 20, note, 9, MUTED, family=MONO))
    save(name, hh, body, title)


rate_pairs("fig21_monthly_rates.svg", "monthly_rate.csv", "rate_before", "rate_after", -15, 20, 5,
           "Monthly growth in complexity density before and after adoption, per codebase",
           "Open circle: monthly growth before adoption. Filled: after. Values beyond the axis sit at its edge.")
rate_pairs("fig23_lines_rates.svg", "lines_rate.csv", "lines_before", "lines_after", -15, 25, 5,
           "Monthly growth in production lines committed before and after adoption, per codebase",
           "Open circle: monthly growth before adoption. Filled: after. Values beyond the axis sit at its edge.")

# ---------------------------------------------------------------- Month-by-month complexity around adoption (event time)
msr = load("monthly_series.csv")
xs_ = [int(r["rel_month"]) for r in msr]
a0, a1, t0, t1 = 70, W - 20, 30, 250
ylo, yhi = 40, 200


def EX(k):
    return a0 + (k - xs_[0]) / (xs_[-1] - xs_[0]) * (a1 - a0)


def EY(v):
    return t1 - (min(max(v, ylo), yhi) - ylo) / (yhi - ylo) * (t1 - t0)


hh = t1 + 62
body = []
for v in range(ylo, yhi + 1, 20):
    body.append(line(a0, EY(v), a1, EY(v), MUTED if v == 100 else RULE, 1.2 if v == 100 else 1))
    body.append(text(a0 - 6, EY(v) + 3, pct(v - 100), 9, MUTED, "end", family=MONO))
body.append(f'<rect x="{EX(0) - 0.5:.1f}" y="{t0}" width="{EX(xs_[-1]) - EX(0) + 0.5:.1f}" height="{t1 - t0}" fill="{RED_T}" fill-opacity="0.18"/>')
band = " ".join(f"{EX(int(r['rel_month'])):.1f},{EY(float(r['q3'])):.1f}" for r in msr) + " " + \
    " ".join(f"{EX(int(r['rel_month'])):.1f},{EY(float(r['q1'])):.1f}" for r in reversed(msr))
body.append(f'<polygon points="{band}" fill="{GREY_T}" fill-opacity="0.75"/>')
pre_ = [r for r in msr if int(r["rel_month"]) < 0]
post_ = [r for r in msr if int(r["rel_month"]) >= 0]
for seg, c in ((pre_, GREY), (post_, RED)):
    pts = " ".join(f"{EX(int(r['rel_month'])):.1f},{EY(float(r['median'])):.1f}" for r in seg)
    body.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2.6"/>')
    for r in seg:
        body.append(f'<circle cx="{EX(int(r["rel_month"])):.1f}" cy="{EY(float(r["median"])):.1f}" r="3" fill="{c}"/>')
body.append(line(EX(-1), EY(float(pre_[-1]["median"])), EX(0), EY(float(post_[0]["median"])), RED, 2.6, 'stroke-dasharray="3 2"'))
body.append(line(EX(0), t0 - 6, EX(0), t1, INK, 1.2, 'stroke-dasharray="4 3"'))
body.append(text(EX(0) + 5, t0 + 4, "AI adoption month", 9.5, INK, weight=600))
body.append(text(EX(xs_[-1]), EY(float(post_[-1]["median"])) - 9, pct(float(post_[-1]["median"]) - 100), 10, RED, "end", 700, MONO))
body.append(text(EX(-1), EY(float(pre_[-1]["median"])) + 16, pct(float(pre_[-1]["median"]) - 100), 10, GREY, "middle", 700, MONO))
for r in msr:
    k = int(r["rel_month"])
    body.append(text(EX(k), t1 + 14, f"{k:+d}" if k else "0", 8.5, MUTED, "middle", family=MONO))
    body.append(text(EX(k), t1 + 27, r["n"], 7.5, MUTED, "middle", family=MONO))
body.append(text(8, t1 + 14, "month", 8.5, MUTED, family=MONO))
body.append(text(8, t1 + 27, "codebases", 7.5, MUTED, family=MONO))
body.append(text(8, t1 + 46, "Line: median change in each codebase's complexity vs its own average for the six months before adoption (0% = no change).", 8.5, MUTED, family=MONO))
body.append(text(8, t1 + 58, "Band: middle half of codebases. n: codebases with enough production lines that month.", 8.5, MUTED, family=MONO))
save("fig24_monthly_series.svg", hh, body, "Complexity density month by month, before and after AI adoption")

# ---------------------------------------------------------------- Rework metrics, before vs after adoption
def ba_vals(metric):
    return [f(r["change_pct"]) for r in ba if r["metric"] == metric and f(r["change_pct"]) is not None]


strip("fig22_rework_strip.svg", [
    ("Lines rewritten within 30 days", "forward", ba_vals("lines rewritten within 30 days"), "up_bad"),
    ("Lines rewritten within 90 days", "forward", ba_vals("lines rewritten within 90 days"), "up_bad"),
    ("Rework edits per 100 lines added", "backward", ba_vals("rework edits (per 100 lines added)"), "up_bad"),
    ("Follow-ups per change", "", ba_vals("follow-ups (per change)"), "up_bad"),
    ("Share of follow-ups that are repairs", "model verdict", ba_vals("share of follow-ups that are repairs"), "up_bad"),
    ("Reimplementations per KLOC added", "model verdict", ba_vals("reimplementations (per KLOC added)"), "up_bad"),
], "Rework, follow-up and repair rates before vs after the adoption date",
    ["Each dot is one codebase with an adoption date. Black tick: median. Box: 95% confidence interval of the median.",
     "Red = rose (worse), blue = fell (better). Values above +300% sit at the right edge with an arrow."])

# ---------------------------------------------------------------- Cover art: every fitted complexity trend line
m = "cyclomatic delta (per 100 production lines added)"
fitted = [x for x in tr if x["metric"] == m and x["status"] != "unfitted"]
CW, CH = 816, 520
body = [f'<rect width="{CW}" height="{CH}" fill="#0E1116"/>']
for x in fitted:
    s0, e0 = f(x["start"]), f(x["end"])
    est = x["status"] == "shown"
    c = ACCENT if est else "#5A6070"
    y0 = CH - 40 - (s0 + 5) / 25 * (CH - 80)
    y1 = CH - 40 - (e0 + 5) / 25 * (CH - 80)
    body.append(f'<line x1="40" y1="{y0:.1f}" x2="{CW - 40}" y2="{y1:.1f}" stroke="{c}" stroke-width="{1.8 if est else 1}" stroke-opacity="{0.9 if est else 0.6}"/>')
with open(os.path.join(CHARTS, "cover_trendlines.svg"), "w") as fh:
    fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}" '
             f'role="img" aria-label="Fitted complexity trend lines, one per repository"><title>Fitted complexity-per-line trend line for each of {len(fitted)} repositories; magenta = established trend</title>{"".join(body)}</svg>')

print("charts:", sorted(os.listdir(CHARTS)))
