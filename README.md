# kerno-impact-ai

Public data behind Kerno's October 2026 paper *The Impact of AI on Code Quality*
(*The Complexity Bill*): 201,576 commits across 46 public open-source
codebases, measured with `kerno audit`.

This repository publishes **aggregates, monthly series, the repo list, and the
analysis scripts**. It does **not** republish per-commit artefacts (author
emails, commit messages, file paths). Those already exist in each project's
public git history; the full local run directory is ~493 MB and can be added
later if needed.

Paper appendix D said "GitHub repository (link to come)". This is that
repository.

## Provenance

| Item | Value |
| --- | --- |
| Measurement tool | `kerno audit` / `@fecore/audit-core` |
| CLI commit on the round | `ce1795a38` |
| Round started | 2026-10-19T12:26:33Z |
| Window claimed in the paper | October 2024 – October 2026 |
| Window actually walked per dated repo | 12 months before that repo's adoption month through mid-October 2026 |
| Repositories attempted | 46 public GitHub projects (see `data/repos.tsv`) |
| Dated (before/after) | 30 |
| Undated (trend / attribution only) | 15 |
| Declined (no commits in window) | 1 (`polonel/trudesk`) |
| Commits in window | 201,576 |
| Judge spend | $1.26 |
| Source tree | local `audit-bench/` harness (not shipped here) |

Every listed repository is a **public** open-source project. No customer or
private repos are in this set.

## What "complexity / 100 lines" is

From `libs/audit-core`:

- A **decision point** is cyclomatic complexity minus 1 per function
  (McCabe base of 1 is stripped so splitting a function is not "added
  complexity").
- Per commit: `(cyclomaticDelta * 100) / productionLinesAdded`.
- Period rate: **sum of decision-point deltas × 100 / sum of production lines
  added** — a ratio of sums, not a median of per-commit ratios.
- Bots, generated files, lockfiles and vendored code are excluded.
- A commit is AI-marked only when an agent identity, `Co-authored-by` line or
  "generated with" note is present. Unmarked commits are `unknown`, not human.

Adoption month: the month AI-marked commits cross 25% and hold, **or** a
sustained step against that repository's own baseline (most of this set used
`step`). `--baseline 12` then sets `since` to the first day of the month 12
months before adoption.

## Files

```
data/repos.tsv                 46 owner/name + star counts used for selection
data/repositories.csv          status, adoption month, rule, commits, AI share
data/headline.csv              before/after rows the audit asserted or withheld
data/metrics.csv               per-metric rollup
data/trends.csv                fitted monthly slopes
data/monthly.json              monthly numerators/denominators by attribution arm
data/4y/                       4-year re-run aggregates (2022-10 to 2026-10)
extract/complexity_monthly.csv original-round monthly decision-points / 100 lines
extract/complexity_before_after.csv  original 30-repo before/after + confound flags
extract/window_feasibility.json      original-round coverage vs completed 4y walk
scripts/                       harness scripts that built the original CSVs
REPORT.md                      generated original-round summary (local paths stripped)
```

## Headline numbers, recomputed from the artefacts

Median of the 30 dated repositories, metric
`complexity.cyclomatic_delta_per_100_production_lines`:

| | Before | After | Relative |
| --- | ---: | ---: | ---: |
| Paper | 5.2 | 8.1 | +51.5% |
| Original artefacts | 5.155 | 8.096 | +51.4% |
| 4-year re-run, last 12 months before vs after | 5.155 | 8.176 | +51.3% |
| 4-year re-run, full in-window before vs after | 4.065 | 8.176 | +76.4% |

The paper's short-window association reproduces. The original artefacts
rose in 27 of 30; the 4-year 12-month split rose in 28 of 30 (plane and
infisical fell). Relative is the median of per-repo relatives.

**12 of those 30 original before/after rows are marked `confounded` by
audit-core itself**: the pre-adoption slope already predicted most or all
of the rise. The paper's body (p.12) agrees the fair summary is "this is
what codebases did", not "this is what AI did to them".

## Four-year re-run (completed 2026-10-28)

Same 46 public repos, calendar window **2022-10-01 → 2026-10-27**,
complexity + timeline only, adoption months pinned, no judge, no upload.
46/46 finished. Aggregates: [`data/4y/`](data/4y/).

**The original paper numbers reproduce** on a 12-month pre-adoption arm
(5.16 → 8.18, +51.3%).

**The 4-year calendar series is flat-then-kink**, not a four-year climb:

| Calendar window | Slope of the monthly-median series |
| --- | ---: |
| 2022-10 to 2023-12 | −0.92%/mo |
| 2022-10 to 2024-09 | −0.26%/mo |
| 2024-10 to 2026-10 (paper dates) | +2.99%/mo |
| 2025-01 to 2026-10 | +3.50%/mo |

October 2022 median 5.70 (n=29). Typical 2023 / 2024 month ≈ 4.7–5.0.
October 2026 median **10.31** (n=36).

**The 2025–2026 rise is broad-based.** Dropping any one repo moves the
October 2026 median by at most 0.03. 36 of 39 repos with enough months
rose from 2023–2024 to 2026. Dropping the three largest calendar risers
(vendure, strapi, directus) only trims October 2026 from 10.31 to 9.73.
See `data/4y/leave_one_out.csv` and `data/4y/calendar_rise_ranks.csv`.

A longer before-arm cannot turn this into a causal claim about AI. It
does show that the paper's 5.2 → 8.1 sits on the late side of a 2025–2026
kink, not on a slope that was already compounding in 2022–2024.

## License

Measurement outputs are published so the paper can be checked. The underlying
source code remains under each project's own license. Do not treat this
dataset as a grant of rights to those codebases.
