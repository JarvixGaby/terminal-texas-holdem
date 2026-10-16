# Sprint 3 Full-Hand Event Coverage Gate Report

Date: 2026-05-09

## Summary

Executed Batch 2 from the Sprint 3 robustness batch plan. Added a compact collect-events regression gate that requires at least one completed hand to include lifecycle, betting-round, action, and completion events.

## Implementation

Modified `tests/test_headless_simulation.py`:

- Added `test_collect_events_full_hand_has_lifecycle_action_and_completion_gate`.
- The test uses `SimulationResult.event_types_by_hand_id` from Batch 1.
- It requires at least one hand to contain:
  - `hand_started`
  - `betting_round_started`
  - `betting_round_completed`
  - `action_applied`
  - `hand_completed`
- It also checks public event serialization does not expose `hole_cards` or `deck`.

No production code changes were needed in Batch 2 because Batch 1 provided the summary primitive and existing event coverage satisfied the gate.

## Robustness properties

- Prevents future event-boundary regressions in collect-events mode.
- Keeps test scope small and fast enough for regular pytest runs.
- Does not change terminal behavior or game semantics.
- Uses public event summaries rather than ad-hoc scripts.

## Verification

```text
python3 -m pytest -q tests/test_headless_simulation.py::test_collect_events_full_hand_has_lifecycle_action_and_completion_gate tests/test_headless_simulation.py
8 passed in 10.48s

python3 -m pytest -q
139 passed in 29.78s
```

## Next batch

Batch 3 should focus on terminal renderer parity before any lifecycle event is rendered by default. It should add tests that explicitly define expected renderer behavior, or confirm lifecycle events remain silent until parity is specified.
