# Sprint 3 Slice 10.1 Showdown Start Renderer Completion

Date: 2026-05-09

## Summary

Slice 10.1 routes the showdown-start terminal banner through a new public `showdown_started` engine event and `TerminalEventRenderer`.

The terminal still announces showdown with the same banner:

```text
==============================
摊牌阶段
==============================
```

The event payload is public and serializable: phase, pot, community cards, and remaining player names. It does not include private hole-card data.

## Changes

- Added `ShowdownStartedEvent` for the new `showdown_started` event type.
- Added `showdown_started` handling to `TerminalEventRenderer`.
- Added `showdown_started` to the terminal event rendering allowlist in `game.py`.
- Replaced only the direct showdown-start banner in `_showdown()` with event emission.
- Kept player hand reveal, winner announcement, and pot distribution output unchanged for later slices.

## Verification

Focused RED verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_showdown_started tests/test_game_engine_events.py::test_showdown_routes_start_display_through_renderer
```

Initial result: `2 failed` because `showdown_started` was not rendered or emitted.

Focused GREEN verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_showdown_started tests/test_game_engine_events.py::test_showdown_routes_start_display_through_renderer
```

Result: `2 passed`.

Slice focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
```

Result: `37 passed`.

Full-suite verification:

```bash
python3 -m pytest -q
```

Result: `158 passed`.
