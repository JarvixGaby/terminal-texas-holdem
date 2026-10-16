# Sprint 3 Batch 4 — Action Prompt/Display Boundary Inventory

Date: 2026-05-09

## Objective

Inventory remaining direct IO in `game.py` `_betting_round()` and classify which paths are event-ready versus terminal-only before selecting the next small event-boundary slice.

## Scope inspected

`game.py` lines around `_betting_round()`.

## Direct IO inventory

| Location | Current direct IO | Category | Event-ready? | Notes |
| --- | --- | --- | --- | --- |
| `_betting_round()` start | `print(f"\n{self.game_phase.upper()} 阶段下注开始")` | Lifecycle display | Partially | `betting_round_started` is already emitted with public phase/pot/current-bet/active-player data, but Batch 3 deliberately keeps lifecycle events silent until expected terminal lines are tested. |
| Max-iteration guard | warning `print(...)` lines before `RuntimeError` | Terminal diagnostic / exceptional path | Not first choice | Better handled later as an explicit error/diagnostic event if needed; do not change during normal action-display migration. |
| Call branch | `print(f"{player.name} 跟注: {actual_amount}")` | Action display | Yes | `action_applied` is already emitted after action processing with public player/action/amount/chips/pot/current-bet payload. This is safe to route through `TerminalEventRenderer`. |
| Raise branch | `print(f"{player.name} 加注到: {self.current_bet}")` | Action display | Yes | `action_applied` includes `current_bet`, so the existing visible line can be reproduced from the public event payload. |
| Fold/check branches | comments note printing happens in confirmation/provider path | Action confirmation display | Not in `_betting_round()` direct IO | Leave untouched in this batch; inventory is `_betting_round()` direct IO only. |
| AI action delay | `_delay_after_ai_action()` call | Terminal pacing | Terminal-only for now | Not direct text IO; keep as terminal-play pacing behavior and disabled in headless flows by existing tests/config. |
| Decision provider call | `_get_player_action(...)` | Input boundary | Already abstracted | Human input is behind the provider/validator boundary, not a direct `_betting_round()` `input(...)` call. |

## Selected Batch 5 slice

Migrate exactly one tiny event-boundary display path: route call/raise action-display lines through the existing `action_applied` event and `TerminalEventRenderer`.

Rationale:

- Uses an existing public event; no new engine event contract needed.
- Preserves existing Chinese terminal lines.
- Removes two direct `_betting_round()` prints without touching poker rules, action validation, or betting state transitions.
- Can be protected by focused renderer and game-level no-duplicate tests.

## Deferred items

- Betting-round lifecycle start line should remain direct until expected terminal lifecycle rendering is designed/tested.
- Exceptional max-iteration warnings should stay direct until an error/diagnostic event contract is needed.
- Human prompt/input UX remains behind the provider abstraction and should be inventoried separately if a future batch targets prompts outside `_betting_round()`.
