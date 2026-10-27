#!/usr/bin/env python3
"""Turn a round of runs into the three CSVs the report page reads.

  repositories.csv  one row per repository the round attempted
  headline.csv      the rows that reached a repository's headline
  metrics.csv       every before/after measurement, headline or not
  trends.csv        every window trend, fitted or declined, and why

Nothing here computes a metric. The audit already did that; this reads its
artefacts and re-shapes them, and re-implements only the gates the library
applies when it decides what a headline may say, so the page can show which
measurements never got that far and why.
"""

import csv
import json
import importlib.util
from pathlib import Path

BENCH = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("agg", BENCH / "aggregate.py")
agg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agg)

# `collectHeadline` in libs/audit-core/src/core/engine.ts.
MIN_EFFECT, MIN_ARM, MIN_EVENTS, MAX_P, MIN_VOLUME = 0.05, 20, 5, 0.05, 0.2

# `trendStatus` in the same file. Four answers, not two: a slope nobody could
# fit and a slope that is flat are different facts about a repository, and
# collapsing them is what made an unmeasured metric read as a steady one.
TREND_MIN_EFFECT, TREND_MAX_P = 0.05, 0.05


def trend_status(row):
    if row.get("slopePerMonth") is None:
        return "unfitted"
    p = row.get("p")
    if p is None or p > TREND_MAX_P:
        return "flat"
    relative = row.get("relativeOverWindow")
    if relative is not None and abs(relative) < TREND_MIN_EFFECT:
        return "flat"
    interval = row.get("interval")
    if not isinstance(interval, dict):
        return "unestablished"
    return "unestablished" if interval["low"] <= 0 <= interval["high"] else "shown"


def gate(row):
    """Which headline gate kept this row out, or None if it got through."""
    if row.get("confounded") is True:
        return "confounded by a pre-existing trend"
    relative = row.get("relative")
    if relative is None:
        p = row.get("p")
        if p is None or p > MAX_P:
            return "no ratio and no significant test"
        if row.get("before") is None or row.get("after") is None:
            return "not measured"
        if row["before"] == row["after"]:
            return "no change"
    elif abs(relative) < MIN_EFFECT:
        return "effect under 5%"
    if (row.get("nBefore") or 0) < MIN_ARM or (row.get("nAfter") or 0) < MIN_ARM:
        return "an arm under 20"
    if row.get("p") is not None and row["p"] > MAX_P:
        return "p above 0.05"
    events = row.get("events")
    if events and max(events["before"], events["after"]) < MIN_EVENTS:
        return "under 5 events"
    volume = row.get("volume")
    if volume:
        larger, smaller = max(volume.values()), min(volume.values())
        if larger > 0 and smaller / larger < MIN_VOLUME:
            return "arms too unbalanced"
    return None


