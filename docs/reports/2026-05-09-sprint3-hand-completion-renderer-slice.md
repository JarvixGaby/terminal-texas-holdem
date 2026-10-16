# Sprint 3 Slice 8.2 Hand Completion Renderer Completion

Date: 2026-05-09

## Summary

Slice 8.2 routes the existing early-winner hand-completion terminal display through the structured `hand_completed` engine event and `TerminalEventRenderer`.

The visible early-winner terminal output is unchanged:

```text
==============================
游戏结束
==============================

🏆 <winner> 获胜！（其他玩家都已弃牌）
💰 获得彩池: <pot> 筹码
```

## Changes

- Updated `TerminalEventRenderer` so public `hand_completed` events render the existing fold-win completion lines.
- Added `hand_completed` to the terminal event rendering allowlist in `game.py`.
- Removed the duplicated direct early-winner completion prints from `_handle_early_winner()`.
- Kept showdown completion event rendering silent to avoid duplicating existing showdown winner and payout output in this slice.
- Added renderer and `play_hand()` routing regression coverage.

## Verification

Focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
```

Result: `33 passed`.

Full-suite verification is recorded in the active task completion notes.
