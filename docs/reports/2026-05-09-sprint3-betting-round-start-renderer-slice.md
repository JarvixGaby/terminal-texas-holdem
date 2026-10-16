# Sprint 3 Slice 7.1 Betting Round Start Renderer

Date: 2026-05-09

## Summary

Slice 7.1 moved the betting round start terminal line from direct `_betting_round()` stdout output into `TerminalEventRenderer` handling for the existing public `betting_round_started` event.

The visible terminal line is preserved exactly:

```text
{PHASE} 阶段下注开始
```

`_betting_round()` now emits the existing event and relies on terminal event rendering to display the line, preventing duplicate stdout when rendering is enabled.

## Verification

- `python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_betting_round_started tests/test_game_engine_events.py::test_betting_round_routes_start_display_through_renderer`
- `python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py`
