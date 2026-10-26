# Benchmark Gates

Date: 2026-05-12

## Purpose

This document defines Phase 2 benchmark acceptance gates for the local Texas Hold'em trainer. These gates decide whether the current local AI trainer benchmark artifact is complete, reproducible, safe to inspect, and useful enough for trainer-quality review before any online room, WebSocket, public external-agent API, auth, or platform work begins.

These benchmark gates are local trainer quality gates and diagnostics. They are not solver validation, GTO proof, real-money readiness, online-platform certification, external-agent marketplace certification, or platform security certification.

## Current Module Boundaries

- `texas_holdem/analytics/headless_simulation.py` executes local AI-only simulations through `run_ai_only_simulation(num_hands, player_count, starting_chips, seed, collect_events)`. It owns hand execution, temporary history/stat isolation, final stacks, hand summaries, and optional engine-event collection.
- `texas_holdem/analytics/ai_system_evaluator.py` summarizes simulations through `evaluate_ai_system(...)`, `benchmark_ai_system(...)`, and `benchmark_ai_system_multi_seed(...)`. It owns report shape, aggregate metrics, JSON artifact writing, profile metrics, stack metrics, seeded/multi-seed reports, and transcript samples.
- `texas_holdem/ai/action_validator.py` remains the legality and fallback boundary. Benchmark gates may consume illegal-action metrics, but they do not redefine No-Limit Hold'em legality.
- `texas_holdem/ai/decision_provider.py` remains the decision abstraction boundary. Benchmark gates evaluate provider behavior only through existing simulation/evaluator outputs.
- `texas_holdem/engine/engine_events.py` remains the event boundary. Benchmark gates may require transcript/event safety, but this document does not introduce new event semantics.
- `docs/architecture/public-private-state-contract.md` remains the visibility source of truth. Transcript/report safety gates reference that contract and must not weaken it.

## Gate Categories

| Category | Meaning |
| --- | --- |
| `PASS` | All blocking product gates pass; trainer-quality gates meet pass thresholds or only non-blocking diagnostics are outside target range. |
| `WARN` | Blocking product gates pass, but one or more trainer-quality warning thresholds or diagnostics need review. |
| `FAIL` | Any blocking product gate fails: incomplete runs, runtime errors, illegal actions, missing required metrics, unsafe transcript content, malformed JSON, or missing benchmark metadata. |
| `NOT_RUN` | Required benchmark artifact is absent, stale, unreadable, or uses protocol metadata that does not match the required gate protocol. |

Slice 2.2 defines the gates only. Machine-readable `PASS` / `WARN` / `FAIL` / `NOT_RUN` evaluation belongs to a later implementation slice.

## Primary Product Gate Protocol

The primary Phase 2 benchmark acceptance protocol is a deterministic multi-seed local benchmark:

```python
from texas_holdem.analytics.ai_system_evaluator import benchmark_ai_system_multi_seed

benchmark_ai_system_multi_seed(
    seeds=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    hands_per_seed=500,
    player_count=4,
    starting_chips=10000,
    output_path="docs/reports/YYYY-MM-DD-phase2-ai-benchmark-gates.json",
)
```

Required protocol values:

| Field | Required value |
| --- | --- |
| Seeds | `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]` |
| Hands per seed | `500` |
| Total requested hands | `5,000` |
| Player count | `4` |
| Starting chips | `10,000` |
| Artifact type | JSON returned by `benchmark_ai_system_multi_seed(...)` |
| Runtime scope | Local headless trainer benchmark only |

Reasoning:

- Multi-seed acceptance reduces the chance that one lucky or unlucky run drives a product decision.
- `starting_chips=10000` reduces premature benchmark termination from early bustouts while preserving the current local trainer structure.
- `player_count=4` matches the existing benchmark convention and current Phase 1/Phase 2 evaluation surface.
- The protocol uses existing benchmark functions and does not change metric definitions.

## Optional Smoke Protocol

