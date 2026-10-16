# Sprint 3 Slice 9.1 Validation Failure Renderer Completion

Date: 2026-05-09

## Summary

Slice 9.1 routes existing provider/action validation failure feedback through the structured `validation_failed` engine event and `TerminalEventRenderer`.

The event remains public and serializable. The terminal renderer now displays one clear validation failure line when a provider action is rejected and safely replaced by the validator fallback action:

```text
❌ <player> 动作验证失败: <reason>，已改为 <fallback_action>
```

## Changes

- Added `validation_failed` handling to `TerminalEventRenderer`.
- Added `validation_failed` to the terminal event rendering allowlist in `game.py`.
- Fixed invalid-provider terminal ordering so the validation failure explanation renders before the validator fallback action line.
- Kept `ActionValidator` legality and fallback behavior unchanged.
- Added focused renderer and betting-round routing regression tests, including no-duplicate-line and validation-before-fallback ordering assertions.

## Verification

Focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
```

Result: `35 passed`.

Full-suite verification:

```bash
python3 -m pytest -q
```

Result: `156 passed`.

## Review Fix

Senior Poker Player review requested one trust fix: when a provider illegally checks facing a bet and the validator falls back to fold, the terminal must explain the validation failure before showing the fallback fold line. The fix preserves the existing public event payloads and only changes the emission/rendering order for invalid provider actions:

```text
❌ AI-1 动作验证失败: illegal action: check，已改为 fold
✅ AI-1 弃牌
```
