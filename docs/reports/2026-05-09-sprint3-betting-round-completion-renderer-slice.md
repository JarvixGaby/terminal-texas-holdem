# Sprint 3 Slice 7.2: Betting Round Completion Renderer Boundary

Date: 2026-05-09

## Scope

Slice 7.2 inspected `_betting_round()` for direct betting-round completion display. No direct completion print existed; `_betting_round()` only emitted `betting_round_completed`.

## Decision

`betting_round_completed` remains intentionally silent in `TerminalEventRenderer`. Terminal rendering now still receives the event when terminal event rendering is enabled, but the renderer returns `False` and emits no terminal lines. This preserves the existing CLI UX while keeping lifecycle event routing observable at the adapter boundary.

## Verification

```bash
python3 -m pytest -q tests/test_game_engine_events.py::test_betting_round_routes_completion_display_through_renderer
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_keeps_betting_round_completed_silent_until_explicitly_rendered
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
python3 -m pytest -q
```

Result: focused slice tests pass; full suite passes with `152 passed`.
