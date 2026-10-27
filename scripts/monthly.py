#!/usr/bin/env python3
"""
Monthly aggregates for every rate metric, so a before/after split can be
recomputed at any adoption month without touching git.

`periodOf` is a string comparison — `commit.date[:7] < adoptionMonth` — and
nothing upstream of it reads the adoption date. Every per-commit measurement
in the artefacts was therefore taken identically regardless of where the
boundary sat, and a rate metric is a sum of numerators over a sum of
denominators. Bucket both by month and any month boundary can be re-split
exactly, by anyone, in a browser.

Only the five *rate* metrics are emitted. The median-valued rows (cyclomatic
delta per commit, lines added per commit, days to first follow-up) cannot be
recombined from monthly medians and are deliberately left out rather than
approximated. Line survival is left out for a different reason: its sample is
drawn per period, so moving the boundary would require re-running blame.

    python3 monthly.py            # writes data/monthly.json
"""
import json
import os
import sys
from collections import defaultdict

BENCH = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(BENCH, "runs")
OUT = os.path.join(BENCH, "data", "monthly.json")

# Mirrors HEADLINE_DIRECTIONS in core/engine.ts. A metric absent from that
# table is reported with no direction; none of these five are.
METRICS = [
    {
        "key": "complexity",
        "label": "cyclomatic delta (per 100 production lines added)",
        "short": "Cyclomatic delta",
        "per": "100 production lines added",
        "direction": "lower",
        "judged": False,
    },
    {
        "key": "rework",
        "label": "rework edits (per 100 lines added)",
        "short": "Rework edits",
        "per": "100 lines added",
        "direction": "lower",
        "judged": False,
    },
    {
        "key": "followups",
        "label": "follow-ups (per change)",
        "short": "Follow-ups",
        "per": "change",
        "direction": "lower",
        "judged": False,
    },
    {
        "key": "duplication",
        "label": "reimplementations (per KLOC added)",
        "short": "Reimplementations",
        "per": "KLOC added",
        "direction": "lower",
        "judged": True,
    },
    {
        "key": "repair",
        "label": "share of follow-ups that are repairs",
        "short": "Repair share",
        "per": "judged follow-up",
        "direction": "lower",
        "judged": True,
    },
]


def load(run_dir, name):
    path = os.path.join(run_dir, name + ".json")
    if not os.path.isfile(path):
        return None
    with open(path) as handle:
        return json.load(handle)


def month_of(iso):
    return iso[:7]


def churn_subjects(timeline):
    """Copied from the churn plugin: bots and non-production commits are out."""
    return [
        c
        for c in timeline["commits"]
        if not c.get("isBot") and len(c.get("productionFiles") or []) > 0
    ]


def duplication_subjects(timeline):
    """The duplication plugin drops docs changes on top of churn's filter."""
    return [
        c
        for c in timeline["commits"]
        if not c.get("isBot")
        and len(c.get("productionFiles") or []) > 0
        and c.get("changeKind") != "docs"
    ]


# Arm slots inside a month's row, in the order they are written out.
# `compareArmRatesWithin` splits on exposure 'high' against 'unknown' and drops
# 'medium' from both arms: a generated-with marker in a commit body is weaker
# evidence than an agent identity, and putting it in either arm would blur the
# contrast the row exists to draw. It is carried here so the date split can
# still count it, and so the page can show how much of the history it is.
ARMS = ("high", "medium", "unknown")


def arm_of(exposure):
    return exposure if exposure in ARMS else "unknown"


def bucket(points):
    """[(month, arm, numerator, denominator)] -> {month: [n,d,c] * 3 arms}."""
    out = defaultdict(lambda: [0.0, 0.0, 0, 0.0, 0.0, 0, 0.0, 0.0, 0])
    for month, arm, num, den in points:
        base = ARMS.index(arm) * 3
        row = out[month]
        row[base] += num
        row[base + 1] += den
        row[base + 2] += 1
    return out


def followup_counts(followups):
    """Qualifying follow-ups per originating commit.

    A hot file, a sweep and a revert are each one decision recorded many
    times; the plugins exclude all three before counting, and a denominator
    assembled any other way would not reproduce the run.
    """
    counts = defaultdict(int)
    for f in followups:
        if f.get("isHotFile") or f.get("isSweep") or f.get("isRevert"):
            continue
        counts[f["originSha"]] += 1
    return counts


