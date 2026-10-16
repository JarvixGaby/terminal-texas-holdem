# Sprint 3 Completion Report: Event-Boundary Migration

Date: 2026-05-09
Final verification date: 2026-05-10
Project: Texas Hold'em local terminal trainer -> future AI Poker Arena / Agent Poker Platform

## Summary

Sprint 3 is complete for the local terminal/headless event-boundary foundation.

The sprint moved normal poker-hand narration toward structured `EngineEvent` emission and `TerminalEventRenderer` output while preserving the existing terminal trainer experience. It also established headless event collection evidence for future adapter work.

This is not online/API/WebSocket/platform readiness. Sprint 3 readiness is bounded to local terminal and headless engine-event boundaries.

## Completed Sprint 3 Work

- Foundation: added the `EngineEvent` contract, terminal renderer, headless event collection, and injectable AI delay.
- Headless summary fields: added event count and per-hand event summary fields for collect-events runs.
- Full-hand coverage gate: added regression coverage requiring lifecycle, betting, action, and completion events in a completed hand.
- Terminal renderer parity: added renderer tests for lifecycle and table display events.
- Action display migration: routed call, raise, fold, and check display through `action_applied`.
- Betting lifecycle migration: routed betting-round start display through `betting_round_started`; kept completion lifecycle event silent because no user-facing completion line existed.
- Hand lifecycle migration: routed hand start display through `hand_started`; kept `hand_completed` public and serializable while renderer output remains silent for non-display completion payloads.
- Validation feedback migration: routed provider validation failure display through `validation_failed`.
- Showdown/outcome migration: added and rendered `showdown_started`, `player_hand_revealed`, `winner_announced`, and `pot_distributed`.
- Decision feedback migration: added and rendered `decision_feedback_displayed` for compact human decision feedback.
- Deferred-path inventory: documented terminal-only diagnostics and explicitly separated them from ordinary poker narration.
- Final verification: completed terminal UX parity verification and 100-hand headless event coverage verification.

## Final Test Evidence

Slice 13.3 was documentation-only, so no RED behavior test was needed. Verification used the required focused renderer/event tests and full suite.

Focused renderer/event tests:

```text
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
48 passed in 0.10s
```

Full suite:

```text
python3 -m pytest -q
170 passed in 36.81s
```

Prior Slice 13.1 terminal UX parity verification also recorded:

```text
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
48 passed in 0.09s

python3 -m pytest -q
170 passed in 38.81s
```

Prior Slice 13.2 headless coverage verification recorded:

```text
python3 -m pytest -q
170 passed in 39.95s
```

## Event Coverage Matrix

| Area | Event path | Terminal rendering | Headless coverage | Privacy/serialization status | Sprint 3 status |
| --- | --- | --- | --- | --- | --- |
| Hand lifecycle start | `hand_started` | Renders hand-start banner. | Present for every hand in 100-hand verification. | Public payload only. | Complete for local terminal/headless boundary. |
| Hand lifecycle completion | `hand_completed` | Allowed through renderer but intentionally silent for current terminal UX. | Present for every hand in 100-hand verification. | Public final hand summary excludes private hole cards. | Complete as event contract; no new terminal line added. |
| Street lifecycle | `phase_started`, `cards_dealt`, `community_cards_displayed`, `game_state_displayed` | Existing terminal flow preserved for board/state display. | Present in headless sample when hands reached later streets. | Public board/state data only. | Covered. |
| Betting lifecycle | `betting_round_started`, `betting_round_completed` | Start renders the existing phase-start line; completion remains silent. | Present in headless sample. | Public phase/pot/current-bet style data. | Covered. |
| Player actions | `action_applied` | Renders call, raise, fold, and check action lines. | Present in every completed-hand coverage gate and 100-hand verification. | Public action/player/amount data only. | Covered. |
| Validation feedback | `validation_failed` | Renders provider fallback validation feedback. | Present in the 100-hand AI-only sample through safe fallback behavior. | Public reason/fallback/action data only. | Covered. |
| Showdown start | `showdown_started` | Renders showdown banner. | Present in the 100-hand sample when showdown occurred. | Public pot/board/player names. | Covered. |
| Hand reveal | `player_hand_revealed` | Renders revealed showdown hole cards and hand description. | Present in the 100-hand sample when showdown occurred. | Public only because showdown cards are intentionally revealed. | Covered. |
| Winner announcement | `winner_announced` | Renders showdown and fold-winner announcements. | Present for every hand in 100-hand verification. | Public winner names and reason only. | Covered. |
| Pot distribution | `pot_distributed` | Renders visible chip-award lines. | Present for every hand in 100-hand verification. | Public player/winnings/pot data only. | Covered. |
| Decision feedback | `decision_feedback_displayed` | Renders compact human decision feedback. | Not expected in AI-only headless verification. | Public message payload only. | Covered for human terminal path; absent from AI-only run by design. |
| Headless collection | `SimulationResult.engine_events`, `event_type_counts`, `event_types_by_hand_id` | Not terminal-rendered. | 100 hands, 1071 events, 100 hand ids verified. | All event dicts JSON-serializable; `private_payload_by_player` empty in verification. | Covered. |
| Terminal-only/deferred diagnostics | No ordinary table event. | Remain direct terminal diagnostics/prompts. | Not part of hand event stream. | Avoids leaking local errors/config/details into public table events. | Documented and bounded. |