def write_csv(path, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{path.name}: {len(rows)} rows")


def main():
    out = BENCH / "data"
    out.mkdir(exist_ok=True)

    status = {}
    for line in (BENCH / "status.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["stage"] != "skipped" or row["name"] not in status:
            status[row["name"]] = row

    slugs = {}
    for line in (BENCH / "repos.tsv").read_text().splitlines():
        slug, size = line.split("\t")
        slugs[slug.split("/")[1]] = (slug, int(size))

    repos, headline, metrics, trends = [], [], [], []
    for name, st in status.items():
        slug, size = slugs.get(name, (name, 0))
        run = BENCH / "runs" / name
        report_file = run / "report.json"

        if not report_file.exists():
            reason, kind = agg.classify(BENCH, st)
            repos.append(
                dict(
                    repo=slug, name=name,
                    status="declined" if kind == "declined" else "failed",
                    reason=reason, size_mb=round(size / 1024, 1),
                    commits="", ai_commits="", ai_share="", adoption="", rule="",
                    since="", until="",
                    audit_minutes=round(st.get("auditSeconds", 0) / 60, 1),
                    clone_seconds=st.get("cloneSeconds", 0), peak_rss_mb="",
                    judge_usd=0, judge_requests=0, judge_cache_hits=0,
                    judge_failures=0, headline_rows=0,
                    trends_shown=0, trends_total=0,
                    authors="", authors_attributed="",
                )
            )
            continue

        report = json.loads(report_file.read_text())
        telemetry = report.get("telemetry") or {}
        spend = report.get("spend") or {}
        timeline = json.loads((run / "timeline.json").read_text())
        adoption = timeline.get("adoption") or {}
        scanned = adoption.get("scannedCommits") or len(timeline.get("commits") or [])
        attributed = adoption.get("attributedCommits") or 0

        all_trends = report.get("trends") or []
        shown = [t for t in all_trends if trend_status(t) == "shown"]
        authors = [a for a in (timeline.get("authors") or []) if not a.get("bot")]
        dated = bool(report["window"].get("adoption"))

        repos.append(
            dict(
                repo=slug, name=name,
                # A repository that could not be dated is measured now; it
                # simply has no before/after. Calling it "declined", as this
                # round's first pass had to, would hide fifteen reports.
                status="measured" if dated else "undated",
                reason="" if dated else "no adoption month could be dated",
                size_mb=round(size / 1024, 1), commits=scanned,
                ai_commits=attributed,
                ai_share=round(attributed / scanned, 4) if scanned else "",
                adoption=report["window"].get("adoption") or "",
                rule=adoption.get("rule") or "",
                since=report["window"]["since"], until=report["window"]["until"],
                audit_minutes=round((telemetry.get("totalMs") or 0) / 60000, 1),
                clone_seconds=st.get("cloneSeconds", 0),
                peak_rss_mb=telemetry.get("peakRssMb") or "",
                judge_usd=round(spend.get("usd") or 0, 4),
                judge_requests=spend.get("requests") or 0,
                judge_cache_hits=spend.get("cacheHits") or 0,
                judge_failures=spend.get("failures") or 0,
                headline_rows=len(report.get("headline") or []),
                trends_shown=len(shown), trends_total=len(all_trends),
                authors=len(authors),
                authors_attributed=sum(1 for a in authors if a.get("attributed")),
            )
        )

        for row in all_trends:
            interval = row.get("interval")
            trends.append(
                dict(
                    repo=name, metric=row["metric"],
                    direction=agg.meaning(row["metric"])[0],
                    status=trend_status(row),
                    months=row.get("months"), n=row.get("n"),
                    start=row.get("from") or "", end=row.get("to") or "",
                    slope_per_month=row.get("slopePerMonth"),
                    fitted_start=row.get("fittedStart"),
                    fitted_end=row.get("fittedEnd"),
                    relative=row.get("relativeOverWindow"),
                    p=row.get("p") if row.get("p") is not None else "",
                    ci_low=interval["low"] if isinstance(interval, dict) else "",
                    ci_high=interval["high"] if isinstance(interval, dict) else "",
                )
            )

        def shape(row, status_, reason):
            interval = row.get("interval")
            return dict(
                repo=name, metric=row["metric"],
                direction=agg.meaning(row["metric"])[0],
                before=row.get("before"), after=row.get("after"),
                relative=row.get("relative"),
                ci_low=interval["low"] if isinstance(interval, dict) else "",
                ci_high=interval["high"] if isinstance(interval, dict) else "",
                n_before=row.get("nBefore"), n_after=row.get("nAfter"),
                p=row.get("p") if row.get("p") is not None else "",
                status=status_, reason=reason,
                verdict="" if reason else agg.verdict(row),
            )

        for row in report.get("headline") or []:
            withheld = agg.withheld_reason(row, spend)
            entry = shape(row, "withheld" if withheld else "asserted", withheld or "")
            entry.pop("direction")
            entry["withheld_reason"] = withheld or ""
            headline.append(entry)

        for artefact in sorted(run.glob("*.json")):
            if artefact.stem in ("report", "config", "telemetry"):
                continue
            for row in json.loads(artefact.read_text()).get("beforeAfter") or []:
                excluded = gate(row)
                withheld = None if excluded else agg.withheld_reason(row, spend)
                entry = shape(
                    row,
                    "excluded" if excluded else ("withheld" if withheld else "asserted"),
                    excluded or withheld or "",
                )
                entry["plugin"] = artefact.stem
                entry["caveats"] = len(row.get("caveats") or [])
                metrics.append(entry)

    order = {"measured": 0, "undated": 1}
    repos.sort(key=lambda r: (order.get(r["status"], 2), r["name"]))
    write_csv(out / "repositories.csv", repos)
    write_csv(out / "headline.csv", headline)
    write_csv(out / "metrics.csv", metrics)
    write_csv(out / "trends.csv", trends)


if __name__ == "__main__":
    main()
