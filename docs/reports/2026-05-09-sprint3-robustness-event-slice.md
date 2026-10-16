# Sprint 3 Robustness Event Slice Report

Date: 2026-05-09

## Summary

Executed a narrow Sprint 3 robustness slice after the Claude Code architecture audit. The slice adds explicit betting-round lifecycle events without changing current terminal gameplay behavior or poker rules.

## Why this slice

Claude Code identified the correct next move as continuing Sprint 3 engine/UI separation incrementally, not starting online-room work or a broad `game.py` rewrite. This slice follows that recommendation by strengthening event coverage at a high-value boundary: `_betting_round()`.

## Implementation

### Code changes

- `game.py`
  - Emits `betting_round_started` at the beginning of `_betting_round()`.
  - Emits `betting_round_completed` once before each normal return path.
  - Keeps existing `print()` behavior unchanged.
  - Does not add these lifecycle events to default terminal rendering yet.

- `tests/test_game_engine_events.py`
  - Adds strict TDD coverage for betting-round lifecycle events.
  - Verifies public payload shape.
  - Verifies no private hole-card/deck terms are leaked.

- `docs/plans/2026-05-09-sprint3-robustness-event-slice-plan.md`
  - New narrowed execution plan.

- `docs/active_plan.md`
  - Updated from completed Terminal Pro Trust work to current Sprint 3 robustness slice.

## Event coverage matrix

| Event type | Current producer | Default terminal renderer | Headless collection | Privacy status | Notes |
| --- | --- | --- | --- | --- | --- |
| `cards_dealt` | `game.py` street deal methods | Yes | Optional via `collect_events=True` | Public community cards only | Existing Sprint 3 event. |
| `community_cards_displayed` | `game.py` display method | Yes | Optional | Public only | Existing renderer migration point. |
| `game_state_displayed` | `game.py` display method | Yes | Optional | Public player state only | Existing renderer migration point. |
| `active_players_displayed` | `game.py` display method | Yes | Optional | Public player state only | Existing renderer migration point. |
| `action_applied` | `game.py` `_record_processed_action()` | No | Optional | Public action metadata | Existing action-event boundary. |
| `validation_failed` | `game.py` `_record_processed_action()` | No | Optional | Public fallback/validation metadata | Existing safety event. |
| `hand_completed` | `game.py` hand completion paths | Partially supported by renderer, not auto-rendered in `_emit_event` allowlist | Optional | Public outcome only | Existing completion event. |
| `betting_round_started` | `game.py` `_betting_round()` | No | Optional | Public phase/pot/current bet/player names | Added in this slice. |
| `betting_round_completed` | `game.py` `_betting_round()` | No | Optional | Public phase/pot/current bet/player names/iteration count | Added in this slice. |

## Payload contracts added

### `betting_round_started`

```python
{
    "phase": str,
    "pot": int,
    "current_bet": int,
    "active_player_names": list[str],
}
```

### `betting_round_completed`

```python
{
    "phase": str,
    "continued": bool,
    "active_player_names": list[str],
    "pot": int,
    "current_bet": int,
    "iteration_count": int,
}
```

## Robustness properties

- TDD was followed: the new focused test first failed because no `betting_round_started` event existed.
- The implementation is additive and keeps terminal output unchanged.
- Events are public and serializable.
- No poker hand ranking/comparison semantics were modified.
- No online-room/API scope was started.

## Verification

Focused event tests:

```text
python3 -m pytest -q tests/test_game_engine_events.py::test_betting_round_emits_started_and_completed_events tests/test_game_engine_events.py
10 passed in 0.07s
```

Full-suite and benchmark verification are recorded in `docs/active_plan.md` after execution. Final verification passed with `135 passed in 28.75s`, 10-hand benchmark `illegal_action_rate=0.0`, and a collect-events headless smoke confirming both new betting lifecycle events are emitted.

## Recommended next slice

Continue with another small Sprint 3 migration, preferably one of:

1. Add lifecycle events for `hand_started` / `phase_started` with public payload only.
2. Make `headless_simulation.run_ai_only_simulation(..., collect_events=True)` the default in benchmark-only paths, after confirming artifact size and performance.
3. Add a test-only event coverage assertion that every full hand emits at least one lifecycle event, one action event, and one completion event.

Do not start `GameState` extraction until event coverage and regression tests are stronger.
