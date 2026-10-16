# External Agent Contract Stub

Date: 2026-05-12

## Purpose

This document defines the Phase 2 contract stub for a future external poker agent integration. It documents the request/response shape, versioning, serialization, timeout/error behavior, legal-action dependency, and seat-scoped visibility expected by future adapters.

This is documentation only. It does not implement an HTTP API, WebSocket server, MCP server, auth, sandboxing, process runner, public marketplace, or external-agent runtime.

## Scope and Dependencies

The future external agent adapter must sit behind the existing local decision boundary:

1. `game.py` builds a decision-time `GameStateSnapshot` for exactly one acting seat.
2. `agent_state_contract.py` converts that snapshot into an `ExternalAgentState` with public table state plus only the acting seat's `private_hole_cards`.
3. A future adapter serializes `ExternalAgentState` into an external agent request.
4. The external agent returns an action response.
5. The adapter maps that response into `ActionResponse`.
6. `validate_action(snapshot, response)` remains the required legality boundary before engine mutation.
7. Engine events, headless transcripts, and benchmark reports remain governed by `docs/architecture/public-private-state-contract.md` and `docs/architecture/decision-action-event-boundaries.md`.

## Versioning

Every future request and response should carry an explicit schema version.

Recommended current stub value:

```json
{
  "schema_version": "external-agent.v0"
}
```

Versioning rules:

- `external-agent.v0` means a local trainer contract stub, not a public platform API guarantee.
- Breaking field removals or semantic changes require a new version.
- Additive public-safe fields may remain in the same version only when old agents can ignore them safely.
- The adapter must reject unsupported request/response versions with a provider-level error and safe fallback.
- The version is not an auth, permission, or sandbox guarantee.

## Future Request Shape

A future external agent request should be a JSON-serializable object shaped like:

```json
{
  "schema_version": "external-agent.v0",
  "request_id": "uuid-or-engine-generated-id",
  "game_id": "g1",
  "hand_id": "h1",
  "seat": {
    "player_name": "AI-1",
    "position": 0
  },
  "state": {
    "phase": "flop",
    "private_hole_cards": ["A♠", "K♠"],
    "community_cards": ["2♣", "7♦", "Q♥"],
    "pot_size": 150,
    "current_bet": 40,
    "amount_to_call": 20,
    "player_chips": 980,
    "public_players": [
      {
        "name": "AI-1",
        "chips": 980,
        "current_bet": 20,
        "is_folded": false,
        "is_all_in": false,
        "position": 0
      }
    ],
    "action_history": [
      {"phase": "preflop", "player_name": "AI-2", "action": "raise", "amount": 40}
    ],
    "legal_actions": ["fold", "call", "raise"],
    "min_raise": 80,
    "dealer_position": 0,
    "small_blind": 5,
    "big_blind": 10
  },
  "constraints": {
    "timeout_ms": 2000,
    "requires_action_in": ["fold", "call", "raise"],
    "amount_units": "chips"
  }
}
```

Request rules:

- `state` must be derived from `ExternalAgentState`, not directly from live engine objects.
- `private_hole_cards` belongs only to the acting seat named in `seat.player_name`.
- `public_players` must not contain any player hand, hole-card, deck, or hidden evaluator state.
- `action_history` must be public action history only. It may include phase, player name, action, amount, and public metadata, but must exclude `deck`, `hole_cards`, `opponent_hole_cards`, `private_ai_internals`, unsafe random state, or hidden-card assumptions.
- `legal_actions` is authoritative for action names the agent may choose from, but amount legality is still validated by `validate_action(...)`.
- `constraints.timeout_ms` is an adapter budget, not a poker rule.

## Future Response Shape

A future external agent response should be JSON-serializable and shaped like:

```json
{
  "schema_version": "external-agent.v0",
  "request_id": "uuid-or-engine-generated-id",
  "action": "raise",
  "amount": 120,
  "metadata": {
    "summary": "Raising with initiative on a dry flop.",
    "tags": ["pressure"]
  }
}
```

Response rules:

