# Sprint 3 Batch 5 — Action Applied Renderer Slice

Date: 2026-05-09

## Objective

Execute one safe event-boundary migration from the Batch 4 inventory: move call/raise action-display lines out of direct `_betting_round()` prints and into the terminal renderer for `action_applied` events.

## Changes

### Tests

- `tests/test_terminal_renderer.py`
  - Added `test_terminal_renderer_renders_call_and_raise_action_applied_events`.
  - Confirms public `action_applied` payloads render the existing terminal lines:
    - `AI-1 跟注: 10`
    - `AI-2 加注到: 40`

- `tests/test_game_engine_events.py`
  - Added `test_betting_round_routes_call_print_through_action_applied_renderer`.
  - Added `test_betting_round_routes_raise_print_through_action_applied_renderer`.
  - Confirms `_betting_round()` no longer writes call/raise action lines directly to stdout when terminal event rendering is configured; the lines come through the renderer instead.

### Production code

- `terminal_renderer.py`
  - Added `action_applied` handling for `call` and `raise`.
  - Unsupported actions remain unrendered, preventing duplicate fold/check output from other confirmation paths.

- `game.py`
  - Removed direct call/raise prints from `_betting_round()`.
  - Added `action_applied` to the terminal event render allowlist.
  - Emits/renders `action_applied` before decision feedback, preserving the visible action line before feedback ordering for call/raise.

## TDD log

```text
RED:
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_call_and_raise_action_applied_events tests/test_game_engine_events.py::test_betting_round_routes_call_print_through_action_applied_renderer
2 failed as expected:
- TerminalEventRenderer returned False for action_applied.
- _betting_round still printed call directly to stdout.

GREEN:
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_call_and_raise_action_applied_events tests/test_game_engine_events.py::test_betting_round_routes_call_print_through_action_applied_renderer
2 passed in 0.03s
```

## Final verification

```text
Focused:
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
24 passed in 0.06s

Full:
python3 -m pytest -q
145 passed in 26.51s

Collect-events smoke:
Errors: []
Events collected: 9
Event type counts: {'hand_started': 1, 'game_state_displayed': 1, 'betting_round_started': 1, 'action_applied': 3, 'validation_failed': 1, 'betting_round_completed': 1, 'hand_completed': 1}
Hands summarized: 1
```

## Guardrails checked

- No canonical poker rule changes.
- No broad `game.py` rewrite.
- No online/API/WebSocket work.
- `action_applied` payload remains public and serializable.
- Terminal call/raise text is preserved while routing through the event renderer.
