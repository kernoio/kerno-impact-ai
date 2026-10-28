# 4-year complexity re-run

Local walk of the same 46 public repositories, **2022-10-01 to 2026-10-27**.
Finished 2026-10-28T01:20:45Z. 46/46 completed, 0 failed.

## Method

- Plugins: `timeline` + `complexity` only. No judge. No upload.
- Adoption months pinned from the original paper round (`adoption.json` /
  `data/repositories.csv`). Not re-detected on the longer window.
- The published CLI has `--baseline` and `--adoption`, not `--since`. This
  walk set `baselineMonths` so `resolveWindow()` landed on 2022-10-01 while
  keeping the pinned month. Undated repos used `since=2022-10-01`.
- Calendar medians drop months with fewer than 1,000 production lines
  (same rule as the paper's growth-rate months).
- This directory is **aggregates only**. Per-commit JSON and local clones
  are not published.

## Files

| File | Contents |
| --- | --- |
| `calendar_median.csv` | Cross-repo monthly median, n, p25, p75 (2022-10..2026-10) |
| `complexity_monthly.csv` | Per-repo monthly rate (ratio of sums) |
| `paper_comparable_before_after.csv` | Last 12 months before adoption vs after |
| `full_window_before_after.csv` | All in-window months before adoption vs after |
| `calendar_rise_ranks.csv` | Each repo's 2023–2024 typical month vs 2026 |
| `leave_one_out.csv` | Monthly median / slope / 12m B/A with that repo dropped |
| `adoption.json` | Pinned adoption months |
| `summary.json` | Headline numbers from this walk |

## Reading

The original paper's 12-month split still reproduces (median of 30 dated
repos 5.16 → 8.18, median relative +51.3%). The calendar series is
**flat-to-down through 2024**, then rises through 2025–2026 to 10.31 in
October 2026. Leave-one-out: dropping any one repo moves the October 2026
median by at most 0.03. 36 of 39 repos with enough months rose. The late
rise is broad-based, not one repository.
