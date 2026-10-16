# Sprint 3 Slice 10.2 Player Hand Reveal Renderer Completion

Date: 2026-05-09

## Summary

Slice 10.2 routes each showdown hand reveal through a new public `player_hand_revealed` engine event and `TerminalEventRenderer`.

The terminal reveal line remains:

```text
AI-1: A♣ 3♠ - 一对A
```

The event payload is public and serializable after the reveal: player name, revealed hole cards, and hand description. It does not expose deck state or any non-revealed private cards.

## Changes

- Added `PlayerHandRevealedEvent` for the new `player_hand_revealed` event type.
- Added `player_hand_revealed` handling to `TerminalEventRenderer`.
- Added `player_hand_revealed` to event class dispatch and terminal rendering in `game.py`.
- Replaced only the direct per-player hand reveal print in `_showdown()` with event emission.
- Kept participating-player, winner announcement, and pot distribution output unchanged for later slices.

## Verification

Focused RED verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_player_hand_revealed tests/test_game_engine_events.py::test_showdown_routes_hand_reveal_through_renderer
```

Initial result: `2 failed` because `player_hand_revealed` was not rendered or emitted.

Focused GREEN verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_player_hand_revealed tests/test_game_engine_events.py::test_showdown_routes_hand_reveal_through_renderer
```

Result: `2 passed`.

Slice focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
```

Result: `39 passed`.

Full-suite verification:

```bash
python3 -m pytest -q
```

Result: `160 passed`.
