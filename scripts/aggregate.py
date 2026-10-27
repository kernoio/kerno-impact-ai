#!/usr/bin/env python3
"""Turn a round of `kerno audit` runs into one Markdown report.

Reads only what the audit itself wrote: `runs/<name>/report.json`, its
`timeline.json`, and the harness's `status.jsonl`. It computes no metric of its
own — every number here is a number the audit produced, re-arranged so a round
can be read in one sitting.
"""

import argparse
import json
import re
import statistics
from datetime import datetime
from pathlib import Path

P_SIGNIFICANT = 0.05

# Mirrors `HEADLINE_DIRECTIONS` in `libs/audit-core/src/core/engine.ts`. Kept in
# the same order, because matching is first-wins there too. If a metric is added
# to the audit and not here it reads as ambiguous, which is the same safe default
# the library takes.
DIRECTIONS = [
    (re.compile(r"^cyclomatic delta per commit"), "lower", False),
    (re.compile(r"^cyclomatic delta \(per "), "lower", False),
    (re.compile(r"^production lines added per commit"), "ambiguous", False),
    (re.compile(r"^excess complexity per KLOC"), "lower", False),
    (re.compile(r"^reimplementations\b"), "lower", True),
    (re.compile(r"^rework edits\b"), "lower", False),
    (re.compile(r"^lines rewritten within "), "lower", False),
    (re.compile(r"^follow-ups\b"), "lower", False),
    (re.compile(r"^share of follow-ups that are repairs"), "lower", True),
    (re.compile(r"^days to first follow-up"), "ambiguous", False),
]


def meaning(metric):
    for pattern, direction, judge_dependent in DIRECTIONS:
        if pattern.match(metric):
            return direction, judge_dependent
    return "ambiguous", False


def verdict(row):
    """`headlineVerdict`, in Python: what the row's change means once signed."""
    direction, _ = meaning(row["metric"])
    if direction == "ambiguous":
        return "unclear"
    change = row.get("relative")
    if change is None:
        before, after = row.get("before"), row.get("after")
        change = after - before if before is not None and after is not None else None
    if change is None or change == 0:
        return "unclear"
    rose = change > 0
    return ("better" if rose else "worse") if direction == "higher" else ("worse" if rose else "better")


def withheld_reason(row, spend):
    """Why the audit's own brief would not assert this row, or None if it would.

    Both rules come from `libs/audit-core/src/report.ts`: a judge-dependent row
    on a run that got no verdicts is a count of nothing, and a bootstrap
    interval that includes zero means the sign is not established.
    """
    interval = row.get("interval", "absent")
    if interval != "absent":
        if interval is None:
            return "no interval"
        if interval["low"] <= 0 <= interval["high"]:
            return "CI includes 0"
    _, judge_dependent = meaning(row["metric"])
    judged_nothing = (spend.get("requests") or 0) == 0 and (spend.get("cacheHits") or 0) == 0
    if judge_dependent and judged_nothing and (row.get("judgePending") or float("inf")) > 0:
        return "no judge verdicts"
    return None


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def fmt_pct(value):
    if value is None:
        return "—"
    return f"{value * 100:+.0f}%"


def fmt_num(value):
    if value is None:
        return "—"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.3g}"
    return f"{value:g}"


def fmt_p(value):
    if value is None:
        return "—"
    if value < 0.0001:
        return "<0.0001"
    return f"{value:.4f}"


def fmt_duration(seconds):
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s"


def collect(bench):
    status = {}
    status_file = bench / "status.jsonl"
    if status_file.exists():
        for line in status_file.read_text().splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            status[row["name"]] = row

    runs = []
    for run_dir in sorted((bench / "runs").iterdir()):
        if not run_dir.is_dir():
            continue
        report = load(run_dir / "report.json")
        if report is None:
            continue
        timeline = load(run_dir / "timeline.json") or {}
        runs.append(
            {
                "name": run_dir.name,
                "report": report,
                "adoption": timeline.get("adoption") or {},
                "months": timeline.get("months") or [],
                "commits": len(timeline.get("commits") or []),
                "status": status.get(run_dir.name, {}),
                "dir": run_dir,
            }
        )
    return runs, status


def classify(bench, row):
    """Why a repository produced no report.

    Three of these are the audit declining to measure rather than breaking, and
    a round that files them under "failed" reads as a broken tool. The markers
    are the CLI's own words, taken from the run's log.
    """
    if row.get("stage") == "timeout":
        return "timed out", "harness"
    log = bench / "logs" / f"{row['name']}.log"
    text = log.read_text(errors="replace") if log.exists() else ""
    # The CLI's output is wrapped by ink, so every marker is matched against a
    # whitespace-collapsed copy rather than line by line.
    norm = re.sub(r"\s+", " ", text)
    if "Stopping before the expensive part" in norm:
        match = re.search(r"automatically\.(.*?)Without a month to split on", norm)
        why = match.group(1).strip() if match else "no datable adoption month"
        # The CLI explains itself at length; the first sentence is the fact.
        why = why.split(". ")[0].rstrip(".")
        return f"undatable — {why}", "declined"
    if "No commits on" in norm:
        match = re.search(r"No commits on (\S+) between (\S+) and (\S+)", norm)
        where = f" on {match.group(1)}" if match else ""
        return f"no commits in the window{where}", "declined"
    if "is not a git repository" in norm:
        return "clone unusable", "harness"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    tail = next(
        (line for line in reversed(lines) if not line.startswith(("[", "(node:", "⚠", "✗"))),
        "",
    )
    return (tail[:160] or "no output"), "error"


