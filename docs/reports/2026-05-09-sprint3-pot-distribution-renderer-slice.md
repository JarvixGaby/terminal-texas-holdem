# Sprint 3 Slice 11.1 Pot Distribution Renderer

Date: 2026-05-09

## Scope

Routed visible pot payout lines through a public `pot_distributed` engine event and `TerminalEventRenderer`.

## Changes

- Added `PotDistributedEvent`.
- Emitted `pot_distributed` at showdown payout, early-fold payout, and invalid all-fold split payout display points.
- Added terminal rendering for `pot_distributed`.
- Kept payout wording aligned with existing terminal UX:
  - Showdown/split: `<player> 获得 <amount> 筹码`
  - Early fold: `💰 获得彩池: <amount> 筹码`
- Stopped `hand_completed` from rendering the early-fold payout line to avoid duplicate output.

## Event Boundary

`pot_distributed` uses public serializable payload only:

- `player_name`
- `winnings`
- `winner_reason`
- `total_pot`

No private hole cards, deck state, side-pot internals, or agent-private state are included.

## TDD Evidence

RED:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_pot_distributed tests/test_game_engine_events.py::test_pot_distribution_routes_display_through_renderer tests/test_game_engine_events.py::test_early_fold_pot_distribution_routes_display_through_renderer
```

Failed with missing renderer handling and missing `pot_distributed` emission.

GREEN:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_pot_distributed tests/test_game_engine_events.py::test_pot_distribution_routes_display_through_renderer tests/test_game_engine_events.py::test_early_fold_pot_distribution_routes_display_through_renderer
```

Passed: `3 passed`.

Focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
```

Passed: `46 passed`.

Full verification:

```bash
python3 -m pytest -q
```

Passed: `167 passed`.
