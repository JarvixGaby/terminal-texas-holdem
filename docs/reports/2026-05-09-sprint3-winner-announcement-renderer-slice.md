# Sprint 3 Slice 10.3 Winner Announcement Renderer Completion

Date: 2026-05-09

## Summary

Slice 10.3 routes winner announcement display through a public `winner_announced` engine event and `TerminalEventRenderer`.

Terminal wording remains equivalent:

```text
获胜者: <winner names>
```

For early fold wins, the existing completion wording remains:

```text
==============================
游戏结束
==============================

🏆 <winner> 获胜！（其他玩家都已弃牌）
💰 获得彩池: <pot> 筹码
```

## Changes

- Added `WinnerAnnouncedEvent` as a public serializable engine event.
- Added `winner_announced` rendering for showdown and fold-win winner announcements.
- Replaced the direct showdown winner print with the new event-renderer path.
- Moved the early-fold winner line out of `hand_completed` rendering to prevent duplicate winner announcements while preserving the existing line order.
- Kept pot distribution display on the existing `hand_completed` renderer path; Slice 11.1 remains responsible for `pot_distributed`.

## Verification

Focused RED:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_winner_announced tests/test_terminal_renderer.py::test_terminal_renderer_renders_fold_winner_announced tests/test_game_engine_events.py::test_winner_routes_announcement_through_renderer_for_early_fold tests/test_game_engine_events.py::test_winner_routes_announcement_through_renderer_for_showdown
```

Result before implementation: `4 failed`.

Focused GREEN:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_winner_announced tests/test_terminal_renderer.py::test_terminal_renderer_renders_fold_winner_announced tests/test_game_engine_events.py::test_winner_routes_announcement_through_renderer_for_early_fold tests/test_game_engine_events.py::test_winner_routes_announcement_through_renderer_for_showdown
```

Result after implementation: `4 passed`.

Required focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
```

Result: `43 passed`.

Full-suite verification:

```bash
python3 -m pytest -q
```

Result: `164 passed`.
