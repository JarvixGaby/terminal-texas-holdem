# Sprint 3 Slice 6.2 — Check Action Renderer

Date: 2026-05-09

## Objective

Route check action display through the public `action_applied` event renderer while preserving the existing terminal line.

## Changes

- Added `TerminalEventRenderer` handling for `action_applied` events where `action == "check"`.
- Removed direct human confirmation-path check prints; `_betting_round()` now emits the existing `action_applied` event and the renderer owns the visible check line.
- Added renderer and betting-round integration tests for check routing.

## TDD log

```text
RED:
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_check_action_applied tests/test_game_engine_events.py::test_betting_round_routes_check_through_action_applied_renderer
2 failed as expected:
- TerminalEventRenderer returned False for check action_applied.
- The human confirmation path still printed the check line directly to stdout.

GREEN:
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_check_action_applied tests/test_game_engine_events.py::test_betting_round_routes_check_through_action_applied_renderer
2 passed in 0.04s
```

## Verification

```text
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
28 passed in 0.05s

python3 -m pytest -q
149 passed in 33.06s
```

## Guardrails checked

- No canonical poker rule changes.
- No broad `game.py` rewrite.
- No online/API/WebSocket work.
- `action_applied` payload remains public and serializable.
- Existing check terminal text is preserved through the renderer without duplicate stdout.
