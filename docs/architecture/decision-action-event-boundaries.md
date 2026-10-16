# Decision / Action / Event Boundaries

Date: 2026-05-12

## Purpose

This document defines the Phase 2 boundary between decision providers, action validation, engine events, history/report metadata, terminal rendering, headless collection, benchmark reporting, and future external-agent adapters.

It is a contract document only. It does not implement online rooms, WebSocket servers, public APIs, auth, external-agent runtimes, or new poker rules.

## Boundary Summary

| Layer | Current module | Contract responsibility |
| --- | --- | --- |
| Decision input | `decision_provider.py` / `GameStateSnapshot` | Build the acting seat's decision snapshot: public game state plus that seat's private hole cards. |
| Decision provider | `DecisionProvider.decide(...) -> ActionResponse` | Return a proposed action, amount, optional JSON-safe metadata, raw response, and provider error without mutating game state. |
| Legality boundary | `validate_action(...) -> ValidatedAction` in `action_validator.py` | Normalize provider output, enforce legal action/amount constraints, and return safe fallback actions without throwing. |
| Engine mutation | `game.py` betting/showdown flow | Apply only `ValidatedAction.action` and `ValidatedAction.amount` to chips, pot, side pots, folds, all-ins, history, and events. |
| Event boundary | `EngineEvent.public_payload`, `private_payload_by_player`, `metadata` in `engine_events.py` | Emit serializable lifecycle/action/showdown/feedback events for terminal, headless, and future adapters. |
| Terminal adapter | `terminal_renderer.py` | Render selected public engine events into terminal text. |
| Headless adapter | `headless_simulation.py` | Collect public-safe serialized events and hand summaries for local benchmark/evaluation. |
| Benchmark/reporting | `ai_system_evaluator.py` | Consume hand summaries and transcript samples as local trainer diagnostics and benchmark gates. |

## Decision Snapshot Contract

`GameStateSnapshot` is built immediately before a player acts through `game.py`'s provider pipeline. It is the only state shape a `DecisionProvider` should need.

Allowed fields include:

- `game_id` and `hand_id`.
- `phase`.
- `player_name` and `position` for the acting seat.
- `hole_cards` for the acting seat only.
- `community_cards` already dealt and visible.
- `pot_size`, `current_bet`, `amount_to_call`, `player_chips`, `min_raise`, `dealer_position`, `small_blind`, and `big_blind`.
- `visible_players`: public player states only: name, chips, current bet, folded/all-in flags, and position.
- `action_history`: public action records with phase, player name, action, and amount.
- `legal_actions`: action strings available to the acting player at that decision point.

Forbidden in decision snapshots for future external-agent surfaces:

- Deck order and undealt cards.
- Future community cards.
- Opponent hole cards before a valid showdown reveal.
- Private AI internals from other seats.
- Unsafe random state or seed material that could reconstruct hidden cards.

The built-in local AI may be adapted through existing internal objects, but future external-agent serialization must preserve this public-plus-own-private boundary.

## `DecisionProvider.decide(...) -> ActionResponse`

`DecisionProvider` is the decision abstraction. The canonical signature is:

```python
class DecisionProvider(ABC):
    @abstractmethod
    def decide(self, state: GameStateSnapshot) -> ActionResponse:
        ...
```

A provider may:

- Inspect the supplied `GameStateSnapshot`.
- Return an `ActionResponse(action, amount, metadata, raw_response, error)`.
- Include JSON-safe provider metadata such as public explanations, fallback flags, or provider name.
- Return an error field instead of raising when possible.

A provider must not:

- Mutate player chips, pot, community cards, deck, history, side pots, or engine phase.
- Decide from hidden cards belonging to another unrevealed seat.
- Bypass `validate_action(...)`.
- Treat `metadata` as private unless a future contract explicitly scopes private metadata.
- Include raw deck, opponent hole cards, hidden-card assumptions, or non-serializable runtime objects in public-facing metadata.

Current provider notes:

- `BuiltInAIDecisionProvider` wraps `AIPlayer.make_decision(...)`, converts the AI output to `ActionResponse`, and falls back to check/fold on provider error.
- `BuiltInAIDecisionProvider` filters explanation metadata through JSON-safe conversion and excludes keys such as `hole_cards`, `opponent_hole_cards`, and `deck`.
- `HumanCliDecisionProvider` is testable CLI IO scaffolding. Current terminal play still uses a legacy human provider path to preserve UX.

