# Public/Private State Contract

Date: 2026-05-11

## Purpose

This document defines what each project actor may see during a Texas Hold'em hand. It is the Phase 2 visibility contract for local trainer, built-in AI, benchmark/reporting, terminal/headless adapters, and future external agents.

No API server, WebSocket server, online room, auth system, or external-agent runtime is implemented by this document.

## Current Module Boundaries

- `agent_state_contract.py` defines immutable future-facing external-agent state objects: `ExternalAgentState` and `PublicAgentPlayerState`.
- `decision_provider.py` defines `GameStateSnapshot`, `VisiblePlayerSnapshot`, `DecisionProvider`, `ActionResponse`, `BuiltInAIDecisionProvider`, and `HumanCliDecisionProvider`.
- `action_validator.py` validates provider output through `validate_action(...)` and normalizes unsafe or illegal responses into `ValidatedAction`.
- `engine_events.py` defines `EngineEvent` with `public_payload`, `private_payload_by_player`, and `metadata`.
- `headless_simulation.py` runs local AI-only simulations and can collect serialized engine events when `collect_events=True`.
- `ai_system_evaluator.py` summarizes local benchmark results, player/profile metrics, stack metrics, seeded/multi-seed reports, and bounded transcript samples.

## Protected Private Data

These values are private unless a rule below explicitly reveals them:

- Deck order and undealt cards.
- Unrevealed opponent hole cards.
- A player's private hole cards, except to that player, its current decision provider, or future external agent acting for that same seat.
- Private AI internals that are not JSON-safe public explanation metadata, including raw hidden-card assumptions, private search state, and fields named like `deck`, `hole_cards`, or `opponent_hole_cards` inside explanation metadata.
- Random seeds when exposing them would allow reconstructing hidden state in a live or replay-sensitive context.
- Any future authentication, sandbox, account, or platform security state.

## Actor Visibility Matrix

| Actor | Pre-hand / setup | Preflop | Flop / turn / river | Showdown | After hand / report |
| --- | --- | --- | --- | --- | --- |
| Human player | Seat names, stacks, blinds, position, game settings. | Own hole cards, public player states, pot, bets, legal actions, action history, no opponent hole cards. | Own hole cards, community cards already dealt, public player states, pot, bets, legal actions, action history. | Showdown participants' revealed hands and winner/pot distribution; folded non-showdown hands stay hidden unless current terminal behavior deliberately records historical final hands outside public transcript surfaces. | May review public hand flow, own decisions, cautious trainer feedback, and showdown reveals. |
| Built-in AI | Same table state as its seat needs for decision-making. | Acting AI's own `state.hole_cards`, public players, legal actions, pot/bet context, public action history. | Acting AI's own hole cards, community cards, public players, legal actions, pot/bet context, public action history. | Revealed showdown hands only after public reveal. | AI explanation metadata may be saved only after JSON-safety filtering and must not include hidden deck/opponent-hole-card data. |
| Future external agent | Future serialized equivalent of `ExternalAgentState` for its own seat only. | Own `private_hole_cards`, `public_players`, `legal_actions`, pot/bet/blind fields, public action history. | Own private hole cards, visible community cards, public players, legal actions, pot/bet fields, public action history. | Public showdown reveals only. | May receive public hand result and its own seat outcome; no folded/non-showdown opponent cards. |
| Benchmark/reporting | Run parameters and aggregate public-safe simulation metadata. | May count actions, legal/illegal outcomes, public action records, and per-player metrics. | May count public board/action progression and metrics. | May include showdown reveals because those hands became public. | Transcript samples must omit folded/non-showdown hole cards and include hidden-card details only for true showdown reveals. Aggregate metrics may use internal final summaries but public report text must preserve visibility rules. |
| Terminal renderer / headless adapter | Public table setup and adapter configuration. | Renders or collects public events; private payloads must remain seat-scoped if used. | Renders or collects public events for visible board/action state. | Renders or collects `showdown_started`, `player_hand_revealed`, `winner_announced`, and `pot_distributed` public events. | Headless `engine_events` collection must keep `private_payload_by_player` empty unless a future consumer is explicitly seat-scoped and tested. |