A single-seed smoke benchmark may be used for quick local sanity checks:

```python
from texas_holdem.analytics.ai_system_evaluator import benchmark_ai_system

benchmark_ai_system(
    num_hands=100,
    player_count=4,
    starting_chips=10000,
    seed=0,
    output_path="docs/reports/YYYY-MM-DD-phase2-ai-benchmark-smoke.json",
)
```

The smoke protocol is diagnostic only. It must not replace the primary multi-seed product gate.

## Blocking Product Gates

These gates must pass before a benchmark artifact can be accepted as Phase 2 local trainer evidence.

| Gate | Acceptance threshold |
| --- | --- |
| Completion | Every primary run completes exactly `500` hands. Any early stop, including bustout-driven early termination, fails the gate. |
| Runtime errors | Every run has `errors == []`. Any runtime error fails the gate. |
| Action coverage | Every run has `total_actions > 0`. Zero-action runs fail. |
| Illegal action rate | Every run has `illegal_action_rate == 0.0`. Any illegal action fails because legality is a core product boundary, not a tuning issue. |
| Required top-level metrics | Every run includes JSON-serializable `hands_played`, `total_actions`, `illegal_action_rate`, `average_decision_score`, `grade_distribution`, `final_stacks`, `errors`, `player_metrics`, `profile_metrics`, `weakest_profile`, `style_separability_score`, `vpip_spread`, `pfr_spread`, `aggression_spread`, `call_rate_spread`, `largest_stack_share`, `bustout_rate`, `hands_until_first_bust`, `stack_gini`, `transcript_samples`, and `benchmark`. |
| Player metrics | `player_metrics` contains entries for players that appeared in the run and exposes the existing VPIP, PFR, aggression, call, fold, showdown, win, poor/blunder, average-score, and counter fields. Missing or non-numeric fields fail. |
| Profile metrics | `profile_metrics` is present and non-empty when profile data exists. Missing profile aggregation fails for the current built-in AI benchmark. |
| Multi-seed summary | The multi-seed artifact includes `summary` with `mean`, `std`, `min`, and `max` for the current numeric summary metrics. |
| Benchmark metadata | Artifact metadata records seeds, hands per seed, player count, starting chips, and generated timestamp. Missing or mismatched protocol metadata yields `NOT_RUN` or `FAIL`. |
| Transcript availability | Each completed run has `1 <= len(transcript_samples) <= 3`. Empty samples fail when hands completed is non-zero. |
| Transcript safety | Transcript text must not expose deck order, undealt cards, future board cards, folded/non-showdown hole cards, opponent private cards, private AI internals, or unsafe hidden-state fields. Any leak fails. |
| JSON safety | The artifact must serialize with standard JSON output and must not contain runtime objects, card objects, provider objects, exception instances, or non-serializable private state. |

## Trainer-Quality Gates

These gates support local trainer confidence, but they remain heuristic. They are based on the current evaluator and should not be described as poker-theory proof.

| Gate | PASS | WARN | FAIL |
| --- | --- | --- | --- |
| Average decision score mean | `average_decision_score.mean >= 60.0` | `55.0 <= mean < 60.0` | `mean < 55.0` |
| Average decision score floor | `average_decision_score.min >= 50.0` | `45.0 <= min < 50.0` | `min < 45.0` |
| Poor/blunder rate | Mean derived from available player/profile metrics is `<= 0.30` | `> 0.30` and `<= 0.40` | `> 0.40` |
| Stack concentration | `largest_stack_share.mean <= 0.85` | `> 0.85` and `<= 0.95` | Blocking only if paired with completion failure or high bustout pressure. |
| Bustout pressure | `bustout_rate.mean <= 0.25` | `> 0.25` and `<= 0.50` | Blocking only if completion is affected. |

The hard product gates above take priority. For example, a benchmark with strong decision scores but one illegal action is `FAIL`, not `WARN`.

