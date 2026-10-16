# Phase 3 Calling-Station Negative-Equity Call Tuning

Date: 2026-05-22

## Summary

This slice follows the public-context pot-odds audit split. The audit showed that sampled `pot-odds call mistake` cases were true negative-equity calls rather than obvious evaluator false positives, with a strong concentration in the `calling_station` profile.

The change is intentionally narrow in two steps:

1. when a profiled AI is facing a flop continuation bet with weak air, no draw, and equity is clearly below the public pot price, the profile stickiness branch no longer forces a call;
2. after reviewing the remaining post-tuning samples, when `calling_station` faces a preflop raise with a non-premium hand and public equity is below the pot price by more than 0.04, the high call-bias fallback folds instead of calling.

This does not change benchmark thresholds, evaluator scoring, public/private contracts, online/API/WebSocket/auth scope, or general calling-station identity.

## What changed

`advanced_ai_engine.py` now computes a postflop `equity_far_below_price` guard in facing-bet spots:

```text
equity <= pot_odds - 0.25
```

That guard is applied only to the profiled flop c-bet stickiness override. A calling station can still be stickier than TAG/nit profiles in ordinary weak-air c-bet spots, but it should not call when public decision-time equity is dramatically below the price.

The follow-up sample review found a second shared public pattern in the post-tuning artifact: all 21 remaining `calling_station` `true_negative_equity_call` samples were calls with the `negative_pot_odds_call` risk tag; 16/21 were preflop, with public pot odds from 0.195 to 0.400 and equity edge from -0.1913 to -0.0438. The second guard is therefore limited to `calling_station` preflop raise-facing spots where the hand is non-premium and equity is clearly negative versus price:

```text
current_bet > 10
profile == calling_station
equity < pot_odds - 0.04
not premium
```

## Focused regression fixture

Added focused fixtures:

- `tests/test_ai_tuning.py::test_calling_station_folds_postflop_air_when_equity_clearly_below_pot_odds`
- `tests/test_ai_tuning.py::test_calling_station_folds_nonpremium_preflop_raise_when_equity_negative_price`

The RED run failed as expected before the policy guard:

```text
E       AssertionError: assert ('call', 50) == ('fold', 0)
E       AssertionError: assert ('call', 22) == ('fold', 0)
```

After the minimal guards, the focused file passes:

```text
7 passed in 0.02s
```

A broader AI/evaluator regression set passes:

```text
101 passed in 5.72s
```

This includes `tests/test_ai_scenario_sanity.py`, preserving the existing expectation that calling stations still fold less often than tighter profiles in less extreme weak-air c-bet spots.

## Updated reduced post-tuning artifact

Generated:

- `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json`
- `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.progress.json`
- `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark-evaluation.json`

Protocol:

```text
10 seeds × 100 hands
player_count = 4
starting_chips = 10000
ai_equity_simulations = 5
```

Gate status against the explicit reduced protocol:

```text
PASS
```

Key benchmark summary:

| Metric | Before audit artifact | Post-tuning artifact |
|---|---:|---:|
| average decision score mean | 72.7313 | 72.9862 |
| average decision score min | 72.1245 | 72.2222 |
| average decision score max | 73.1433 | 73.4727 |
| pot-odds call mistake samples | 33 | 18 |
| calling-station pot-odds samples | 23 | 11 |
| evaluator false-positive candidates | 0 | 0 |

Post-tuning poor/blunder sample classes:

| Classification | Count |
|---|---:|
| pot-odds call mistake | 18 |
| overfold | 13 |
| low-equity bluff | 3 |

Post-tuning pot-odds audit split:

| Split | Count |
|---|---:|
| true_negative_equity_call | 18 |
| evaluator_false_positive_candidate | 0 |
| insufficient_public_context | 0 |

Post-tuning pot-odds sample concentration by profile:

| Profile | Count |
|---|---:|
| calling_station | 11 |
| nit | 4 |
| tight_aggressive | 3 |
| loose_aggressive | 0 |

## Interpretation

The reduced artifact shows a larger improvement in the targeted diagnostic class after the second narrow preflop guard, without weakening gates or broadening the evaluator. It is still not enough evidence to claim broad AI strength improvement.

Recommended next step: if continuing tuning, inspect the remaining `calling_station` true-negative pot-odds samples from the refreshed post-tuning artifact and add another focused fixture only if they share a public, decision-time pattern. Avoid broad threshold changes. In parallel, the evaluation loop can now split Builder/Hacker roles: Builder creates a contract-safe AI Player candidate, while Hacker adversarially searches for public-information exploits and hands only reproducible regression targets back to Builder.

