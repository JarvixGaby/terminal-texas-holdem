# Sprint 3 Slice 8.1 Hand Start Renderer Completion

Date: 2026-05-09

## Summary

Slice 8.1 routes the existing hand-start terminal banner through the structured `hand_started` engine event and `TerminalEventRenderer`.

The visible terminal output is unchanged:

```text
==================================================
开始新的一手牌
==================================================
```

## Changes

- Added `hand_started` rendering to `TerminalEventRenderer` using only public event payload routing.
- Added `hand_started` to the terminal event rendering allowlist in `game.py`.
- Removed the direct hand-start banner print from `start_new_hand()`, which is the start path used by `play_hand()`.
- Added renderer and integration regression coverage for the routed display path.

## Verification

Focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
```

Result: `32 passed`.

Full-suite verification is recorded in the active task completion notes.

Full verification:

```bash
python3 -m pytest -q
```

Result: `153 passed`.