## Observational Diagnostics

These metrics are useful for AI tuning, product review, and future benchmark refinement, but they do not block Phase 2 acceptance by themselves:

- `vpip_spread`
- `pfr_spread`
- `aggression_spread`
- `call_rate_spread`
- `style_separability_score`
- `weakest_profile`
- `largest_stack_share` when completion is unaffected
- `bustout_rate` when completion is unaffected
- `hands_until_first_bust`
- `stack_gini`
- Individual player win rates
- Individual profile win rates
- Transcript flags such as `c-bet`, `fold-to-cbet`, and `no-obvious-issue`

These diagnostics are variance-sensitive and depend on the current AI archetype mix, blind structure, stack depth, and evaluator heuristics. Use them to guide later tuning, not to claim GTO strength.

## Transcript Safety Rules

Benchmark transcript samples are public-facing review artifacts. They must follow `docs/architecture/public-private-state-contract.md`.

Allowed transcript content:

- Hand number.
- Public board cards after they are dealt.
- Public actions, amounts, winners, total pot, and public winner reason.
- Showdown hole cards only when `outcome_metadata["went_to_showdown"] is True` or an equivalent future event proves showdown.
- Public-safe tags such as `c-bet`, `fold-to-cbet`, and `no-obvious-issue`.

Forbidden transcript content:

- Deck order or undealt cards.
- Future community cards before they are dealt.
- Folded or non-showdown hole cards.
- Opponent private cards before a valid showdown reveal.
- Private AI internals, raw hidden-card assumptions, search state, or fields named like `deck`, `hole_cards`, or `opponent_hole_cards` outside valid showdown reveals.
- Unsafe live random-state data that could reconstruct hidden state.

## Artifact Expectations

A primary multi-seed benchmark artifact should be stored under `docs/reports/` when generated for a durable review, for example:

```text
docs/reports/YYYY-MM-DD-phase2-ai-benchmark-gates.json
```

The artifact must include:

- `benchmark.hands_per_seed`
- `benchmark.player_count`
- `benchmark.starting_chips`
- `benchmark.seeds`
- `benchmark.generated_at`
- `summary` with mean/std/min/max numeric rollups
- `runs` with per-seed report dictionaries
- Per-run `benchmark` or seed metadata sufficient to connect each run to its seed
- Required top-level metrics and transcript samples described above

Older benchmark artifacts may remain historical evidence, but a Phase 2 gate must be evaluated against a fresh artifact generated by the current evaluator shape.

## Non-Goals

The benchmark gates do not implement or certify:

- Online poker rooms.
- WebSocket servers.
- Public external-agent API endpoints.
- Auth, user accounts, permissions, rate limits, or sandboxing.
- Real-money play, payments, balances, custody, or compliance systems.
- Solver validation or GTO correctness.
- Human professional poker skill claims.
- Platform security, multi-tenant isolation, or adversarial external-agent safety.

## Future Slice 2.5 Implementation Guidance

A later implementation slice should add machine-readable gate evaluation and tests without changing the Phase 2.2 definitions silently.

Suggested future gate result shape:

```json
{
  "gate_version": "phase2.2",
  "status": "PASS|WARN|FAIL|NOT_RUN",
  "protocol": {
    "seeds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    "hands_per_seed": 500,
    "player_count": 4,
    "starting_chips": 10000
  },
  "checks": [
    {
      "name": "illegal_action_rate",
      "status": "PASS",
      "threshold": "== 0.0",
      "observed": 0.0
    }
  ]
}
```

Future tests should cover:

- `PASS`, `WARN`, `FAIL`, and `NOT_RUN` classification.
- Incomplete hands fail.
- Non-empty errors fail.
- Any illegal action rate above zero fails.
- Missing required metrics fail.
- Missing seed/player/stack metadata fails.
- Transcript samples reject hidden-card, deck-order, and private-internal leaks.
- JSON artifacts remain machine-readable and public/private safe.