## `ActionResponse` Metadata Handling

`ActionResponse.metadata` is provider-supplied. It may be persisted into action metadata through `game.py`'s `_build_action_metadata()` and may later be inspected by benchmark/reporting code.

Allowed public metadata examples:

- `provider`: provider class/source name.
- `fallback`: whether the provider selected a provider-level fallback.
- `ai_explanation`: JSON-safe public explanation payload.
- Public strategy tags such as `c-bet`, `fold-to-cbet`, `pot-odds`, `pressure`, or `pot-control`.

Forbidden public metadata examples:

- `deck`.
- `hole_cards` outside the acting seat's private decision snapshot or valid showdown reveal.
- `opponent_hole_cards`.
- Raw search trees, private hidden-card assumptions, private solver state, or engine objects.
- Live random state/seed values capable of reconstructing hidden state.

Metadata consumers must treat provider metadata as public-reportable only after JSON-safety and visibility filtering.

## `validate_action(...) -> ValidatedAction`

`validate_action(snapshot, response)` is the legality and normalization boundary. The canonical flow is:

```python
response = provider.decide(snapshot)
validated = validate_action(snapshot, response)
return validated.action, validated.amount
```

`ValidatedAction` contains:

- `action`: normalized action used by the engine.
- `amount`: normalized amount used by the engine.
- `is_valid`: whether the original provider response passed validation.
- `reason`: `ok`, normalization reason, or fallback reason.
- `original_action` and `original_amount`: audit fields for provider/validator diagnostics.

Validation responsibilities:

- Reject actions not in `snapshot.legal_actions`.
- Reject check when facing a bet.
- Normalize call amounts to the current call price or short-stack all-in call.
- Enforce raise minimums and maximum total bet constraints.
- Normalize all-in to the player's current chip count.
- Return safe fallback check/fold on bad input or exceptions.

Validation non-responsibilities:

- It does not decide strategy.
- It does not mutate game state.
- It does not alter canonical hand ranking semantics.
- It does not grant access to hidden information.
- It does not redefine benchmark metrics; it supplies legality evidence consumed later.

## Engine Mutation Boundary

Only the engine flow in `game.py` may apply a validated action to game state. The engine should use the pre-action snapshot for decision evaluation and then mutate state in the betting branch:

1. Build decision snapshot.
2. Ask provider for `ActionResponse`.
3. Validate into `ValidatedAction`.
4. Store `last_action_response` and `last_validated_action` for audit metadata.
5. Capture pre-mutation pot/chip/current-bet values for decision evaluation.
6. Apply fold/check/call/raise/all-in to player, pot, side pot, current bet, and acted-since-last-raise state.
7. Record action history with decision evaluation and action metadata.
8. Emit public engine events.

Any future adapter must preserve this ordering. Decision quality and benchmark legality must be evaluated against the decision-time snapshot, not accidentally against post-mutation state.

## `EngineEvent` Contract

`EngineEvent` is the structured event boundary:

```python
@dataclass(frozen=True)
class EngineEvent:
    type: str
    hand_id: str
    phase: str
    public_payload: Dict[str, Any] = field(default_factory=dict)
    private_payload_by_player: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### `public_payload`

`public_payload` is safe for public terminal/headless/future adapter consumption if populated according to `docs/architecture/public-private-state-contract.md`.

It may contain:

- Public lifecycle fields: hand, phase, street, pot, current bet, active player names.
- Public board cards after they are dealt.
- Public player state: name, chips, current bet, dealer marker, folded/all-in flags.
- Applied public action details: player name, action, amount, chips before/after, pot, current bet.
- Validation failure summaries: original action/amount, fallback action, public reason.
- Showdown reveals only for players who reached showdown.
- Winner and pot distribution fields.
- Human-only decision feedback messages that do not leak hidden state.

It must not contain:

- Deck order or undealt/future cards.
- Folded/non-showdown hole cards.
- Opponent private cards before a valid showdown reveal.
- Private AI internals or raw hidden-card assumptions.
- Unsafe live seed/random-state data.

### `private_payload_by_player`

`private_payload_by_player` is reserved for future seat-scoped private delivery. Current headless event collection should keep it empty unless a future consumer is explicitly seat-scoped and covered by tests.

Future use must satisfy all of the following:

- Keyed by stable player/seat identity.
- Delivered only to that player/seat's adapter.
- Never copied into public transcript samples or aggregate public reports.
- Tested for no cross-seat leakage.
- Documented in the public/private state contract before broad use.

### `metadata`

`metadata` is event-level adapter metadata. Current examples include street labels such as `metadata={"street": "flop"}` for dealt-card events.

Default rule: treat `metadata` as public-adapter metadata. Do not place hidden cards, deck order, private AI state, raw provider objects, or unsafe seeds in metadata unless a future contract introduces explicit private metadata scoping and tests.

## Renderer Consumption Boundary

`TerminalEventRenderer` consumes selected `EngineEvent` objects and renders terminal-friendly lines. It should:

- Read from `public_payload` and public `metadata` only.
- Ignore `private_payload_by_player` unless a future terminal mode is explicitly seat-scoped and tested.
- Preserve existing terminal UX when event routing changes.
- Avoid adding hidden-card reveals outside valid showdown events.

Current rendered event types include hand start, cards dealt, community cards, game state, active players, betting round start, action applied, validation failed, decision feedback, showdown start, player hand reveal, winner announcement, pot distribution, and hand completion placeholders.

## Headless and Benchmark Consumption Boundary

`headless_simulation.py` may collect serialized `EngineEvent.to_dict()` results when `collect_events=True`. It may also summarize hand records for benchmark reporting.

Headless and benchmark consumers may use:

- Public event streams.
- Hand summaries with public action records.
- Showdown reveals that satisfy the showdown rules.
- Decision evaluations and action metadata for aggregate local trainer diagnostics.
- Illegal-action evidence from validation/evaluation fields.

They must not publish:

- Folded/non-showdown hole cards.
- Deck order or future cards.
- Private AI internals.
- `private_payload_by_player` content into public samples.
- Provider `raw_response` fields unless they have been serialized and visibility-filtered.

`ai_system_evaluator.py` may use internal summaries to compute local metrics, but public transcript samples and durable reports must remain public/private safe.

## Report and History Metadata Boundary

`game.py` records provider/validator metadata through `_build_action_metadata()`:

- `raw_action`
- `raw_amount`
- `raw_response`
- `provider_error`
- `provider_metadata`
- `validated_action`
- `validated_amount`
- `is_valid`
- `validation_reason`

This metadata is useful for debugging, benchmark gate tests, and local trainer diagnostics. It is not automatically safe for public API responses or external-agent transcripts.

Before metadata appears in public-facing docs, samples, reports, or future external-agent responses, consumers must verify:

1. It is JSON-serializable.
2. It contains no deck order, future cards, folded/non-showdown hole cards, or opponent private cards.
3. It contains no private AI internals or raw non-serializable runtime objects.
4. It is consistent with `docs/architecture/public-private-state-contract.md` and `docs/architecture/benchmark-gates.md`.

## Future External-Agent Boundary

Future external-agent adapters should plug in as `DecisionProvider` implementations or a thin adapter around that interface:

1. Receive a serialized, versioned, seat-scoped decision state equivalent to `GameStateSnapshot` / `ExternalAgentState`.
2. Return a serialized action response equivalent to `ActionResponse`.
3. Pass through `validate_action(...)` before any engine mutation.
4. Have timeouts/errors converted to safe fallback responses.
5. Emit or persist only JSON-safe public metadata by default.
6. Never receive opponent private cards or deck order.

External-agent adapters must not bypass `ActionValidator`, write directly to engine state, or consume event private payloads for another seat.

## Validation Targets

Future implementation and test slices should prove:

- `DecisionProvider.decide(...) -> ActionResponse` remains the decision boundary.
- Every provider action is passed through `validate_action(...) -> ValidatedAction` before state mutation.
- Invalid provider actions generate validation metadata and safe fallback events.
- `EngineEvent.public_payload` contains only public state or valid showdown reveals.
- `private_payload_by_player` stays empty in current headless public collection.
- `metadata` remains JSON-safe and public-safe by default.
- Terminal renderer output can be driven from event public payloads without hidden-card leaks.
- Benchmark/report consumption preserves transcript safety and illegal-action evidence.
