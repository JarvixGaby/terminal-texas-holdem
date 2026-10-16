# Sprint 2.3B Completion Report: Blind-aware VPIP/PFR and Preflop Opportunities

Date: 2026-05-08
Project: Texas Hold'em local trainer -> AI Poker Arena / Agent Poker Platform

## Goal

Sprint 2.3B improves preflop metric fidelity by separating forced blind postings from voluntary preflop actions and by adding a denominator that reflects actual preflop opportunities.

Before this stage, VPIP/PFR used `hands_played` as the denominator. That was serviceable for early baselines, but it blurred busted/inactive-player behavior and did not explicitly encode blind positions or forced blind payments.

## Changes

### `game.py`

Added per-hand blind metadata:

- `current_blind_metadata`
- `blind_positions.small_blind`
- `blind_positions.big_blind`
- `forced_blinds[]`

Each forced blind record includes:

- `player_name`
- `blind_type`
- `amount`
- `chips_before`
- `chips_after`
- `is_forced`
- `is_all_in`

This metadata is included in `GameRecord.outcome_metadata` through `_build_outcome_metadata(...)`.

### `headless_simulation.py`

No separate schema migration was needed because headless summaries already pass through `record.outcome_metadata`. The Sprint 2.3B tests now verify every hand summary includes `blind_positions` and `forced_blinds`.

### `ai_system_evaluator.py`

Added `PlayerPokerMetrics.preflop_opportunities`.

Updated VPIP/PFR calculation:

- if blind metadata exists, denominator = `preflop_opportunities`
- otherwise, legacy fallback denominator = `hands_played`
- voluntary preflop `call`, `raise`, and `all-in` count toward VPIP
- voluntary preflop `raise` counts toward PFR
- forced blind postings are not action records and do not count as VPIP/PFR
- big blind `check` counts as an opportunity but does not count as VPIP/PFR

## Tests

Added/updated tests:

- `tests/test_ai_metrics.py`
  - `test_blind_aware_preflop_metrics_use_opportunities_and_ignore_forced_blinds`
- `tests/test_headless_simulation.py`
  - AI-only hand summaries must include `blind_positions` and `forced_blinds`

RED failures confirmed before implementation:

```text
AttributeError: 'PlayerPokerMetrics' object has no attribute 'preflop_opportunities'
AssertionError: outcome_metadata missing 'blind_positions' and 'forced_blinds'
```

GREEN verification:

```text
python3 -m pytest -q tests/test_ai_metrics.py::test_blind_aware_preflop_metrics_use_opportunities_and_ignore_forced_blinds tests/test_headless_simulation.py::test_run_ai_only_simulation_completes_small_batch_without_input
2 passed in 1.38s
```

Focused suite:

```text
python3 -m pytest -q tests/test_ai_metrics.py tests/test_headless_simulation.py tests/test_ai_system_evaluator.py tests/test_game_history_outcome_metadata.py
15 passed in 17.06s
```

Full suite:

```text
python3 -m pytest -q
90 passed in 22.86s
```

## 1,000-hand benchmark

Generated artifact:

- `docs/reports/2026-05-08-sprint2-3b-ai-1000-hand-benchmark.json`

Command:

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system
benchmark_ai_system(
    num_hands=1000,
    player_count=4,
    output_path='docs/reports/2026-05-08-sprint2-3b-ai-1000-hand-benchmark.json',
)
PY
```

Result summary:

```python
{
    'hands_played': 1000,
    'total_actions': 2785,
    'illegal_action_rate': 0.0,
    'average_decision_score': 59.581687612208256,
    'errors': [],
}
```

Grade distribution:

```python
{
    'questionable': 136,
    'good': 1870,
    'poor': 745,
    'excellent': 34,
}
```

Final stacks:

```python
{
    'AI-1': 3611,
    'AI-2': 0,
    'AI-3': 389,
    'AI-4': 0,
}
```

Blind-aware player metrics subset:

| Player | Hands | Preflop opportunities | VPIP | PFR | Fold rate | Showdown rate | Win rate | Poor/blunder rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI-1 | 1000 | 1000 | 0.039 | 0.03 | 0.882804995196926 | 0.006 | 0.081 | 0.2987512007684918 |
| AI-2 | 17 | 17 | 0.11764705882352941 | 0.058823529411764705 | 0.64 | 0.058823529411764705 | 0.0 | 0.16 |
| AI-3 | 1000 | 1000 | 0.063 | 0.057 | 0.8062678062678063 | 0.006 | 0.15 | 0.30389363722697055 |
| AI-4 | 632 | 632 | 0.0759493670886076 | 0.058544303797468354 | 0.8108108108108109 | 0.00949367088607595 | 0.13924050632911392 | 0.16516516516516516 |

## Interpretation

Sprint 2.3B makes VPIP/PFR denominators explicit and reduces ambiguity in future benchmark comparisons. AI behavior still appears overly tight/passive in this run: VPIP remains low and fold rates remain high. That should be addressed after Sprint 2.4 adds profile/style-aware breakdowns, so tuning can target the weakest profiles rather than aggregate behavior only.

## Remaining Sprint 2 work

Next active stage:

- Sprint 2.4 — Profile/style-aware benchmark breakdown

Then:

- Sprint 2.5 — Targeted AI tuning using benchmark feedback
- Sprint 2.6 — Headless engine boundary design spike
