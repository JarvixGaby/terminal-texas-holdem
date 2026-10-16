# Sprint 3 Headless Event Coverage Verification

Date: 2026-05-10

## Summary

Slice 13.2 verified the headless collect-events path with a 100-hand AI-only simulation. No production code changes were made.

## Simulation Evidence

Command:

```bash
python3 - <<'PY'
import json
from collections import Counter, defaultdict
from headless_simulation import run_ai_only_simulation

result = run_ai_only_simulation(
    num_hands=100,
    player_count=4,
    starting_chips=500,
    collect_events=True,
)
# The verification script checked errors, hand count, event counts,
# JSON serialization, public payload shape, private payload use,
# and per-hand lifecycle/action/completion coverage.
PY
```

Observed result:

```text
errors= []
hands_requested= 100
hands_completed= 100
engine_event_count= 1071
unique_hand_ids= 100
hand_started_count= 100
hand_completed_count= 100
```

Event type counts:

```text
{
  "action_applied": 271,
  "betting_round_completed": 115,
  "betting_round_started": 115,
  "cards_dealt": 15,
  "community_cards_displayed": 15,
  "game_state_displayed": 100,
  "hand_completed": 100,
  "hand_started": 100,
  "phase_started": 15,
  "player_hand_revealed": 8,
  "pot_distributed": 100,
  "showdown_started": 4,
  "validation_failed": 13,
  "winner_announced": 100
}
```

## Coverage Findings

- The event stream was non-empty and covered all 100 completed hand ids.
- Every hand included `hand_started`, at least one `action_applied`, and `hand_completed`.
- Lifecycle and street/display coverage was present: `hand_started`, `phase_started`, `betting_round_started`, `betting_round_completed`, `cards_dealt`, `community_cards_displayed`, and `game_state_displayed`.
- Outcome coverage was present: `winner_announced`, `pot_distributed`, and `hand_completed`.
- Showdown coverage was present in the simulated sample: `showdown_started` and `player_hand_revealed`.
- `validation_failed` appeared 13 times through existing safe fallback behavior.
- `decision_feedback_displayed` was absent, which is expected for this AI-only simulation because that event is emitted by the existing human decision feedback path.
- `action_requested` was not treated as a missing expected category because the current codebase has no producer or existing coverage contract for that event type.

## Payload Findings

- All collected event dictionaries were JSON-serializable.
- Every `public_payload` was a `dict`.
- `private_payload_by_player` was empty for every collected event.
- No private hole-card/deck payload channel was used in this headless run. Public showdown reveal events intentionally expose revealed showdown cards through `public_payload`.

## Tests

```text
python3 -m pytest -q
170 passed in 39.95s
```

## Active Plan

After the simulation and full test suite passed, Slice 13.2 was marked complete and Slice 13.3 was advanced to the single current `[>]` slice.
