# Phase 3 Stage 3.4 Public/Private Safety Gate

Date: 2026-05-16

## Summary

Stage 3.4 promotes public/private safety from ad-hoc transcript sample review toward an explicit contract gate for future external-agent and online-room surfaces. This remains local evidence-hardening work only: no WebSocket/API/auth/account/external-agent runtime implementation was added.

## Scope

Implemented as an additive safety-contract slice in `ai_system_evaluator.py` and `tests/test_ai_system_evaluator.py`:

- Benchmark reports now expose a machine-readable public transcript schema marker.
- Benchmark reports now expose a showdown reveal policy.
- Gate safety checks now inspect sanitized poor/blunder audit samples in addition to transcript sample text.
- Regression tests cover non-showdown winner privacy, showdown reveal behavior, folded-player exclusion, all-in transcript shape, side-pot/showdown-like transcript shape, early-winner privacy, and deliberate audit-sample leakage failure.

## Public transcript schema

Current schema payload emitted by `AISystemEvaluationReport.to_dict()`:

```json
{
  "version": "phase3.4-public-transcript-v1",
  "sample_fields": ["hand_number", "text", "flags"],
  "allowed_private_cards": "only legally revealed showdown contestants",
  "forbidden_fields": ["deck", "hole_cards", "opponent_hole_cards", "private_ai_internals", "unsafe_seed"]
}
```

## Showdown reveal policy

```json
{
  "showdown": "reveal only players who legally reached showdown",
  "non_showdown": "do not reveal any private hole cards",
  "folded_players": "never reveal folded/non-contesting players' private cards"
}
```

## Safety cases covered

| Case | Coverage |
|---|---|
| Fold-only / early winner | Transcript result can name the winner, but must not reveal winner or opponent private cards when `went_to_showdown` is false. |
| Showdown | Transcript may reveal only legal showdown contestants' hole cards and hand ranks. |
| Folded player in showdown hand | A player with `hand_rank: folded` must not appear in the showdown reveal segment and their cards must not leak. |
| All-in | Transcript can include public all-in action text and still apply normal showdown/non-showdown reveal policy. |
| Side-pot / all-in-like showdown | Transcript can include multiple showdown contestants while excluding folded/non-contesting players. |
| Audit sample leak | Benchmark gate fails if `poor_blunder_samples` contain forbidden private-state tokens. |

## Gate integration

`evaluate_benchmark_gates(...)` retains the existing `transcript_safety` gate name, but the check now covers two public artifact families:

1. `transcript_samples[*].text`
2. serialized `poor_blunder_samples`

Forbidden tokens:

- `deck`
- `hole_cards`
- `opponent_hole_cards`
- `private_ai_internals`
- `unsafe_seed`

A hostile benchmark fixture with `poor_blunder_samples=[{"reason": "hole_cards A♥ K♥"}]` now fails with:

```text
forbidden token in poor_blunder_samples: hole_cards
```

## Verification

Focused Stage 3.4 tests:

```bash
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_public_transcript_schema_and_showdown_policy_are_reported tests/test_ai_system_evaluator.py::test_benchmark_gate_fails_for_audit_sample_private_state_leaks
python3 -m pytest -q tests/test_ai_system_evaluator.py::test_public_transcript_safety_covers_all_in_side_pot_and_early_winner_shapes tests/test_ai_system_evaluator.py
```

Observed focused result:

```text
25 passed in 3.23s
```

Final full-suite validation after documentation/index updates:

```text
272 passed in 34.61s
```

Markdown index path validation:

```text
indexed paths ok
```

## Stage 3.5 handoff

Stage 3.5 should define the repeatable evaluation-agent loop templates and run one complete loop over an existing benchmark artifact. The coordinator should preserve the Phase 3 guardrail: no claims of AI improvement without pre/post evidence, and no platform/runtime implementation before the evaluation loop is stable.
