"""Recover the per-month counts behind the sweep panels in 'Adoption date sweep.pdf'.

The panels ("The same question at every other date") are vector bars; their
counts are not in the PDF text. This script converts pages 1-2 to SVG with
pdftocairo, reads the bounding box of every red ("moved the wrong way") and
blue ("moved the right way") bar, and converts bar heights to repository
counts. Scale: each panel's tallest possible bar spans the axis to the value
printed on that axis (35, 21, 23, 25, 19), so count = height / full height x
axis max. Month alignment is not assumed: the script tries every offset and
keeps the one where all five panels reproduce the page-1 cards at the forced
month 2026-02 (e.g. cyclomatic delta 35 wrong / 0 right), and fails unless
exactly one offset does. The rounding residual is reported so a reader can
see how cleanly the heights map to integers.

Output: data/sweep_monthly.csv, data/sweep_monthly_checks.txt
"""
import csv
import os
import re
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PDF = os.path.join(HERE, "..", "..", "Adoption date sweep.pdf")

RED = "rgb(90.19928%, 40.388489%, 40.388489%)"
BLUE = "rgb(22.349548%, 52.938843%, 89.7995%)"
# Page-1 cards at the forced month 2026-02: (wrong way, right way)
CARDS = {"Cyclomatic delta": (35, 0), "Rework edits": (13, 21), "Follow-ups": (23, 12),
         "Reimplementations": (12, 19), "Repair share": (6, 16)}
# Panel order on the page, left-to-right then top-to-bottom, as printed
PANEL_ORDER = ["Cyclomatic delta", "Rework edits", "Follow-ups", "Reimplementations", "Repair share"]
# Value printed at the top (and mirrored bottom) of each panel's axis
AXIS_MAX = {"Cyclomatic delta": 35, "Rework edits": 21, "Follow-ups": 23, "Reimplementations": 25, "Repair share": 19}


def bars(svg, colour):
    out = []
    for m in re.finditer(r'<path [^>]*fill="%s"[^>]*d="([^"]+)"' % re.escape(colour), svg):
        nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", m.group(1))]
        xs, ys = nums[0::2], nums[1::2]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if 3 < w < 8 and h < 120:  # monthly bars are ~5.6pt wide; skips legend chips and the slider
            out.append(dict(x=(min(xs) + max(xs)) / 2, top=min(ys), bottom=max(ys), h=h))
    return out


def page_svg(p):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "p.svg")
        subprocess.run(["pdftocairo", "-svg", "-f", str(p), "-l", str(p), PDF, f], check=True)
        return open(f).read()


# Pages 1 and 2 are stacked into one coordinate space by offsetting page 2.
allbars = []
for page, offset in ((1, 0), (2, 10000)):
    svg = page_svg(page)
    for colour, kind in ((RED, "wrong"), (BLUE, "right")):
        for b in bars(svg, colour):
            b.update(kind=kind, top=b["top"] + offset, bottom=b["bottom"] + offset, page=page)
            allbars.append(b)

# A panel's bars share a baseline: red bars end on it, blue bars start on it.
def baseline(b):
    return round(b["bottom"] if b["kind"] == "wrong" else b["top"])

groups = {}
for b in allbars:
    key = (baseline(b), b["x"] > 300)  # two columns of panels
    groups.setdefault(key, []).append(b)
# A panel split across the page break is drawn whole on both pages and clipped;
# keep each panel on the page where its baseline falls.
groups = {k: v for k, v in groups.items() if 0 <= k[0] % 10000 <= 842}
panels = sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1]))
checks = [f"panels found: {len(panels)} (expected 5)"]


def month_label(start_y, start_m, i):
    k = start_y * 12 + (start_m - 1) + i
    return f"{k // 12}-{k % 12 + 1:02d}"


series = {}
for name, (key, bs) in zip(PANEL_ORDER, panels):
    xs = sorted({round(b["x"], 1) for b in bs})
    months_x = []  # red and blue bars of one month share x
    for x in xs:
        if not months_x or x - months_x[-1] > 2:
            months_x.append(x)
    per = [{"wrong": 0.0, "right": 0.0} for _ in months_x]
    for b in bs:
        i = min(range(len(months_x)), key=lambda j: abs(months_x[j] - b["x"]))
        per[i][b["kind"]] = b["h"]
    series[name] = per
full = max(h for per in series.values() for m in per for h in m.values())
checks.append(f"full-scale bar height: {full:.2f}pt (shared by all panels)")


def counts(name, i):
    return {k: series[name][i][k] / full * AXIS_MAX[name] for k in ("wrong", "right")}


n = len(series[PANEL_ORDER[0]])
matches = [i for i in range(n)
           if all((round(counts(nm, i)["wrong"]), round(counts(nm, i)["right"])) == CARDS[nm] for nm in PANEL_ORDER)]
checks.append(f"slots per panel: {n}; slot indices reproducing all five 2026-02 cards: {matches}")
if len(matches) != 1:
    raise SystemExit("\n".join(checks) + "\nFAIL: forced-month alignment is not unique")
anchor = matches[0]
k0 = 2026 * 12 + 1 - anchor  # 2026-02 sits at slot `anchor`
start_y, start_m = k0 // 12, k0 % 12 + 1
checks.append(f"OK  alignment: slot {anchor} = 2026-02, so slots run {month_label(start_y, start_m, 0)}..{month_label(start_y, start_m, n - 1)}")

rows = []
for name in PANEL_ORDER:
    worst = 0.0
    for i in range(n):
        c = counts(name, i)
        for kind in ("wrong", "right"):
            rows.append(dict(metric=name, month=month_label(start_y, start_m, i), direction=kind,
                             count=round(c[kind]), raw=round(c[kind], 3)))
            worst = max(worst, abs(c[kind] - round(c[kind])))
    checks.append(f"  {name}: max rounding residual {worst:.3f} repos")

with open(os.path.join(DATA, "sweep_monthly.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["metric", "month", "direction", "count", "raw"])
    w.writeheader()
    w.writerows(rows)
open(os.path.join(DATA, "sweep_monthly_checks.txt"), "w").write("\n".join(checks) + "\n")
print("\n".join(checks))