## Verification

Commands run:

```bash
python3 -m pytest tests/test_ai_tuning.py::test_calling_station_folds_nonpremium_preflop_raise_when_equity_negative_price -q
```

Observed RED before the second guard:

```text
1 failed
E       AssertionError: assert ('call', 22) == ('fold', 0)
```

```bash
python3 -m pytest tests/test_ai_tuning.py -q
```

Observed:

```text
7 passed in 0.02s
```

```bash
python3 -m pytest -q tests/test_ai_tuning.py tests/test_ai_scenario_sanity.py tests/test_decision_provider.py tests/test_ai_system_evaluator.py
```

Observed after the second guard:

```text
101 passed in 5.72s
```

```bash
python3 -m pytest -q
```

Observed:

```text
276 passed in 31.81s
```

Reduced post-tuning benchmark generation observed after the second guard:

```text
status PASS
avg_score_summary {'mean': 72.9861596563484, 'std': 0.3177476134151951, 'min': 72.22222222222223, 'max': 73.47272727272727}
poor_blunder_classes {'pot-odds call mistake': 18, 'overfold': 13, 'low-equity bluff': 3}
pot_odds_audit_splits {'true_negative_equity_call': 18}
pot_odds_profiles {'calling_station': 11, 'nit': 4, 'tight_aggressive': 3}
```


## Loop-closure addendum: measurable target reached

After the user requested a goal-driven loop, the target was set to continue Builder/Hacker-style review until the reduced `10 seeds × 100 hands` artifact met all of these conditions:

- gate `status == PASS`;
- `calling_station` `true_negative_equity_call` pot-odds samples `<= 5`;
- total `pot-odds call mistake` samples `<= 10`;
- no public/private safety regression;
- full test suite passes.

Loop 1 Hacker identified a real public decision-time pattern in `calling_station` small preflop negative-price calls. Builder added `tests/test_ai_tuning.py::test_calling_station_folds_blind_price_preflop_when_equity_below_pot_odds` and a narrow non-premium small-price guard. This reduced `calling_station` pot-odds samples to target range, but total pot-odds samples remained 14.

Loop 2 initially investigated a `nit` preflop cluster. Reconstructing the benchmark hands showed this was mostly a low-rollout evaluator artifact on strong preflop hands such as AA, AQ, AJ, JJ, and KK rather than a policy defect. The policy-side nit guard was therefore removed. The accepted fix was evaluator-side: strong preflop calls are no longer flagged as `negative_pot_odds_call` from noisy raw equity alone, while non-strong pairs can still be flagged.

Final reduced benchmark regeneration:

```text
status PASS
avg_score_summary {'mean': 72.94647386549948, 'std': 0.2913088254686317, 'min': 72.34375, 'max': 73.49090909090908}
poor_blunder_classes {'overfold': 12, 'low-equity bluff': 4, 'pot-odds call mistake': 6}
pot_odds_audit_splits {'true_negative_equity_call': 6}
pot_odds_profiles {'tight_aggressive': 2, 'nit': 2, 'calling_station': 2}
TARGET_STATUS True
TARGET_CALLING_STATION<=5 True
TARGET_TOTAL_POT_ODDS<=10 True
```

Additional verification:

```text
python3 -m pytest -q tests/test_decision_evaluator.py::test_preflop_strong_hand_call_is_not_negative_pot_odds_from_noisy_equity tests/test_decision_evaluator.py::test_preflop_non_strong_pair_call_can_still_be_negative_pot_odds
# RED before evaluator fix: 1 failed, 1 passed

python3 -m pytest -q tests/test_decision_evaluator.py::test_preflop_strong_hand_call_is_not_negative_pot_odds_from_noisy_equity tests/test_decision_evaluator.py::test_preflop_non_strong_pair_call_can_still_be_negative_pot_odds tests/test_decision_evaluator.py tests/test_ai_tuning.py
# 43 passed

python3 -m pytest -q tests/test_ai_system_evaluator.py tests/test_decision_provider.py
# 39 passed

python3 -m pytest -q
# 279 passed
```

Interpretation: the explicit reduced-artifact loop target is reached. This is evidence of improved evaluator/policy consistency for the targeted diagnostic class, not a claim of broad poker strength.
