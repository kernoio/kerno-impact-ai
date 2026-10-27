# `kerno audit` benchmark round

Generated 2026-10-19 15:23 CEST.

```
started      2026-10-19T12:26:33Z
cli          kerno-cli (local build)
cli version  0.0.1
commit       ce1795a38
repositories 16
parallel     3
timeout      150m
```

## The round

| | |
| --- | --- |
| Repositories attempted | 46 |
| Reports produced | 45 |
| Declined to measure (undatable, or no commits in the window) | 1 |
| Failed or timed out | 0 |
| Audit time (summed, not wall-clock) | 12h46m |
| Clone time (summed) | 14m19s |
| Judge spend | $1.2575 over 26767 requests (10146 cache hits) |

### Measured nothing, and said why

The audit refusing to split a repository it cannot date is the designed behaviour, not a failure: without a month to split on every metric would be one window with nothing to compare it to.

| Repository | Reason | Elapsed |
| --- | --- | ---: |
| polonel/trudesk | no commits in the window on master | 0m10s |

## Adoption dating

The date every before/after rests on. `rule` is how it was dated — a hard threshold or a sustained step against the repository's own baseline. A blank month is the tool declining to invent one.

| Repository | Commits | AI-attributed | Adoption | Rule | Confidence | Window |
| --- | ---: | ---: | --- | --- | --- | --- |
| Ghost | 9215 | 51 (1%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| activepieces | 6011 | 395 (7%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |
| actual | 2375 | 366 (15%) | 2025-12 | step | strong | 2024-12-01 → 2026-10-18 |
| amplication | 80 | — | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| appsmith | 1216 | 144 (12%) | 2026-02 | threshold | strong | 2025-02-01 → 2026-10-18 |
| appwrite | 1230 | 34 (3%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| baserow | 2067 | 12 (1%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| budibase | 2895 | 12 (0%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| cal.com | 6533 | 996 (15%) | 2025-04 | step | strong | 2024-06-01 → 2026-10-18 |
| directus | 1373 | 64 (5%) | 2025-11 | step | strong | 2024-11-01 → 2026-10-18 |
| django-cms | 483 | 12 (2%) | 2025-08 | step | strong | 2024-08-01 → 2026-10-18 |
| erpnext | 5647 | 38 (1%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| erxes | 2132 | 12 (1%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| evershop | 267 | 1 (0%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| flagsmith | 2157 | 144 (7%) | 2025-11 | step | strong | 2024-11-01 → 2026-10-18 |
| focalboard | 3 | — | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| formbricks | 2406 | 529 (22%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |
| grafana | 17903 | 1225 (7%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |
| hoppscotch | 755 | 19 (3%) | 2025-08 | step | strong | 2024-08-01 → 2026-10-18 |
| infisical | 3002 | 76 (3%) | 2026-08 | step | strong | 2025-08-01 → 2026-10-18 |
| jitsi-meet | 1814 | 12 (1%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| keep | 1882 | 34 (2%) | 2025-06 | step | strong | 2024-06-01 → 2026-10-18 |
| lightdash | 15906 | 2702 (17%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |
| mattermost | 4936 | 944 (19%) | 2025-05 | step | strong | 2024-06-01 → 2026-10-18 |
| medusa | 4112 | 54 (1%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| n8n | 12999 | 3279 (25%) | 2026-01 | step | strong | 2025-01-01 → 2026-10-18 |
| nango | 4073 | 327 (8%) | 2026-03 | step | strong | 2025-03-01 → 2026-10-18 |
| nocodb | 2778 | — | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| novu | 5475 | 1280 (23%) | 2025-05 | step | strong | 2024-06-01 → 2026-10-18 |
| outline | 3404 | 525 (15%) | 2025-12 | step | strong | 2024-12-01 → 2026-10-18 |
| payload | 2603 | 109 (4%) | 2026-06 | step | strong | 2025-06-01 → 2026-10-18 |
| peppermint | 22 | — | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| plane | 1624 | 74 (5%) | 2026-03 | step | strong | 2025-03-01 → 2026-10-18 |
| prefect | 4441 | 1920 (43%) | 2025-10 | threshold | strong | 2024-10-01 → 2026-10-18 |
| rallly | 2221 | 957 (43%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |
| redash | 161 | 26 (16%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |
| sentry | 35187 | 3731 (11%) | 2026-01 | step | strong | 2025-01-01 → 2026-10-18 |
| strapi | 1325 | 144 (11%) | 2026-05 | step | strong | 2025-05-01 → 2026-10-18 |
| twenty | 11790 | 381 (3%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |
| typebot.io | 929 | 48 (5%) | 2026-04 | threshold | strong | 2025-04-01 → 2026-10-18 |
| unleash | 2879 | 122 (4%) | 2026-06 | step | strong | 2025-06-01 → 2026-10-18 |
| vendure | 1030 | 19 (2%) | 2026-08 | step | strong | 2025-08-01 → 2026-10-18 |
| wagtail | 2744 | 13 (0%) | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| wiki | 260 | — | **undated** | — | none | 2024-10-19 → 2026-10-19 |
| zulip | 9231 | 921 (10%) | 2026-02 | step | strong | 2025-02-01 → 2026-10-18 |

**30 of 45** repositories could be dated; the rest ran without a before/after split.

## Headline metrics across the set

One row per metric that reached at least one repository's headline. A row is **asserted** only where the audit's own brief would assert it — a judge-dependent row on a run with no verdicts, and a row whose bootstrap interval includes zero, are counted as withheld and left out of the direction and median columns. *Significant* counts asserted rows with p < 0.05; rows with no p (ratios of two sums, which no two-sample test takes) are counted as untested, never as significant.

| Metric | Repos | Asserted | Worse | Better | Withheld | Significant | Untested | Median change (asserted) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| lines rewritten within 90 days | 28 | 18 | 1 | 17 | 10 | 0 | 18 | -34% |
| lines rewritten within 30 days | 25 | 11 | 0 | 11 | 14 | 0 | 11 | -34% |
| reimplementations (per KLOC added) | 23 | 23 | 5 | 18 | 0 | 0 | 23 | -34% |
| production lines added per commit | 22 | 22 | 0 | 0 | 0 | 22 | 0 | +95% |
| share of follow-ups that are repairs | 21 | 21 | 5 | 16 | 0 | 0 | 21 | -22% |
| cyclomatic delta (per 100 production lines added) | 15 | 15 | 15 | 0 | 0 | 0 | 15 | +56% |
| follow-ups (per change) | 10 | 10 | 10 | 0 | 0 | 0 | 10 | +132% |
| days to first follow-up | 3 | 3 | 0 | 0 | 0 | 3 | 0 | -38% |
| rework edits (per 100 lines added) | 2 | 2 | 2 | 0 | 0 | 0 | 2 | +94% |

"Worse" and "better" are the metric's declared direction applied to the sign of the change, not a judgement about the repository.

### Why rows were withheld

| Reason | Rows |
| --- | ---: |
| CI includes 0 | 22 |
| no interval | 2 |

## Per repository

### Ghost

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 9215 commits. Ran in 18m23s (clone 0m02s), peak RSS 560 MB, judge $0.0465 over 946 requests. Judged: yes.

_No metric reached the headline._

### activepieces

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 6011 commits. Ran in 30m33s (clone 0m44s), peak RSS 706 MB, judge $0.0396 over 1087 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.22 | 0.157 | -28% | -44% … -9% | 46763 | 49314 | — | better |
| production lines added per commit | 28 | 77 | +175% | — | 2276 | 2229 | <0.0001 | unclear |
| follow-ups (per change) | 0.295 | 1.27 | +329% | — | 2317 | 2249 | — | worse |
| reimplementations (per KLOC added) | 0.104 | 0.147 | +42% | — | 2311 | 2230 | — | worse |
| cyclomatic delta (per 100 production lines added) | 7.05 | 8.64 | +23% | — | 2276 | 2229 | — | worse |

### actual

Adoption **2025-12**, window 2024-12-01 → 2026-10-18, baseline 12 months. 2375 commits. Ran in 7m37s (clone 0m23s), peak RSS 422 MB, judge $0.0182 over 267 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 30 days | 0.0799 | 0.0524 | -34% | -55% … -4% | 31767 | 30449 | — | better |
| lines rewritten within 90 days | 0.144 | 0.0967 | -33% | -49% … -12% | 31767 | 30449 | — | better |
| production lines added per commit | 20 | 28 | +40% | — | 846 | 920 | 0.0043 | unclear |
| cyclomatic delta (per 100 production lines added) | 4.8 | 8.27 | +72% | — | 846 | 920 | — | worse |
| share of follow-ups that are repairs | 0.12 | 0.0909 | -24% | — | 50 | 66 | — | better |

### amplication

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 80 commits. Ran in 1m17s (clone 0m01s), peak RSS 516 MB, judge $0.0003 over 8 requests. Judged: yes.

_No metric reached the headline._

### appsmith

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 1216 commits. Ran in 8m39s (clone 0m35s), peak RSS 533 MB, judge $0.0132 over 216 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 30 days | 0.0978 | 0.0237 | -76% | -96% … -31% | 25984 | 12123 | — | better |
| lines rewritten within 90 days | 0.132 | 0.0363 | -72% | -90% … -43% | 25984 | 12123 | — | better |
| production lines added per commit | 27 | 44 | +63% | — | 609 | 206 | <0.0001 | unclear |
| share of follow-ups that are repairs | 0.294 | 0.571 | +94% | — | 85 | 28 | — | worse |
| reimplementations (per KLOC added) | 0.223 | 0.0522 | -77% | — | 631 | 211 | — | better |

### appwrite

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 1230 commits. Ran in 8m10s (clone 0m03s), peak RSS 963 MB, judge $0.0001 over 3 requests. Judged: yes.

_No metric reached the headline._

### baserow

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 2067 commits. Ran in 10m00s (clone 0m05s), peak RSS 703 MB, judge $0.0003 over 7 requests. Judged: yes.

_No metric reached the headline._

### budibase

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 2895 commits. Ran in 6m45s (clone 0m02s), peak RSS 580 MB, judge $0.0084 over 228 requests. Judged: yes.

_No metric reached the headline._

### cal.com

Adoption **2025-06**, window 2024-06-01 → 2026-10-18, baseline 12 months. 6533 commits. Ran in 25m53s (clone 0m40s), peak RSS 810 MB, judge $0.0517 over 1064 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.214 | 0.286 | +34% | +6% … +67% | 34905 | 35314 | — | worse |
| reimplementations (per KLOC added) | 0.265 | 0.198 | -25% | — | 2527 | 2514 | — | better |
| share of follow-ups that are repairs | 0.125 | 0.0976 | -22% | — | 32 | 82 | — | better |
| follow-ups (per change) | 0.874 | 0.949 | +9% | — | 2546 | 2528 | — | worse |
| lines rewritten within 30 days | 0.128 | 0.137 | +7% | -23% … +50% | 34905 | 35314 | — | withheld — CI includes 0 |

### directus

Adoption **2025-11**, window 2024-11-01 → 2026-10-18, baseline 12 months. 1373 commits. Ran in 2m41s (clone 0m23s), peak RSS 449 MB, judge $0.0078 over 122 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 16 | 23 | +44% | — | 304 | 381 | 0.0063 | unclear |
| cyclomatic delta (per 100 production lines added) | 6.88 | 13.2 | +92% | — | 304 | 381 | — | worse |
| share of follow-ups that are repairs | 0.522 | 0.161 | -69% | — | 23 | 93 | — | better |
| reimplementations (per KLOC added) | 0.0853 | 0.0323 | -62% | — | 307 | 384 | — | better |
| lines rewritten within 30 days | 0.0364 | 0.0446 | +23% | -58% … +237% | 9238 | 15586 | — | withheld — CI includes 0 |
| lines rewritten within 90 days | 0.0626 | 0.073 | +17% | -42% … +120% | 9238 | 15586 | — | withheld — CI includes 0 |

### django-cms

Adoption **2025-08**, window 2024-08-01 → 2026-10-18, baseline 12 months. 483 commits. Ran in 1m33s (clone 0m07s), peak RSS 223 MB, judge $0.0027 over 42 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| cyclomatic delta (per 100 production lines added) | 2.16 | 4.37 | +103% | — | 99 | 180 | — | worse |
| lines rewritten within 90 days | 0.0838 | 0.0425 | -49% | -77% … +1% | 3711 | 6207 | — | withheld — CI includes 0 |
| lines rewritten within 30 days | 0.0377 | 0.0193 | -49% | -79% … +21% | 3711 | 6207 | — | withheld — CI includes 0 |

### erpnext

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 5647 commits. Ran in 28m25s (clone 0m05s), peak RSS 1353 MB, judge $0.0410 over 988 requests. Judged: yes.

_No metric reached the headline._

### erxes

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 2132 commits. Ran in 17m57s (clone 0m02s), peak RSS 748 MB, judge $0.0419 over 827 requests. Judged: yes.

_No metric reached the headline._

### evershop

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 267 commits. Ran in 1m53s (clone 0m01s), peak RSS 533 MB, judge $0.0036 over 91 requests. Judged: yes.

_No metric reached the headline._

### flagsmith

Adoption **2025-11**, window 2024-11-01 → 2026-10-18, baseline 12 months. 2157 commits. Ran in 5m01s (clone 0m15s), peak RSS 485 MB, judge $0.0103 over 123 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 18 | 39 | +117% | — | 430 | 726 | <0.0001 | unclear |
| reimplementations (per KLOC added) | 0.144 | 0.0902 | -37% | — | 423 | 724 | — | better |
| lines rewritten within 30 days | 0.0835 | 0.0919 | +10% | -23% … +59% | 21696 | 40051 | — | withheld — CI includes 0 |

### focalboard

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 3 commits. Ran in 0m07s (clone 0m01s), peak RSS 462 MB, judge $0.0000 over 0 requests. Judged: no.

_No metric reached the headline._

### formbricks

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 2406 commits. Ran in 9m06s (clone 0m30s), peak RSS 532 MB, judge $0.0201 over 298 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.195 | 0.146 | -25% | -40% … -6% | 34977 | 36881 | — | better |
| production lines added per commit | 23 | 57 | +148% | — | 719 | 975 | <0.0001 | unclear |
| cyclomatic delta (per 100 production lines added) | 3.97 | 9.46 | +138% | — | 719 | 975 | — | worse |
| reimplementations (per KLOC added) | 0.108 | 0.0565 | -48% | — | 737 | 975 | — | better |
| share of follow-ups that are repairs | 0.243 | 0.189 | -22% | — | 37 | 74 | — | better |
| lines rewritten within 30 days | 0.1 | 0.0839 | -16% | -41% … +18% | 34977 | 36881 | — | withheld — CI includes 0 |
| follow-ups (per change) | 1.15 | 1.32 | +15% | — | 744 | 982 | — | worse |

### grafana

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 17903 commits. Ran in 1h20m (clone 1m15s), peak RSS 1594 MB, judge $0.1996 over 4857 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.185 | 0.119 | -35% | -50% … -16% | 35605 | 38216 | — | better |
| lines rewritten within 30 days | 0.116 | 0.0782 | -32% | -51% … -6% | 35605 | 38216 | — | better |
| production lines added per commit | 29 | 56 | +93% | — | 4221 | 4761 | <0.0001 | unclear |

### hoppscotch

Adoption **2025-08**, window 2024-08-01 → 2026-10-18, baseline 12 months. 755 commits. Ran in 2m33s (clone 0m04s), peak RSS 271 MB, judge $0.0101 over 123 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 30 days | 0.103 | 0.0259 | -75% | -86% … -55% | 12609 | 13148 | — | better |
| lines rewritten within 90 days | 0.139 | 0.0493 | -64% | -77% … -44% | 12609 | 13148 | — | better |
| cyclomatic delta (per 100 production lines added) | 8.23 | 11.1 | +35% | — | 260 | 218 | — | worse |
| reimplementations (per KLOC added) | 0.239 | 0.173 | -28% | — | 265 | 220 | — | better |
| share of follow-ups that are repairs | 0.3 | 0.26 | -13% | — | 60 | 50 | — | better |

### infisical

Adoption **2026-08**, window 2025-08-01 → 2026-10-18, baseline 12 months. 3002 commits. Ran in 23m21s (clone 1m10s), peak RSS 892 MB, judge $0.0478 over 926 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.229 | 0.0908 | -60% | -69% … -50% | 56503 | 57040 | — | better |
| lines rewritten within 30 days | 0.11 | 0.0746 | -32% | -51% … -10% | 56503 | 57040 | — | better |
| production lines added per commit | 72 | 101 | +40% | — | 1690 | 683 | 0.0068 | unclear |
| follow-ups (per change) | 0.218 | 0.7 | +221% | — | 1702 | 689 | — | worse |
| rework edits (per 100 lines added) | 0.0289 | 0.0815 | +182% | — | 1702 | 689 | — | worse |
| share of follow-ups that are repairs | 0.17 | 0.0769 | -55% | — | 47 | 65 | — | better |
| reimplementations (per KLOC added) | 0.193 | 0.127 | -34% | — | 1682 | 667 | — | better |

### jitsi-meet

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 1814 commits. Ran in 3m54s (clone 0m02s), peak RSS 754 MB, judge $0.0103 over 161 requests. Judged: yes.

_No metric reached the headline._

### keep

Adoption **2025-06**, window 2024-06-01 → 2026-10-18, baseline 12 months. 1882 commits. Ran in 5m08s (clone 0m05s), peak RSS 492 MB, judge $0.0014 over 12 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 30 days | 0.165 | 0.0119 | -93% | -97% … -88% | 37594 | 7459 | — | better |
| lines rewritten within 90 days | 0.257 | 0.0224 | -91% | -96% … -86% | 37594 | 7459 | — | better |
| production lines added per commit | 24 | 15 | -38% | — | 1326 | 231 | <0.0001 | unclear |

### lightdash

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 15906 commits. Ran in 1h13m (clone 0m46s), peak RSS 1872 MB, judge $0.0690 over 1568 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.288 | 0.196 | -32% | -43% … -18% | 38055 | 47783 | — | better |
| lines rewritten within 30 days | 0.203 | 0.139 | -31% | -46% … -15% | 38055 | 47783 | — | better |
| production lines added per commit | 37 | 73 | +97% | — | 2834 | 6341 | <0.0001 | unclear |
| share of follow-ups that are repairs | 0.37 | 0.0581 | -84% | — | 27 | 86 | — | better |
| cyclomatic delta (per 100 production lines added) | 4.89 | 8.96 | +83% | — | 2834 | 6341 | — | worse |
| reimplementations (per KLOC added) | 0.204 | 0.126 | -38% | — | 2871 | 6389 | — | better |

### mattermost

Adoption **2025-06**, window 2024-06-01 → 2026-10-18, baseline 12 months. 4936 commits. Ran in 52m33s (clone 0m59s), peak RSS 1407 MB, judge $0.0667 over 1459 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 20 | 73 | +265% | — | 1370 | 1787 | <0.0001 | unclear |
| follow-ups (per change) | 0.26 | 0.633 | +144% | — | 1394 | 1819 | — | worse |
| reimplementations (per KLOC added) | 0.258 | 0.0858 | -67% | — | 1394 | 1787 | — | better |
| share of follow-ups that are repairs | 0.0625 | 0.0843 | +35% | — | 32 | 83 | — | worse |
| lines rewritten within 90 days | 0.0669 | 0.0599 | -10% | -36% … +27% | 31045 | 44416 | — | withheld — CI includes 0 |

### medusa

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 4112 commits. Ran in 12m42s (clone 0m02s), peak RSS 571 MB, judge $0.0255 over 512 requests. Judged: yes.

_No metric reached the headline._

### n8n

Adoption **2026-01**, window 2025-01-01 → 2026-10-18, baseline 12 months. 12999 commits. Ran in 1h00m (clone 0m35s), peak RSS 1723 MB, judge $0.1402 over 3332 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 27 | 62 | +130% | — | 3110 | 6901 | <0.0001 | unclear |
| days to first follow-up | 13.1 | 8.1 | -38% | — | 974 | 2710 | <0.0001 | unclear |
| share of follow-ups that are repairs | 0.13 | 0.0633 | -51% | — | 23 | 79 | — | better |
| lines rewritten within 90 days | 0.211 | 0.169 | -20% | -37% … +2% | 29758 | 36139 | — | withheld — CI includes 0 |
| lines rewritten within 30 days | 0.131 | 0.112 | -15% | -38% … +18% | 29758 | 36139 | — | withheld — CI includes 0 |

### nango

Adoption **2026-03**, window 2025-03-01 → 2026-10-18, baseline 12 months. 4073 commits. Ran in 10m45s (clone 0m22s), peak RSS 791 MB, judge $0.0290 over 593 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 19.5 | 52 | +167% | — | 1178 | 1154 | <0.0001 | unclear |
| follow-ups (per change) | 0.62 | 1.37 | +121% | — | 1197 | 1162 | — | worse |
| cyclomatic delta (per 100 production lines added) | 6.91 | 9.77 | +41% | — | 1178 | 1154 | — | worse |
| share of follow-ups that are repairs | 0.0938 | 0.0602 | -36% | — | 32 | 83 | — | better |
| lines rewritten within 30 days | 0.128 | 0.136 | +6% | -18% … +38% | 25922 | 37546 | — | withheld — CI includes 0 |

### nocodb

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 2778 commits. Ran in 19m51s (clone 0m01s), peak RSS 835 MB, judge $0.0162 over 375 requests. Judged: yes.

_No metric reached the headline._

### novu

Adoption **2025-06**, window 2024-06-01 → 2026-10-18, baseline 12 months. 5475 commits. Ran in 20m27s (clone 0m21s), peak RSS 715 MB, judge $0.0706 over 1399 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 30 days | 0.264 | 0.173 | -34% | -48% … -20% | 37500 | 47070 | — | better |
| lines rewritten within 90 days | 0.348 | 0.237 | -32% | -43% … -20% | 37500 | 47070 | — | better |
| production lines added per commit | 26 | 52 | +100% | — | 1864 | 2275 | <0.0001 | unclear |
| cyclomatic delta (per 100 production lines added) | 4.33 | 7.92 | +83% | — | 1864 | 2275 | — | worse |
| share of follow-ups that are repairs | 0.167 | 0.25 | +50% | — | 48 | 56 | — | worse |
| reimplementations (per KLOC added) | 0.217 | 0.232 | +7% | — | 1916 | 2320 | — | worse |
| follow-ups (per change) | 2.02 | 2.14 | +6% | — | 1922 | 2335 | — | worse |

### outline

Adoption **2025-12**, window 2024-12-01 → 2026-10-18, baseline 12 months. 3404 commits. Ran in 8m55s (clone 0m13s), peak RSS 599 MB, judge $0.0172 over 297 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 15 | 24.5 | +63% | — | 981 | 1630 | <0.0001 | unclear |
| lines rewritten within 30 days | 0.0816 | 0.0578 | -29% | -51% … +1% | 24998 | 25494 | — | withheld — CI includes 0 |
| cyclomatic delta (per 100 production lines added) | 5.93 | 7.63 | +29% | — | 981 | 1630 | — | worse |
| lines rewritten within 90 days | 0.132 | 0.102 | -22% | -42% … +3% | 24998 | 25494 | — | withheld — CI includes 0 |
| share of follow-ups that are repairs | 0.289 | 0.236 | -18% | — | 38 | 72 | — | better |
| reimplementations (per KLOC added) | 0.105 | 0.0907 | -13% | — | 992 | 1646 | — | better |

### payload

Adoption **2026-06**, window 2025-06-01 → 2026-10-18, baseline 12 months. 2603 commits. Ran in 9m58s (clone 0m11s), peak RSS 706 MB, judge $0.0155 over 240 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 20 | 37 | +85% | — | 1332 | 576 | <0.0001 | unclear |
| reimplementations (per KLOC added) | 0.044 | 0.0782 | +78% | — | 1337 | 583 | — | worse |
| cyclomatic delta (per 100 production lines added) | 5.46 | 8.54 | +56% | — | 1332 | 576 | — | worse |
| share of follow-ups that are repairs | 0.333 | 0.217 | -35% | — | 42 | 69 | — | better |
| lines rewritten within 90 days | 0.126 | 0.0916 | -28% | -49% … +1% | 21550 | 34318 | — | withheld — CI includes 0 |
| lines rewritten within 30 days | 0.0746 | 0.0626 | -16% | -47% … +34% | 21550 | 34318 | — | withheld — CI includes 0 |

### peppermint

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 22 commits. Ran in 0m07s (clone 0m01s), peak RSS 296 MB, judge $0.0000 over 0 requests. Judged: yes.

_No metric reached the headline._

### plane

Adoption **2026-03**, window 2025-03-01 → 2026-10-18, baseline 12 months. 1624 commits. Ran in 7m51s (clone 0m10s), peak RSS 696 MB, judge $0.0175 over 296 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.182 | 0.115 | -37% | -62% … -5% | 35010 | 9911 | — | better |
| reimplementations (per KLOC added) | 0.114 | 0.043 | -62% | — | 1100 | 243 | — | better |

### prefect

Adoption **2025-10**, window 2024-10-01 → 2026-10-18, baseline 12 months. 4441 commits. Ran in 13m17s (clone 0m13s), peak RSS 564 MB, judge $0.0422 over 905 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 30 days | 0.131 | 0.0905 | -31% | -54% … -3% | 36553 | 35078 | — | better |
| lines rewritten within 90 days | 0.167 | 0.125 | -25% | -44% … -1% | 36553 | 35078 | — | better |
| reimplementations (per KLOC added) | 0.355 | 0.714 | +101% | — | 1114 | 1426 | — | worse |
| share of follow-ups that are repairs | 0.267 | 0.125 | -53% | — | 75 | 40 | — | better |

### rallly

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 2221 commits. Ran in 4m13s (clone 0m04s), peak RSS 279 MB, judge $0.0160 over 249 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 13.5 | 33 | +144% | — | 558 | 1052 | <0.0001 | unclear |
| cyclomatic delta (per 100 production lines added) | 2.37 | 4.38 | +85% | — | 558 | 1052 | — | worse |
| reimplementations (per KLOC added) | 0.248 | 0.282 | +14% | — | 582 | 1085 | — | worse |
| lines rewritten within 90 days | 0.303 | 0.264 | -13% | -27% … +4% | 22361 | 38893 | — | withheld — CI includes 0 |
| follow-ups (per change) | 1.16 | 1.23 | +6% | — | 585 | 1087 | — | worse |

### redash

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 161 commits. Ran in 0m38s (clone 0m00s), peak RSS 238 MB, judge $0.0008 over 18 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| follow-ups (per change) | 0.0154 | 0.122 | +693% | — | 65 | 41 | — | worse |
| lines rewritten within 30 days | 0.003 | 0.0177 | +490% | — | 1333 | 1130 | — | withheld — no interval |
| lines rewritten within 90 days | 0.0038 | 0.0212 | +458% | — | 1333 | 1130 | — | withheld — no interval |
| reimplementations (per KLOC added) | 0.211 | 0.121 | -43% | — | 65 | 41 | — | better |
| cyclomatic delta (per 100 production lines added) | 5.94 | 7.1 | +20% | — | 64 | 40 | — | worse |

### sentry

Adoption **2026-01**, window 2025-01-01 → 2026-10-18, baseline 12 months. 35187 commits. Ran in 1h18m (clone 0m45s), peak RSS 1776 MB, judge $0.0730 over 1813 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.277 | 0.218 | -21% | -37% … -1% | 21679 | 23352 | — | better |
| production lines added per commit | 12 | 17 | +42% | — | 7349 | 7564 | <0.0001 | unclear |
| share of follow-ups that are repairs | 0.175 | 0.121 | -31% | — | 40 | 66 | — | better |
| cyclomatic delta (per 100 production lines added) | 4.08 | 5.26 | +29% | — | 7349 | 7564 | — | worse |
| reimplementations (per KLOC added) | 0.201 | 0.153 | -24% | — | 7821 | 8079 | — | better |
| lines rewritten within 30 days | 0.209 | 0.164 | -22% | -42% … +3% | 21679 | 23352 | — | withheld — CI includes 0 |

### strapi

Adoption **2026-05**, window 2025-05-01 → 2026-10-18, baseline 12 months. 1325 commits. Ran in 5m56s (clone 0m26s), peak RSS 430 MB, judge $0.0103 over 122 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| reimplementations (per KLOC added) | 0.121 | 0.0581 | -52% | — | 330 | 546 | — | better |
| lines rewritten within 90 days | 0.0737 | 0.0819 | +11% | -22% … +63% | 20263 | 29264 | — | withheld — CI includes 0 |
| lines rewritten within 30 days | 0.049 | 0.0447 | -9% | -45% … +51% | 20263 | 29264 | — | withheld — CI includes 0 |
| share of follow-ups that are repairs | 0.333 | 0.31 | -7% | — | 30 | 84 | — | better |
| rework edits (per 100 lines added) | 0.0536 | 0.0574 | +7% | — | 330 | 549 | — | worse |

### twenty

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 11790 commits. Ran in 33m32s (clone 1m28s), peak RSS 1295 MB, judge $0.0104 over 162 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.36 | 0.276 | -23% | -35% … -11% | 49560 | 49582 | — | better |
| production lines added per commit | 64 | 89 | +39% | — | 3532 | 4980 | <0.0001 | unclear |
| days to first follow-up | 7.7 | 6 | -22% | — | 1752 | 2197 | <0.0001 | unclear |
| reimplementations (per KLOC added) | 0.117 | 0.083 | -29% | — | 3585 | 5041 | — | better |
| lines rewritten within 30 days | 0.219 | 0.186 | -15% | -31% … +3% | 49560 | 49582 | — | withheld — CI includes 0 |
| share of follow-ups that are repairs | 0.093 | 0.087 | -7% | — | 43 | 69 | — | better |

### typebot.io

Adoption **2026-04**, window 2025-04-01 → 2026-10-18, baseline 12 months. 929 commits. Ran in 2m49s (clone 0m14s), peak RSS 309 MB, judge $0.0103 over 164 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.171 | 0.0663 | -61% | -81% … -36% | 25276 | 7086 | — | better |
| lines rewritten within 30 days | 0.102 | 0.0435 | -58% | -79% … -26% | 25276 | 7086 | — | better |
| production lines added per commit | 16 | 38.5 | +141% | — | 585 | 122 | <0.0001 | unclear |
| reimplementations (per KLOC added) | 0.12 | 0.0331 | -72% | — | 590 | 121 | — | better |

### unleash

Adoption **2026-06**, window 2025-06-01 → 2026-10-18, baseline 12 months. 2879 commits. Ran in 6m40s (clone 0m14s), peak RSS 462 MB, judge $0.0157 over 242 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.333 | 0.177 | -47% | -56% … -36% | 28950 | 32971 | — | better |
| lines rewritten within 30 days | 0.241 | 0.141 | -42% | -53% … -28% | 28950 | 32971 | — | better |
| production lines added per commit | 19 | 32 | +68% | — | 1280 | 750 | 0.0003 | unclear |
| share of follow-ups that are repairs | 0.0154 | 0.111 | +622% | — | 65 | 45 | — | worse |
| cyclomatic delta (per 100 production lines added) | 3.62 | 5.39 | +49% | — | 1280 | 750 | — | worse |
| reimplementations (per KLOC added) | 0.593 | 0.326 | -45% | — | 1295 | 762 | — | better |

### vendure

Adoption **2026-08**, window 2025-08-01 → 2026-10-18, baseline 12 months. 1030 commits. Ran in 4m25s (clone 0m10s), peak RSS 484 MB, judge $0.0135 over 231 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| production lines added per commit | 27 | 74 | +174% | — | 519 | 126 | <0.0001 | unclear |
| follow-ups (per change) | 0.236 | 0.661 | +180% | — | 530 | 127 | — | worse |
| lines rewritten within 90 days | 0.073 | 0.0821 | +12% | -47% … +96% | 23953 | 8896 | — | withheld — CI includes 0 |
| share of follow-ups that are repairs | 0.206 | 0.218 | +6% | — | 63 | 55 | — | worse |

### wagtail

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 2744 commits. Ran in 4m46s (clone 0m01s), peak RSS 577 MB, judge $0.0142 over 271 requests. Judged: yes.

_No metric reached the headline._

### wiki

Adoption **undated**, window 2024-10-19 → 2026-10-19, baseline 12 months. 260 commits. Ran in 1m14s (clone 0m01s), peak RSS 484 MB, judge $0.0000 over 1 requests. Judged: yes.

_No metric reached the headline._

### zulip

Adoption **2026-02**, window 2025-02-01 → 2026-10-18, baseline 12 months. 9231 commits. Ran in 21m22s (clone 0m26s), peak RSS 906 MB, judge $0.0087 over 122 requests. Judged: yes.

| Metric | Before | After | Change | 95% CI | n before | n after | p | Verdict |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| lines rewritten within 90 days | 0.227 | 0.141 | -38% | -56% … -10% | 14354 | 10972 | — | better |
| days to first follow-up | 14.6 | 8.65 | -41% | — | 335 | 114 | 0.0056 | unclear |
| share of follow-ups that are repairs | 0.0976 | 0.0606 | -38% | — | 82 | 33 | — | better |
| reimplementations (per KLOC added) | 0.19 | 0.162 | -15% | — | 3768 | 1901 | — | better |
| lines rewritten within 30 days | 0.346 | 0.319 | -8% | -29% … +21% | 14354 | 10964 | — | withheld — CI includes 0 |