- `action` must be a string and must appear in the request's `state.legal_actions` before it can be accepted by the adapter.
- `amount` must be numeric or safely coercible to an integer chip amount. `validate_action(...)` remains responsible for min/max/call/all-in normalization.
- `metadata` is optional and must be treated as public unless a future private metadata contract is documented and tested.
- `metadata` must be JSON-safe and must not include deck order, hidden-card assumptions, opponent private cards, unsafe seeds, raw model prompts containing hidden state, stack traces with hidden state, or non-serializable runtime objects.
- `raw_response` may be retained internally for diagnostics only if filtered before public reports.

## Timeout and Error Behavior

Future adapters must fail closed into existing safe action behavior.

Required behavior:

- Timeout: return `ActionResponse(error="external_agent_timeout", metadata={"fallback": true, "provider": ...})` and let `validate_action(...)` choose a safe fallback check/fold if needed.
- Unsupported version: return a provider error and safe fallback.
- Malformed JSON or missing response fields: return a provider error and safe fallback.
- Action not in `legal_actions`: preserve the original action in diagnostic fields when safe, but route through `validate_action(...)` for fallback.
- Invalid amount: route through `validate_action(...)`; never mutate engine state from an unvalidated amount.
- Adapter exception: catch it at the provider boundary and return an `ActionResponse` with `error`, not a game-loop crash.

Timeout/error metadata may include public operational facts such as provider name, timeout class, elapsed milliseconds, or schema version. It must not include hidden card state or raw private payloads.

## Legal-Action Dependency

The future external agent contract must treat legal actions as a dependency, not advice.

- The request must include `legal_actions` from the decision-time snapshot.
- The adapter should pre-check that the returned `action` is in `legal_actions`.
- `validate_action(...)` remains mandatory even after adapter pre-checks.
- If `legal_actions` is missing, empty, or malformed, the adapter must reject the response path and use safe fallback rather than asking the external agent to infer legality.
- Future external agents must not be allowed to introduce new action names outside the engine vocabulary: `fold`, `check`, `call`, `raise`, and `all-in` unless the engine and validator contract are updated first.

## Seat-Scoped Visibility

Visibility is seat-scoped at the request boundary:

- One request is for one acting seat only.
- The request may include that seat's `private_hole_cards`.
- The request must not include any unrevealed opponent hole cards.
- The request must not include folded/non-showdown cards, deck order, future board cards, or private AI internals.
- Showdown reveals may appear only after a valid showdown event or hand-result contract proves those cards became public.
- Any future `private_payload_by_player` delivery must be keyed by stable seat identity and tested for no cross-seat leakage before use.

## Serialization Rules

External-agent request/response payloads must be JSON-compatible:

- Strings, numbers, booleans, nulls, arrays, and objects only.
- Cards represented as stable display strings until a separate card schema is documented.
- No Python `Card`, `Player`, `Deck`, exception, model client, provider, or database objects.
- No non-deterministic object repr strings in public reports.
- Standard `json.dumps(..., ensure_ascii=False)` should succeed for request, response, and gate/report artifacts.

## Non-Implementation Notes

This contract deliberately does not choose:

- Transport: HTTP, WebSocket, stdio, MCP, subprocess, or hosted-agent bridge.
- Auth and authorization model.
- Sandbox or resource isolation model.
- External marketplace packaging.
- Multi-agent room orchestration.
- Public API stability or deployment target.

Those are platform decisions and should not begin until Phase 2 visibility tests, benchmark gates, external-agent stubs, and platform non-goals are all documented and stable.

## Validation Hooks

Current and future tests should protect this contract by verifying:

- `ExternalAgentState.to_dict()` contains public state plus only the acting seat's private hand.
- Serialized state excludes unrevealed opponent cards, deck order, unsafe seeds, and private AI internals.
- Benchmark gate evaluation fails on unsafe transcript leaks and malformed protocol metadata.
- Future adapter tests convert timeout, malformed response, unsupported version, illegal action, and invalid amount into `ActionResponse` plus `validate_action(...)` fallback.
