# Sprint 3 Hand/Phase Lifecycle Event Slice Report

Date: 2026-05-09

## Summary

Executed the next small Sprint 3 robustness slice after the betting-round lifecycle event work. The slice adds public `hand_started` and `phase_started` events at stable hand and street transition boundaries without changing terminal gameplay behavior or poker rules.

## Implementation

### Code changes

- `game.py`
  - Emits `hand_started` in `start_new_hand()` after `current_game_id` is assigned and before private cards are dealt.
  - Emits `phase_started` in `_deal_flop()`, `_deal_turn()`, and `_deal_river()` after the phase is set and history phase is started.
  - Leaves default terminal rendering unchanged; these lifecycle events are not rendered by default.

- `tests/test_game_engine_events.py`
  - Adds TDD coverage for `hand_started` public payload and privacy boundaries.
  - Adds TDD coverage for `phase_started` public street lifecycle events and privacy boundaries.

- `docs/plans/2026-05-09-sprint3-hand-phase-lifecycle-event-slice-plan.md`
  - New narrowed execution plan.

- `docs/active_plan.md`
  - Updated to track this lifecycle event slice.

## Event coverage update

| Event type | Current producer | Default terminal renderer | Headless collection | Privacy status | Notes |
| --- | --- | --- | --- | --- | --- |
| `hand_started` | `game.py` `start_new_hand()` | No | Optional via `collect_events=True` | Public hand metadata only | Added in this slice. |
| `phase_started` | `game.py` street deal methods | No | Optional | Public street metadata and community cards only | Added in this slice. |
| `betting_round_started` | `game.py` `_betting_round()` | No | Optional | Public phase/pot/current bet/player names | Previous slice. |
| `betting_round_completed` | `game.py` `_betting_round()` | No | Optional | Public phase/pot/current bet/player names/iteration count | Previous slice. |
| `cards_dealt` | `game.py` street deal methods | Yes | Optional | Public community cards only | Existing Sprint 3 event. |
| `community_cards_displayed` | `game.py` display method | Yes | Optional | Public only | Existing renderer migration point. |
| `game_state_displayed` | `game.py` display method | Yes | Optional | Public player state only | Existing renderer migration point. |
| `active_players_displayed` | `game.py` display method | Yes | Optional | Public player state only | Existing renderer migration point. |
| `action_applied` | `game.py` `_record_processed_action()` | No | Optional | Public action metadata | Existing action boundary. |
| `validation_failed` | `game.py` `_record_processed_action()` | No | Optional | Public fallback/validation metadata | Existing safety event. |
| `hand_completed` | `game.py` hand completion paths | Partially supported by renderer, not auto-rendered in `_emit_event` allowlist | Optional | Public outcome only | Existing completion event. |

## Payload contracts added

### `hand_started`

```python
{
    "players": list[str],
    "small_blind": int,
    "big_blind": int,
    "dealer_position": int,
    "phase": "preflop",
    "pot": 0,
    "current_bet": 0,
}
```

### `phase_started`

```python
{
    "phase": str,
    "community_cards": list[str],
    "pot": int,
    "current_bet": int,
}
```

## Robustness properties

- TDD was followed: the focused tests first failed because no lifecycle events existed.
- The implementation is additive and non-rendered by default, so terminal UX stays unchanged.
- Event payloads are public and serializable.
- No hole-card or deck internals are emitted.
- No poker rule semantics were modified.
- No online/API/platform scope was started.

## Verification

Focused event tests:

```text
python3 -m pytest -q tests/test_game_engine_events.py::test_start_new_hand_emits_public_hand_started_event tests/test_game_engine_events.py::test_street_deal_methods_emit_phase_started_events tests/test_game_engine_events.py
12 passed in 0.04s
```

Full-suite and collect-events smoke verification are recorded in `docs/active_plan.md` after execution. Final verification passed with `137 passed in 27.74s`; collect-events smoke completed one hand with 23 events and confirmed `hand_started`, `phase_started`, `betting_round_started`, and `hand_completed` are present.

## Recommended next slice

Continue only with small event-boundary increments. Suggested next move:

1. Add `hand_completed` auto-render allowlist only after terminal output parity tests exist, or
2. Add a test-only full-hand event coverage assertion requiring `hand_started`, at least one `phase_started`, at least one betting-round event, one action event, and `hand_completed` in collect-events mode.

Do not start `GameState` extraction until event coverage and regression tests are stronger.
