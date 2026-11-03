"""AI-marked vs unmarked commits: do AI commits add more hard-to-test functions (> 10 decision points)?

Same frame as Exhibit 8: codebases with an adoption date, commits after adoption,
AI-marked (exposure high/medium) vs unmarked (unknown), bots excluded (merges kept: squash-merge repos record each PR as a merge on main),
commits with no production lines excluded, >= 20 commits per arm.

Per codebase:
  A. share of commits that add >= 1 function over 10 decision points (complexFunctionDelta > 0)
  B. same, size-matched: Mantel-Haenszel risk ratio within the codebase's size quintiles
  C. hard-to-test functions added per 1,000 production lines (sum delta / sum lines)
  D. same as C, month-matched: only months with >= 5 commits in each arm, months weighted equally
Each is a % difference AI vs unmarked; summarised across codebases (median, bootstrap CI, sign test).
"""
import csv, json, os, sys, statistics as st  # noqa: E401
from collections import defaultdict

AN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AN)
from stats_util import describe  # noqa

RUNS = os.path.join(AN, "raw", "zip", "audit-bench", "runs")
repos = {r["repo"]: r for r in csv.DictReader(open(os.path.join(AN, "data", "repos.csv")))}
MIN = 20


def pct(a, b):
    return None if not b else 100 * (a / b - 1)


rows = []
for name, meta in sorted(repos.items()):
    adopt = meta.get("adoption")
    p = os.path.join(RUNS, name)
    if not adopt or not os.path.exists(os.path.join(p, "complexity.json")):
        continue
    tl = {c["sha"]: c for c in json.load(open(os.path.join(p, "timeline.json")))["commits"]}
    arms = {"ai": [], "un": []}
    for c in json.load(open(os.path.join(p, "complexity.json")))["commits"]:
        t = tl.get(c["sha"])
        if not t or t["isBot"] or not c.get("date") or c["date"][:7] < adopt:
            continue
        if not c.get("productionLinesAdded"):
            continue
        arm = "ai" if c["exposure"] in ("high", "medium") else "un"
        arms[arm].append(c)
    na, nu = len(arms["ai"]), len(arms["un"])
    if na < MIN or nu < MIN:
        continue
    share = {k: sum(c["complexFunctionDelta"] > 0 for c in v) / len(v) for k, v in arms.items()}
    per_k = {k: 1000 * sum(max(c["complexFunctionDelta"], 0) for c in v) / sum(c["productionLinesAdded"] for c in v)
             for k, v in arms.items()}
    lines = {k: st.median(c["productionLinesAdded"] for c in v) for k, v in arms.items()}
    # B. size quintiles over the pooled commits
    allc = sorted(c["productionLinesAdded"] for v in arms.values() for c in v)
    cuts = [allc[int(len(allc) * q / 5)] for q in (1, 2, 3, 4)]
    def q(x):
        return sum(x > k for k in cuts)
    num = den = 0.0
    for s in range(5):
        A = [c for c in arms["ai"] if q(c["productionLinesAdded"]) == s]
        U = [c for c in arms["un"] if q(c["productionLinesAdded"]) == s]
        N = len(A) + len(U)
        if not A or not U:
            continue
        a = sum(c["complexFunctionDelta"] > 0 for c in A)
        u = sum(c["complexFunctionDelta"] > 0 for c in U)
        num += a * len(U) / N
        den += u * len(A) / N
    mh = None if not den else 100 * (num / den - 1)
    # D. month-matched density
    bym = defaultdict(lambda: {"ai": [], "un": []})
    for k, v in arms.items():
        for c in v:
            bym[c["date"][:7]][k].append(c)
    ma, mu = [], []
    for m, d in bym.items():
        if len(d["ai"]) >= 5 and len(d["un"]) >= 5:
            for k, out in (("ai", ma), ("un", mu)):
                out.append(1000 * sum(max(c["complexFunctionDelta"], 0) for c in d[k]) / sum(c["productionLinesAdded"] for c in d[k]))
    mm = pct(st.mean(ma), st.mean(mu)) if ma and st.mean(mu) else None
    rows.append(dict(repo=name, ai_n=na, un_n=nu, ai_med_lines=lines["ai"], un_med_lines=lines["un"],
                     ai_share=share["ai"], un_share=share["un"], share_diff=pct(share["ai"], share["un"]),
                     share_diff_size_matched=mh, ai_per_kloc=per_k["ai"], un_per_kloc=per_k["un"],
                     per_kloc_diff=pct(per_k["ai"], per_k["un"]), months_matched=len(ma), per_kloc_month_matched=mm))

out = os.path.join(AN, "data", "ai_hard_functions.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

print(f"codebases: {len(rows)}  AI-marked commits: {sum(r['ai_n'] for r in rows)}  unmarked: {sum(r['un_n'] for r in rows)}")
print(f"median lines per commit: AI {st.median(r['ai_med_lines'] for r in rows)}  unmarked {st.median(r['un_med_lines'] for r in rows)}")
print(f"median share adding a >10 function: AI {100*st.median(r['ai_share'] for r in rows):.1f}%  unmarked {100*st.median(r['un_share'] for r in rows):.1f}%")
print(f"median >10 functions per 1,000 lines: AI {st.median(r['ai_per_kloc'] for r in rows):.2f}  unmarked {st.median(r['un_per_kloc'] for r in rows):.2f}")
for i, (k, label) in enumerate((("share_diff", "A. share of commits adding a >10 function"),
                                ("share_diff_size_matched", "B. same, size-matched (MH)"),
                                ("per_kloc_diff", "C. >10 functions per 1,000 lines"),
                                ("per_kloc_month_matched", "D. same, month-matched"))):
    d = describe([r[k] for r in rows], seed=9100 + i)
    print(f"{label:45s} n={d['n']:2d} median {d['median']:+.1f}%  95% CI {d['ci_low']:+.1f}% to {d['ci_high']:+.1f}%  "
          f"up/down {d['rose']}/{d['fell']}  sign p={d['sign_p']:.3f}")