## Phase Rules

### Pre-Hand and Setup

Public:

- Player names/seats, stack sizes, dealer position, blinds, and configuration needed to render or evaluate legal actions.

Private:

- Shuffled deck order, future board cards, and random state.

### Preflop

Public:

- Blinds, pot size, current bet, amount to call, public player stack/current-bet/fold/all-in state, action history, legal actions, and min raise.

Private:

- Each player's hole cards are visible only to that seat and its active decision provider. Opponent hole cards and deck order are hidden.

### Flop, Turn, and River

Public:

- Dealt community cards, public player state, pot and bet state, legal actions, action history, and street name.

Private:

- Unrevealed hole cards, deck order, future community cards, and private AI internals.

### Showdown

Public:

- `showdown_started` public information: phase, pot, community cards, and names of players who reached showdown.
- `player_hand_revealed` information for showdown participants: player name, revealed hole cards, and hand description.
- Winner announcements and pot distribution.

Private:

- Folded players' hole cards remain private in public event streams, transcript samples, and future external-agent surfaces.

### Fold-Ended Hands

Public:

- Winning player, pot amount, winning reason, and public action sequence.

Private:

- Non-showdown folded hands and any hidden deck/future-card data.

## Showdown Reveal Rules

1. A hand is public-reveal eligible only when `outcome_metadata["went_to_showdown"] is True` or an equivalent future event proves showdown.
2. `PlayerHandRevealedEvent` / `player_hand_revealed` events may include `hole_cards` only for players who reached showdown.
3. Folded players' hole cards must not appear in public event payloads, transcript samples, external-agent state, or public benchmark prose.
4. Internal history may retain full final-hand details for local compatibility, but any public-facing renderer, report, or future external-agent adapter must filter through this visibility contract.

## Benchmark Transcript and Reporting Rules

`ai_system_evaluator.py` currently builds transcript samples from `headless_simulation.py` hand summaries. Phase 2 treats these samples as public-facing review artifacts.

Transcript samples may include:

- Hand number.
- Public street boards after cards are dealt.
- Public actions, amounts, winners, pot, and winner reason.
- Showdown hole cards only when the hand went to showdown.
- Public-safe flags such as c-bet or fold-to-cbet patterns.

Transcript samples must not include:

- Folded/non-showdown hole cards.
- Deck order or undealt cards.
- Private AI internals or raw hidden-card assumptions.
- Unsafe live random seed data that would reconstruct hidden state.

Aggregate benchmark reports may include:

- Hand counts, action counts, illegal action rate, decision score aggregates, profile metrics, style separability, stack concentration, seeds used for offline reproducibility, and public-safe transcript samples.

Aggregate benchmark reports must label their purpose correctly:

- They are local trainer quality gates and diagnostics.
- They are not solver validation, GTO proof, real-money readiness, or platform security certification.

## Decision and Event Boundary Implications

- `GameStateSnapshot.hole_cards` is private to the acting seat even though it is part of the decision snapshot.
- `VisiblePlayerSnapshot` and `PublicAgentPlayerState` must remain opponent-public: name, chips, current bet, folded/all-in flags, and position only.
- `BuiltInAIDecisionProvider` may use the acting player's hand and public game state, but its returned metadata must remain JSON-safe and hidden-card filtered.
- `validate_action(...)` in `action_validator.py` validates only actions and amounts. It must not become a visibility or hidden-information bypass.
- `EngineEvent.public_payload` is safe for terminal/headless/future public consumers. `private_payload_by_player` is reserved for future seat-scoped private delivery and requires tests before use.
- `EngineEvent.metadata` must be treated as public-adapter metadata unless a future contract explicitly scopes it.

## Phase 2 Validation Targets

Future implementation slices should add tests that prove:

- Serialized external-agent state contains only public state plus the acting seat's private hand.
- Public event streams do not contain folded/non-showdown hole cards.
- Benchmark transcript samples include showdown reveals only when showdown occurred.
- AI explanation metadata does not serialize `deck`, `hole_cards`, or `opponent_hole_cards`.
- Any exposed seed metadata is offline benchmark metadata, not live hidden-state leakage.