def judged_state(run):
    """Whether any judged measure in this run actually had a model behind it."""
    spend = run["report"].get("spend") or {}
    requests = spend.get("requests") or 0
    hits = spend.get("cacheHits") or 0
    if requests or hits:
        return "yes"
    for plugin in ("duplication", "complexity", "followups"):
        artefact = load(run["dir"] / f"{plugin}.json")
        if artefact and artefact.get("judged"):
            return "yes"
    return "no"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench", required=True, type=Path)
    args = parser.parse_args()
    bench = args.bench

    runs, status = collect(bench)
    out = []
    w = out.append

    meta_file = bench / "run-meta.txt"
    meta = meta_file.read_text().strip() if meta_file.exists() else ""

    w("# `kerno audit` benchmark round")
    w("")
    w(f"Generated {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}.")
    w("")
    if meta:
        w("```")
        w(meta)
        w("```")
        w("")

    # --- what came back ----------------------------------------------------
    attempted = set(status) | {r["name"] for r in runs}
    ok = [r for r in runs]
    failed = [row for name, row in sorted(status.items()) if row.get("stage") not in ("ok", "skipped")]

    total_audit_s = sum(float(row.get("auditSeconds") or 0) for row in status.values())
    total_clone_s = sum(float(row.get("cloneSeconds") or 0) for row in status.values())
    total_usd = sum((r["report"].get("spend") or {}).get("usd") or 0 for r in runs)
    total_requests = sum((r["report"].get("spend") or {}).get("requests") or 0 for r in runs)
    total_hits = sum((r["report"].get("spend") or {}).get("cacheHits") or 0 for r in runs)

    w("## The round")
    w("")
    w("| | |")
    w("| --- | --- |")
    w(f"| Repositories attempted | {len(attempted)} |")
    w(f"| Reports produced | {len(ok)} |")
    declined_count = sum(1 for row in failed if classify(bench, row)[1] == "declined")
    w(f"| Declined to measure (undatable, or no commits in the window) | {declined_count} |")
    w(f"| Failed or timed out | {len(failed) - declined_count} |")
    w(f"| Audit time (summed, not wall-clock) | {fmt_duration(total_audit_s)} |")
    w(f"| Clone time (summed) | {fmt_duration(total_clone_s)} |")
    w(f"| Judge spend | ${total_usd:.4f} over {total_requests} requests ({total_hits} cache hits) |")
    w("")

    if failed:
        classified = [(row, *classify(bench, row)) for row in failed]
        declined = [item for item in classified if item[2] == "declined"]
        broke = [item for item in classified if item[2] != "declined"]

        if declined:
            w("### Measured nothing, and said why")
            w("")
            w(
                "The audit refusing to split a repository it cannot date is the designed "
                "behaviour, not a failure: without a month to split on every metric would be one "
                "window with nothing to compare it to."
            )
            w("")
            w("| Repository | Reason | Elapsed |")
            w("| --- | --- | ---: |")
            for row, reason, _ in declined:
                w(f"| {row.get('repo', row['name'])} | {reason} | {fmt_duration(row.get('auditSeconds'))} |")
            w("")

        if broke:
            w("### Failed")
            w("")
            w("| Repository | Stage | Exit | What the log says | Elapsed |")
            w("| --- | --- | ---: | --- | ---: |")
            for row, reason, _ in broke:
                w(
                    f"| {row.get('repo', row['name'])} | {row.get('stage')} | {row.get('exit')} | "
                    f"{reason} | {fmt_duration(row.get('auditSeconds'))} |"
                )
            w("")

    # --- adoption dating ---------------------------------------------------
    w("## Adoption dating")
    w("")
    w(
        "The date every before/after rests on. `rule` is how it was dated — a hard threshold "
        "or a sustained step against the repository's own baseline. A blank month is the tool "
        "declining to invent one."
    )
    w("")
    w("| Repository | Commits | AI-attributed | Adoption | Rule | Confidence | Window |")
    w("| --- | ---: | ---: | --- | --- | --- | --- |")
    dated = 0
    for run in sorted(runs, key=lambda r: r["name"]):
        a = run["adoption"]
        window = run["report"].get("window") or {}
        attributed = a.get("attributedCommits")
        scanned = a.get("scannedCommits") or run["commits"]
        share = f"{attributed} ({attributed / scanned * 100:.0f}%)" if attributed and scanned else "—"
        if a.get("month"):
            dated += 1
        w(
            f"| {run['name']} | {scanned or '—'} | {share} | {a.get('month') or '**undated**'} | "
            f"{a.get('rule') or '—'} | {a.get('confidence') or '—'} | "
            f"{window.get('since', '—')} → {window.get('until', '—')} |"
        )
    w("")
    if runs:
        w(f"**{dated} of {len(runs)}** repositories could be dated; the rest ran without a before/after split.")
        w("")

    # --- headline metrics across the set -----------------------------------
    by_metric = {}
    for run in runs:
        spend = run["report"].get("spend") or {}
        for row in run["report"].get("headline") or []:
            by_metric.setdefault(row["metric"], []).append(
                (run["name"], row, withheld_reason(row, spend))
            )

    w("## Headline metrics across the set")
    w("")
    w(
        "One row per metric that reached at least one repository's headline. A row is **asserted** "
        "only where the audit's own brief would assert it — a judge-dependent row on a run with no "
        "verdicts, and a row whose bootstrap interval includes zero, are counted as withheld and "
        "left out of the direction and median columns. *Significant* counts asserted rows with "
        "p < 0.05; rows with no p (ratios of two sums, which no two-sample test takes) are counted "
        "as untested, never as significant."
    )
    w("")
    w("| Metric | Repos | Asserted | Worse | Better | Withheld | Significant | Untested | Median change (asserted) |")
    w("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for metric, rows in sorted(by_metric.items(), key=lambda kv: -len(kv[1])):
        asserted = [row for _, row, reason in rows if reason is None]
        changes = [r["relative"] for r in asserted if r.get("relative") is not None]
        worse = sum(1 for r in asserted if verdict(r) == "worse")
        better = sum(1 for r in asserted if verdict(r) == "better")
        sig = sum(1 for r in asserted if r.get("p") is not None and r["p"] < P_SIGNIFICANT)
        untested = sum(1 for r in asserted if r.get("p") is None)
        median = fmt_pct(statistics.median(changes)) if changes else "—"
        w(
            f"| {metric} | {len(rows)} | {len(asserted)} | {worse} | {better} | "
            f"{len(rows) - len(asserted)} | {sig} | {untested} | {median} |"
        )
    w("")
    w(
        "\"Worse\" and \"better\" are the metric's declared direction applied to the sign of the "
        "change, not a judgement about the repository."
    )
    w("")

    # --- why rows were withheld -------------------------------------------
    reasons = {}
    for metric, rows in by_metric.items():
        for _, _, reason in rows:
            if reason:
                reasons[reason] = reasons.get(reason, 0) + 1
    if reasons:
        w("### Why rows were withheld")
        w("")
        w("| Reason | Rows |")
        w("| --- | ---: |")
        for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
            w(f"| {reason} | {count} |")
        w("")

    # --- per repository ----------------------------------------------------
    w("## Per repository")
    w("")
    for run in sorted(runs, key=lambda r: r["name"]):
        report = run["report"]
        window = report.get("window") or {}
        spend = report.get("spend") or {}
        tele = report.get("telemetry") or {}
        st = run["status"]
        w(f"### {run['name']}")
        w("")
        w(
            f"Adoption **{window.get('adoption') or 'undated'}**, window "
            f"{window.get('since')} → {window.get('until')}, baseline "
            f"{window.get('baselineMonths')} months. "
            f"{run['commits']} commits. "
            f"Ran in {fmt_duration((tele.get('totalMs') or 0) / 1000)}"
            f" (clone {fmt_duration(st.get('cloneSeconds'))}), peak RSS "
            f"{tele.get('peakRssMb', '—')} MB, judge ${spend.get('usd', 0):.4f} "
            f"over {spend.get('requests', 0)} requests. Judged: {judged_state(run)}."
        )
        w("")
        skipped = report.get("skipped") or []
        if skipped:
            names = ", ".join(
                s if isinstance(s, str) else f"{s.get('plugin')} ({s.get('reason')})" for s in skipped
            )
            w(f"Skipped plugins: {names}.")
            w("")
        headline = report.get("headline") or []
        if not headline:
            w("_No metric reached the headline._")
            w("")
            continue
        w("| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |")
        w("| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |")
        for row in headline:
            reason = withheld_reason(row, spend)
            interval = row.get("interval")
            ci = (
                f"{fmt_pct(interval['low'])} … {fmt_pct(interval['high'])}"
                if isinstance(interval, dict)
                else "—"
            )
            w(
                f"| {row['metric']} | {fmt_num(row.get('before'))} | {fmt_num(row.get('after'))} | "
                f"{fmt_pct(row.get('relative'))} | {ci} | {row.get('nBefore', '—')} | "
                f"{row.get('nAfter', '—')} | {fmt_p(row.get('p'))} | "
                f"{'withheld — ' + reason if reason else verdict(row)} |"
            )
        w("")

    print("\n".join(out))


if __name__ == "__main__":
    main()
