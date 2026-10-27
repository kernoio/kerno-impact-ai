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
extract/complexity_monthly.csv recomputed monthly decision-points / 100 lines
extract/complexity_before_after.csv  30-repo before/after + confound flags
extract/window_feasibility.json      4-year trend notes
scripts/                       harness scripts that built the CSVs
REPORT.md                      generated round summary (local paths stripped)
```

## Headline numbers, recomputed from the artefacts

Median of the 30 dated repositories, metric
`complexity.cyclomatic_delta_per_100_production_lines`:

| | Before | After | Relative |
| --- | ---: | ---: | ---: |
| Paper | 5.2 | 8.1 | +51.5% |
| Recomputed | 5.155 | 8.096 | +51.4% |

Rose in 27 of 30; fell in 3 (paper appendix says 27 / 2 — `strapi` is −0.1%
and is the likely rounding difference).

**12 of those 30 before/after rows are marked `confounded` by audit-core
itself**: the pre-adoption slope already predicted most or all of the rise.
The paper's body (p.12) agrees the fair summary is "this is what codebases
did", not "this is what AI did to them".

## Four-year trends

Existing stored series are **not** a 4-year panel. Median coverage is 22
months. A handful of artefacts contain sparse pre-2024 points (`zulip`,
`Ghost`, `wagtail`); they are not complete monthly histories.

A 4-year chart is possible only by **re-running** `kerno audit` (or a
complexity-only walk) on the same public clones with `since ≈ 2022-10`. The
published CLI exposes `--baseline 3|6|12|24` and `--adoption`, not `--since`.
See `extract/window_feasibility.json`.

## License

Measurement outputs are published so the paper can be checked. The underlying
source code remains under each project's own license. Do not treat this
dataset as a grant of rights to those codebases.
