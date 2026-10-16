# Sprint 2.3 Completion Report: Hand Outcome Metadata and Metric Fidelity

Date: 2026-05-08
Project: Texas Hold'em local trainer -> AI Poker Arena / Agent Poker Platform

## Goal

Sprint 2.3 started the metric-fidelity layer needed before AI tuning and online-room work.

This slice focused on making hand outcomes explicit instead of inferring showdown behavior from `final_hands`.

## Result

Sprint 2.3 slice is complete.

Implemented:

- explicit hand outcome metadata in `GameRecord`
- backward-compatible history loading for older records without outcome metadata
- outcome metadata emitted by showdown endings and fold/early-winner endings in `game.py`
- outcome metadata exposed in headless AI-only hand summaries
- evaluator `showdown_rate` now uses explicit `outcome_metadata.went_to_showdown` when available
- legacy fallback remains for older synthetic/loaded summaries without outcome metadata
- new tests for history persistence, headless summaries, and explicit showdown-rate calculation
- regenerated a 1,000-hand benchmark artifact after metric semantics changed

## Files changed

Code:

- `game_history.py`
- `game.py`
- `headless_simulation.py`
- `ai_system_evaluator.py`

Tests:

- `tests/test_game_history_outcome_metadata.py`
- `tests/test_headless_simulation.py`
- `tests/test_ai_metrics.py`

Docs/artifacts:

- `docs/plans/2026-05-08-sprint2-3-hand-outcome-and-metric-fidelity.md`
- `docs/reports/2026-05-08-sprint2-3-hand-outcome-and-metric-fidelity.md`
- `docs/reports/2026-05-08-sprint2-3-ai-1000-hand-benchmark.json`
- `docs/index.md`
- `docs/active_plan.md`

## Outcome metadata schema

`GameRecord.outcome_metadata` now contains:

```json
{
  "ended_by_fold": true,
  "went_to_showdown": false,
  "winner_reason": "fold",
  "street_reach": {
    "AI-1": {
      "saw_flop": false,
      "saw_turn": false,
      "saw_river": false
    }
  }
}
```

Current `winner_reason` values emitted by `game.py`:

- `showdown`
- `fold`
- `invalid_all_fold`

## TDD evidence

### History metadata RED

Command:

```bash
python3 -m pytest -q tests/test_game_history_outcome_metadata.py
```

Expected RED observed:

```text
TypeError: GameHistoryManager.finish_game() got an unexpected keyword argument 'outcome_metadata'
AttributeError: 'GameRecord' object has no attribute 'outcome_metadata'
```

Then implementation was added and the test passed.

### Headless summary RED

Command:

```bash
python3 -m pytest -q tests/test_headless_simulation.py::test_run_ai_only_simulation_completes_small_batch_without_input
```

Expected RED observed:

```text
assert all("outcome_metadata" in summary for summary in result.hand_summaries)
```

Then `game.py` and `headless_simulation.py` were updated and the test passed.

### Explicit showdown-rate RED

Command:

```bash
python3 -m pytest -q tests/test_ai_metrics.py::test_showdown_rate_uses_explicit_went_to_showdown_when_available
```

Expected RED observed:

```text
assert report.player_metrics["AI-1"].showdown_hands == 1
E assert 2 == 1
```

Then `ai_system_evaluator.py` was updated to use explicit `went_to_showdown` when present.

## Verification

Focused verification:

```bash
python3 -m pytest -q tests/test_game_history_outcome_metadata.py tests/test_headless_simulation.py tests/test_ai_metrics.py tests/test_ai_system_evaluator.py
```

Result:

```text
14 passed in 15.30s
```

Full suite:

```bash
python3 -m pytest -q
```

Result:

```text
89 passed in 21.22s
```

## Regenerated 1,000-hand benchmark

Because `showdown_rate` semantics changed, the benchmark artifact was regenerated.

Artifact:

- `docs/reports/2026-05-08-sprint2-3-ai-1000-hand-benchmark.json`

Command:

```bash
python3 - <<'PY'
from ai_system_evaluator import benchmark_ai_system
report = benchmark_ai_system(
    num_hands=1000,
    player_count=4,
    output_path='docs/reports/2026-05-08-sprint2-3-ai-1000-hand-benchmark.json',
)
print(report.to_dict())
PY
```

Summary:

```json
{
  "hands_played": 1000,
  "total_actions": 2608,
  "illegal_action_rate": 0.0,
  "average_decision_score": 57.78949386503067,
  "grade_distribution": {
    "questionable": 91,
    "good": 1656,
    "poor": 828,
    "excellent": 32,
    "blunder": 1
  },
  "final_stacks": {
    "AI-1": 0,
    "AI-2": 1958,
    "AI-3": 0,
    "AI-4": 2042
  },
  "errors": []
}
```

Explicit showdown rates are now much lower and more plausible than the previous proxy value of `1.0`:

```json
{
  "AI-1": 0.03861003861003861,
  "AI-2": 0.011,
  "AI-3": 0.03932584269662921,
  "AI-4": 0.011
}
```

## Interpretation

Sprint 2.3 improved measurement trustworthiness.

Before this change, `showdown_rate` was effectively a proxy based on `final_hands`, which could produce misleading `1.0` rates for long-running players.

After this change, the evaluator uses an explicit game outcome flag:

- `went_to_showdown=True` means count final-hand players toward showdown rate.
- `went_to_showdown=False` means do not count `final_hands` as showdown, even if final hand records exist for persistence/replay.
- no `outcome_metadata` means legacy fallback remains available.

## Remaining limitations

- `street_reach` is currently based on community-card count at hand end. It is adequate for hand-level reach but not yet per-player folded-street precision.
- VPIP/PFR are still not blind-aware.
- Preflop opportunity counting is still based on `hands_played`, not exact action opportunity.
- AI decision quality remains weak: the benchmark still has 828 `poor` actions and 1 `blunder` out of 2,608 actions.
- `game.py` still mixes CLI output, sleeps, state mutation, history, and evaluation.

## Recommended next Sprint 2.3 slice

Continue with blind-aware preflop metrics:

1. Record blind positions and forced blind postings in hand/action metadata.
2. Add `preflop_opportunities` per player.
3. Recalculate VPIP/PFR using voluntary opportunities instead of raw hands played.
4. Regenerate the 1,000-hand benchmark and compare against this artifact.
