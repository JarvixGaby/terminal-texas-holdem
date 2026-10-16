# Sprint 3 Slice 6.1 — Fold Action Renderer

Date: 2026-05-09

## Objective

Route fold action display through the public `action_applied` event renderer while preserving the existing terminal line.

## Changes

- Added `TerminalEventRenderer` handling for `action_applied` events where `action == "fold"`.
- Removed the direct fold confirmation print from the human confirmation path; `_betting_round()` now emits the existing `action_applied` event and the renderer owns the visible fold line.
- Added renderer and betting-round integration tests for fold routing.

## TDD log

```text
RED:
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_fold_action_applied tests/test_game_engine_events.py::test_betting_round_routes_fold_through_action_applied_renderer
2 failed as expected:
- TerminalEventRenderer returned False for fold action_applied.
- The human confirmation path still printed the fold line directly to stdout.

GREEN:
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_fold_action_applied tests/test_game_engine_events.py::test_betting_round_routes_fold_through_action_applied_renderer
2 passed in 0.05s
```

## Verification

```text
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
26 passed in 0.06s

python3 -m pytest -q
147 passed in 38.93s
```

## Guardrails checked

- No canonical poker rule changes.
- No broad `game.py` rewrite.
- No online/API/WebSocket work.
- `action_applied` payload remains public and serializable.
- Existing fold terminal text is preserved through the renderer.
