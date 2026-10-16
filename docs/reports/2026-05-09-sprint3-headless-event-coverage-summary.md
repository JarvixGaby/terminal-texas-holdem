# Sprint 3 Headless Event Coverage Summary Report

Date: 2026-05-09

## Summary

Executed Batch 1 from the Sprint 3 robustness batch plan. The headless simulation result now summarizes collected engine events, making collect-events runs self-auditing without ad-hoc scripts.

## Why this slice

The previous slices added lifecycle events (`hand_started`, `phase_started`, `betting_round_started`, `betting_round_completed`), but verification still required manual scans over `result.engine_events`. This batch adds a small, additive summary layer so future batches can assert full-hand coverage cheaply and consistently.

## Implementation

Modified `headless_simulation.py`:

- Added `SimulationResult.event_type_counts` as a `Counter[str]`.
- Added `SimulationResult.event_types_by_hand_id` as a hand-id keyed event-type list.
- Updated collect-events subscriber to populate:
  - raw `engine_events`
  - aggregate event type counts
  - per-hand event type sequences

Modified `tests/test_headless_simulation.py`:

- Added `test_run_ai_only_simulation_summarizes_event_coverage`.
- The test first failed with:

```text
AttributeError: 'SimulationResult' object has no attribute 'event_type_counts'
```

Then implementation made the focused test pass.

## Robustness properties

- Additive only; no game rules changed.
- Default non-collecting runs keep the same behavior.
- Raw `engine_events` remain available for consumers.
- Summary fields are derived from existing event dictionaries.
- This prepares Batch 2 full-hand event coverage gate without broad refactors.

## Verification

Focused headless tests:

```text
python3 -m pytest -q tests/test_headless_simulation.py::test_run_ai_only_simulation_summarizes_event_coverage tests/test_headless_simulation.py
7 passed in 11.17s
```

Full suite and smoke:

```text
python3 -m pytest -q
138 passed in 26.70s

Errors: []
Events collected: 34
Event type counts: {'hand_started': 1, 'game_state_displayed': 1, 'betting_round_started': 4, 'action_applied': 14, 'betting_round_completed': 4, 'phase_started': 3, 'cards_dealt': 3, 'community_cards_displayed': 3, 'hand_completed': 1}
Hands summarized: 1
```

## Next batch

Batch 2 should add a dedicated full-hand coverage regression gate using the new summary fields. It should require at least one completed hand to include lifecycle, betting-round, action, and completion events, plus privacy checks.
