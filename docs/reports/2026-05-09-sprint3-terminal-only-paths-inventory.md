# Sprint 3 Terminal-Only Paths Inventory

Date: 2026-05-09

## Purpose

This report records direct terminal output paths that should remain direct for now instead of becoming `EngineEvent` payloads rendered by `TerminalEventRenderer`.

Sprint 3 renderer migration is for normal player-facing game-flow output: hand lifecycle, betting-round lifecycle, validated player actions, showdown reveals, winner announcements, pot distribution, and post-decision feedback. The paths below are different. They are terminal/debug/diagnostic exceptions, mostly used when the process is already in an exceptional state, when optional local tooling is unavailable, or when a human is interacting with terminal-only menus and recovery prompts.

## Boundary Rule

Keep direct terminal output when the message is:

- a guardrail for a suspected internal logic failure;
- a crash/recovery diagnostic intended for local development or operator debugging;
- a local configuration, persistence, import, or optional-module fallback warning;
- a terminal input prompt, retry prompt, cancellation message, or menu-only guard;
- output from replay, config, analytics, migration, or smoke-test command entry points outside the live engine event stream.

Do not use this exception for normal poker-hand narration. If a line tells the player that a hand started, a betting round began or ended, a player checked/called/raised/folded, cards were revealed, a winner was announced, or chips were awarded, that line belongs at the event boundary.

## Inventory

| Path | Current direct output | Why it remains terminal-only |
| --- | --- | --- |
| `game.py` `_betting_round()` max-iteration guard | Warns that the betting round exceeded `MAX_BETTING_ITERATIONS`, prints phase and active players, then raises `RuntimeError`. | This is a defect sentinel, not game narration. If it fires, the hand is already invalid for normal UX. Emitting a renderer event would make a broken engine state look like part of the public table stream. |
| `game.py` `start_new_hand()` insufficient active-player guard | Prints that the game cannot continue because fewer than two players have chips. | This is a terminal session stop condition. It is adjacent to game lifecycle, but it is not a completed hand event and currently doubles as local operator feedback for ending the CLI session. |
| `game.py` `_handle_early_winner()` impossible winner-count branches | Prints all-fold invalid-game warning, split-pot recovery message, or unexpected multiple-remaining-player diagnostic with player fold states. | These are defensive diagnostics for states that should not occur in normal No-Limit Hold'em flow. The valid early-winner and pot-distribution paths are already event-boundary-rendered; these exceptional paths should stay visibly diagnostic until a dedicated error-reporting boundary exists. |
| `game.py` `_show_realtime_assistance()` and `_show_instant_replay()` exception fallbacks | Prints that assistant or replay analysis is temporarily unavailable. | These features are terminal coaching overlays, not engine state. A failure does not alter betting legality, action order, pot state, or hand outcome. |
| `game.py` `_get_human_action()`, `_confirm_action()`, `_handle_raise_action()` | Terminal prompts, status/help commands, invalid-action retry text, cancellation text, and keyboard-interrupt auto-fold notice. | These are interactive CLI controls. They are not public table events and depend on synchronous `input()` loops. Validated final actions should be renderer-driven; prompt mechanics should remain direct terminal UI. |
| `main.py` game setup and runtime recovery guards | Initialization failures, optimization-module fallback, game-loop exception recovery prompt, user-interrupt handling, eliminated-human menu, and final menu/status screens. | `main.py` owns the terminal application shell. These messages are outside a single engine hand and are not part of the serializable public table event stream. |
| `player.py` AI import/decision fallback warnings | Prints advanced-AI import failure, standard/advanced AI exception details, stack trace, and fallback strategy notice. | These are local AI subsystem diagnostics. They may include exception details and implementation names, so they should not become public renderer events or future external-agent table messages. |
| `enhanced_error_handling.py` safe input helpers | Prints validation failures, recovery suggestions, retry-exhausted fallback messages, and unexpected input-processing error handling. | These helpers are terminal input infrastructure. They are intentionally close to CLI prompts and defaults, not poker engine events. |
| `game_config.py` and `enhanced_config_manager.py` config guards | Prints config load/save/import/export failures, version mismatch migration notices, validation repair notices, and defaults fallback. | These are local configuration diagnostics. They concern process setup and files, not a hand's public state. |
| `game_history.py`, `database.py`, `player_styles.py`, `player_evaluation.py`, `advanced_analytics.py` persistence/analytics failures | Prints save/load/query/statistics failures and migration/status messages. | These paths report local storage, stats, and analytics behavior. Some are operator-facing command output; others are fallback diagnostics. They should not enter hand event payloads. |
| `headless_simulation.py` `SimulationResult.errors` | Records invalid player-count and per-hand exception messages in the returned result object. | Headless simulations already use structured result fields instead of terminal rendering. These diagnostics are batch-run metadata, not terminal game-flow output. |
| Standalone smoke-test and demo entry points such as `advanced_ai_engine.py`, `data_visualization.py`, `instant_replay.py`, `realtime_assistant.py`, `side_pot_manager.py`, and legacy root tests | Print demo, smoke-test, chart, replay, or migration information when run directly. | These files are command-line tools or diagnostics outside `TexasHoldemGame` live event rendering. Keeping direct output preserves their standalone utility. |

## Distinction From Event-Boundary Output

Renderer events should continue to own normal player-facing hand flow:

- hand start and completion;
- phase and betting-round lifecycle;
- legal action application after provider/validator resolution;
- validation failure shown to the acting player;
- showdown start, player hand reveal, winner announcement, and pot distribution;
- human decision feedback that belongs to the post-action table experience.

The terminal-only paths above should not be used to hide ordinary poker output. They are exceptions because they are either outside the engine hand stream, part of synchronous CLI control, or evidence that the engine or optional local subsystem is in an abnormal state.

## Not Deferred / Still Normal Flow

The following remaining direct outputs are not covered by this terminal-only diagnostic exception:

- `game.py` `_deal_hole_cards()` "发放手牌..."
- `game.py` `_collect_blinds()` small blind and big blind post messages
- `game.py` `_showdown()` "参与摊牌的玩家..."
- `game.py` `_handle_early_winner()` winner chip-count message

These lines are normal player-facing poker-flow output, not debug or diagnostic paths. They should be migrated or verified separately, or covered by terminal UX parity work, instead of being treated as deferred terminal-only exceptions.

## Current Decision

No production code changes are needed for this slice. The direct paths listed here are intentionally deferred from Sprint 3 event migration. If a future Sprint adds a separate structured diagnostics channel, these paths can be reconsidered as diagnostics or logs, but they should not be modeled as ordinary player-facing renderer events.
