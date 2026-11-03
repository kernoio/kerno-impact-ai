"""Check the PDF-derived tables (01_extract.py) against the raw benchmark data.

The raw zip (kerno-audit-benchmark-2026-10.zip, extracted to raw/zip/) is the
source of truth. This script compares every repository, before/after row and
trend row we read out of the PDFs with the flattened tables the audit's own
build-data.py produced from runs/, and reports any difference.

Output: data/raw_verify.txt
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(HERE, "raw", "zip", "audit-bench", "data")


def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def f(x):
    return None if x in ("", "None", None) else float(x)


out = []
pdf_repos = {r["repo"]: r for r in load(os.path.join(DATA, "repos.csv"))}
raw_repos = {r["name"]: r for r in load(os.path.join(RAW, "repositories.csv"))}
out.append(f"repositories: pdf={len(pdf_repos)} raw={len(raw_repos)}")
bad = 0
for name, r in raw_repos.items():
    p = pdf_repos.get(name)
    if not p:
        out.append(f"  MISSING in pdf extract: {name}")
        bad += 1
        continue
    if r["status"] == "failed" or p["status"] == "declined":
        continue
    checks = [("commits", int(r["commits"]), int(p["commits"])),
              ("ai_share_pct", round(float(r["ai_share"]) * 100, 1), float(p["ai_share_pct"])),
              ("adoption", r["adoption"] or None, p["adoption"] or None),
              ("authors", int(r["authors"]), int(p["authors"]))]
    for k, a, b in checks:
        if a != b:
            out.append(f"  DIFF {name}.{k}: raw={a} pdf={b}")
            bad += 1
out.append(f"  repo-level differences: {bad}")

pdf_ba = {(r["repo"], r["metric"]): r for r in load(os.path.join(DATA, "before_after.csv"))}
raw_ba = {(r["repo"], r["metric"]): r for r in load(os.path.join(RAW, "metrics.csv"))}
out.append(f"before/after rows: pdf={len(pdf_ba)} raw={len(raw_ba)}")
bad = 0
for k, r in raw_ba.items():
    p = pdf_ba.get(k)
    if not p:
        out.append(f"  MISSING in pdf extract: {k}")
        bad += 1
        continue
    rel = f(r["relative"])
    pct = None if rel is None else round(rel * 100)
    pc = f(p["change_pct"])
    if (pct is None) != (pc is None) or (pct is not None and abs(pct - pc) > 1):
        out.append(f"  DIFF change {k}: raw={pct} pdf={pc}")
        bad += 1
    if r["status"] != p["status"]:
        out.append(f"  DIFF status {k}: raw={r['status']} pdf={p['status']}")
        bad += 1
    if int(r["n_before"] or 0) != int(p["n_before"]) or int(r["n_after"] or 0) != int(p["n_after"]):
        out.append(f"  DIFF n {k}: raw={r['n_before']}/{r['n_after']} pdf={p['n_before']}/{p['n_after']}")
        bad += 1
out.append(f"  before/after differences: {bad}")

pdf_tr = {(r["repo"], r["metric"]): r for r in load(os.path.join(DATA, "trends.csv"))}
raw_tr = load(os.path.join(RAW, "trends.csv"))
out.append(f"trend rows: pdf={len(pdf_tr)} raw={len(raw_tr)}")
bad = 0
for r in raw_tr:
    m = r["metric"].replace("follow-ups per change", "follow-ups (per change)")
    p = pdf_tr.get((r["repo"], m))
    if not p:
        out.append(f"  unmatched raw trend: {r['repo']} / {r['metric']}")
        bad += 1
        continue
    if r["status"] != p["status"]:
        out.append(f"  DIFF status {r['repo']}/{m}: raw={r['status']} pdf={p['status']}")
        bad += 1
    rs, ps = f(r["slope_per_month"]), f(p["slope_per_month"])
    if rs is not None and ps is not None and abs(rs - ps) > max(0.01 * abs(rs), 0.0006):
        out.append(f"  DIFF slope {r['repo']}/{m}: raw={rs:.5g} pdf={ps:.5g}")
        bad += 1
out.append(f"  trend differences: {bad}")
open(os.path.join(DATA, "raw_verify.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