def series_for(run):
    timeline = run["timeline"]
    out = {}

    if run.get("complexity"):
        written = [
            c
            for c in run["complexity"]["commits"]
            if (c.get("productionLinesAdded") or 0) > 0 and (c.get("filesRead") or 0) > 0
        ]
        out["complexity"] = bucket(
            (
                month_of(c["date"]),
                arm_of(c.get("exposure")),
                c["cyclomaticDelta"] * 100,
                c["productionLinesAdded"],
            )
            for c in written
        )

    if run.get("followups"):
        counts = followup_counts(run["followups"]["followups"])
        subjects = churn_subjects(timeline)
        # Rework and follow-ups are counted against the commit that ORIGINATED
        # the work, so the arm is that commit's own attribution — the question
        # is whether code written with an agent gets revisited more, not who
        # did the revisiting.
        out["rework"] = bucket(
            (
                month_of(c["date"]),
                arm_of(c.get("exposure")),
                counts.get(c["sha"], 0),
                max(1, c.get("insertions") or 0) / 100,
            )
            for c in subjects
        )
        out["followups"] = bucket(
            (
                month_of(c["date"]),
                arm_of(c.get("exposure")),
                counts.get(c["sha"], 0),
                1,
            )
            for c in subjects
        )

        # Repair share buckets on the follow-up's own date, and arms on the
        # ORIGIN's attribution for the same reason: "was agent-written code
        # repaired more often" is the question, not "did agents do the repairs".
        repair = defaultdict(lambda: [0.0, 0.0, 0] * 3)
        for f in run["followups"]["followups"]:
            if f.get("judgement") is None or f.get("isRevert") or f.get("isSweep"):
                continue
            base = ARMS.index(arm_of(f.get("originExposure"))) * 3
            row = repair[month_of(f["date"])]
            row[base + 1] += 1
            row[base + 2] += 1
            if f["judgement"].get("verdict") == "repair":
                row[base] += 1
        if repair:
            out["repair"] = repair

    if run.get("duplication"):
        by_commit = defaultdict(float)
        for pair in run["duplication"]["pairs"]:
            if pair.get("benign") is not None:
                continue
            by_commit[pair["sha"]] += pair.get("confirmedProbability") or 0
        out["duplication"] = bucket(
            (
                month_of(c["date"]),
                arm_of(c.get("exposure")),
                by_commit.get(c["sha"], 0.0),
                max(1, c.get("insertions") or 0) / 1000,
            )
            for c in duplication_subjects(timeline)
        )

    return out


def main():
    names = sorted(
        entry
        for entry in os.listdir(RUNS)
        if os.path.isdir(os.path.join(RUNS, entry))
    )

    repos = []
    for name in names:
        run_dir = os.path.join(RUNS, name)
        run = {part: load(run_dir, part) for part in
               ("config", "timeline", "complexity", "followups", "duplication")}
        if not run["timeline"] or not run["config"]:
            print("  skip %-16s no timeline" % name, file=sys.stderr)
            continue

        commits = run["timeline"]["commits"]
        # [all, high, medium] per month: the page shows how thin the attributed
        # arm is, which is the first thing to know before reading a row drawn
        # from it.
        activity = defaultdict(lambda: [0, 0, 0])
        for c in commits:
            row = activity[month_of(c["date"])]
            row[0] += 1
            if c.get("exposure") == "high":
                row[1] += 1
            elif c.get("exposure") == "medium":
                row[2] += 1

        series = series_for(run)
        months = sorted(
            set(activity)
            | {m for table in series.values() for m in table}
        )

        attributed = sum(row[1] + row[2] for row in activity.values())
        strong = sum(row[1] for row in activity.values())
        repos.append(
            {
                "name": name,
                "adoption": run["config"].get("adoptionMonth"),
                "since": run["config"].get("since"),
                "until": run["config"].get("until"),
                "commits": len(commits),
                "attributed": attributed,
                "strong": strong,
                "aiShare": round(attributed / len(commits), 4) if commits else 0,
                "months": months,
                # Parallel arrays indexed by `months`, which keeps the payload
                # small enough to ship to a browser whole.
                "activity": [activity.get(m, [0, 0, 0]) for m in months],
                # Nine numbers a month: numerator, denominator and count for
                # each of high / medium / unknown, in that order.
                "series": {
                    key: [
                        [
                            round(v, 6) if i % 3 != 2 else v
                            for i, v in enumerate(table[m])
                        ]
                        if m in table
                        else None
                        for m in months
                    ]
                    for key, table in series.items()
                },
            }
        )
        print(
            "  %-16s %3d months  %s"
            % (name, len(months), ", ".join(sorted(series))),
            file=sys.stderr,
        )

    payload = {"metrics": METRICS, "repos": repos}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as handle:
        json.dump(payload, handle, separators=(",", ":"))

    print(
        "\n%d repositories -> %s (%.0f KB)"
        % (len(repos), OUT, os.path.getsize(OUT) / 1024),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