## Terminal UX Parity Evidence

`docs/reports/2026-05-10-sprint3-terminal-ux-parity-verification.md` verified 8 scripted terminal hands using real `TexasHoldemGame.play_hand()` with `TerminalEventRenderer` enabled.

The transcript covered invalid human action fallback, human decision feedback, fold spots, raise/call spots, check-through postflop streets, and multiple showdowns. Observed output retained the expected order: hand start, card/blind/table state, betting-round start, player actions, board progression, showdown, hand reveals, winner announcement, and pot distribution.

No duplicated renderer lines, missing migrated display lines, or out-of-order terminal UX regressions were observed.

## Headless Coverage, Privacy, and Serialization Evidence

`docs/reports/2026-05-10-sprint3-headless-event-coverage-verification.md` verified a 100-hand AI-only run with event collection:

```text
errors= []
hands_requested= 100
hands_completed= 100
engine_event_count= 1071
unique_hand_ids= 100
hand_started_count= 100
hand_completed_count= 100
```

Observed event type counts:

```text
action_applied: 271
betting_round_completed: 115
betting_round_started: 115
cards_dealt: 15
community_cards_displayed: 15
game_state_displayed: 100
hand_completed: 100
hand_started: 100
phase_started: 15
player_hand_revealed: 8
pot_distributed: 100
showdown_started: 4
validation_failed: 13
winner_announced: 100
```

All collected events were JSON-serializable, all `public_payload` values were dictionaries, and `private_payload_by_player` was empty for every collected event. Public showdown reveal events intentionally include revealed hole cards because those cards are visible at showdown.

## Terminal-Only Deferred Paths

`docs/reports/2026-05-09-sprint3-terminal-only-paths-inventory.md` documents direct terminal paths that remain outside the event boundary for now:

- defect sentinels such as max betting-round iteration warnings;
- impossible-state recovery and diagnostics;
- terminal prompts, retry/cancel messages, and keyboard-interrupt handling;
- local setup, config, persistence, analytics, import, and optional-module diagnostics;
- standalone smoke-test, replay, visualization, and demo command output.

That exception must not hide normal poker narration. If output tells the player that a hand started, a betting round began, a player checked/called/raised/folded, cards were revealed, a winner was announced, or chips were awarded, it belongs at the event boundary unless a later slice explicitly documents otherwise.

The inventory also calls out remaining normal-flow direct outputs that are not covered by the diagnostic exception:

- `_deal_hole_cards()` "发放手牌..."
- `_collect_blinds()` small blind and big blind post messages
- `_showdown()` "参与摊牌的玩家..."
- `_handle_early_winner()` winner chip-count message

These remain candidates for later migration or explicit parity verification.

## Known Limitations

- Sprint 3 does not create a network adapter, API contract, WebSocket room, platform runtime, authentication model, or external-agent execution sandbox.
- `EngineEvent` payloads are ready for local terminal/headless consumers, but future public API schemas still need stricter versioning and compatibility rules.
- Some normal-flow terminal lines remain direct output and should be handled deliberately in later work.
- Terminal-only diagnostics are intentionally not modeled as public table events; a future diagnostics/log channel may revisit them separately.
- Current headless verification used AI-only simulation. Human-only decision feedback is covered by focused renderer/event tests and terminal parity verification, not by the AI-only headless count.

## Sprint 4 Readiness

Sprint 4 can safely build on a local event-boundary foundation:

- terminal rendering has a tested adapter path for the primary poker-hand narration;
- headless simulations can collect structured, serializable event dictionaries;
- public/private payload boundaries have been checked in the final coverage run;
- deferred terminal-only paths are documented so future work does not confuse diagnostics with table narration.

The next sprint should keep the same boundary discipline: strengthen local engine/event contracts first, then approach external-agent or online-room work only after the local public schema is explicit and stable.
