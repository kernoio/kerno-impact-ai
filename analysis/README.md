# Analysis scripts

The statistics behind every number in *The Impact of AI on Code Quality* (2026). Each script reads the `kerno audit` benchmark output and writes its results to `analysis/data/`.

| Scripts | What they compute |
| --- | --- |
| `01_extract.py`, `02_sweep_bars.py` | Parse the benchmark summary and the adoption-date sweep |
| `03_analysis.py` | Before/after medians, bootstrap ranges and sign tests per metric |
| `04_forecast.py` | 12- and 24-month complexity projections |
| `05_charts.py`, `06_numbers.py` | Chart data and the full list of numbers used in the report (`data/numbers.json`) |
| `10_raw_verify.py` to `24_volumes.py` | Per-commit analyses: follow-ups, bug fixes, maintainability grades, monthly growth, output per engineer, tool and model comparisons |
| `25_ai_hard_functions.py` | AI-marked vs unmarked commits adding functions over 10 decision points, including the size-matched comparison |
| `26_censoring_panel.py` | Recent-commit check for the 90-day measures and the fixed-set growth check |
| `stats_util.py` | Shared median, bootstrap and sign-test helpers |

The per-commit benchmark output (about 490 MB, under `raw/`) is not included, in line with the policy in the top-level README. Scripts that need it expect it at `analysis/raw/`. The 100-commit hand-labelled sample used to check commit-type accuracy is also left out because it contains commit messages.
