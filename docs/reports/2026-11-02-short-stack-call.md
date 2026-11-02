# Strong-hand short-stack calls

Date: 2026-11-02

## Accepted fix

Astra reproduced a concrete defect through the real provider and validator: Hero holds A♥K♥ on Q♥J♥T♥2♣3♦, has 50 chips left, faces 100 with a 300-chip pot and minimum raise total of 200. The old AI either folded directly because it could not match 100, or attempted `raise 50` and was rejected by the provider, falling back to fold. The existing rules already allow `call 50`.

The AI sizing helper now returns no raise when the maximum total investment is at or below the current table wager. In the two existing postflop strong-hand branches (equity at least 60%), a positive remaining stack can call `min(amount_to_call, remaining_chips)`. A genuine short all-in raise above the current wager remains possible. Rules, validator, state schemas, medium/weak-hand price logic and profile frequencies were not changed.

## Why this slice

The preceding ten-player position repair reduced mean decision score from 72.4925 to 71.8246. Existing public audit samples do not establish that newly reachable postflop bluffs caused this:

| Sample category | Before position repair | After position repair |
| --- | ---: | ---: |
| Preflop low-equity raise/bluff labels | 17 | 30 |
| Pot-odds call mistake labels, all phases | 17 | 27 |
| Overfold labels, all phases | 5 | 11 |
| Postflop low-equity bluff labels | 0 | 0 |

The recorded samples total 39 and 68 respectively; the latter includes a run truncated at the 25-sample cap. These are sample counts, not full population estimates. Full grade distributions show poor grades 38→71 and blunders 1→1. Five equity rollouts also give coarse individual equity estimates.

Astra found three recorded turn folds with estimated equity 1.0, but these sanitized records omit remaining chips. They motivated the deterministic short-stack fixture, not a claim that this defect explains those specific hands or the aggregate score change. The calibration report targets only four existing profile families, even though ten-player simulations include all six personas. Fixed facing-bet bluff frequencies were not retuned on this evidence.

## Validation

- Astra focused tests: **196 passed**.
- Independent full suite: `python3 -m pytest -q` → **499 passed**.
- New `tests/test_short_stack_ai_calls.py`: **110 cases** covering six profiles, 60%/75% branch boundaries, raise/call random rolls, insufficient/exact stacks, prior investment, a real-equity royal flush, table-wager-plus-one legal short raises, weak-hand folds, ordinary calls paying only the price, and zero stacks. Assertions check raw AI actions, absence of provider errors/fallbacks, and acceptance by the unchanged validator.
- `git diff --check` passed.
- Primary: seeds 0–9 × 500 hands, four players, 10,000 starting chips, five equity rollouts: **PASS**, all **5,000 hands** complete, zero illegal actions and zero runtime errors.
- Ten-player diagnostic: seeds 0–2 × 100 hands, same other settings: **PASS** against its explicitly reduced protocol, all **300 hands** complete, zero illegal actions and zero runtime errors.

Independent seeds ran in isolated Python processes, with the existing evaluator, `_summarize_seed_runs` aggregation and `evaluate_benchmark_gates` checks. Metric definitions and gate thresholds were unchanged.

## Comparison with the actual-position repair

Means across seeds:

| Metric | Four-player before | Four-player after | Ten-player before | Ten-player after |
| --- | ---: | ---: | ---: | ---: |
| Average decision score | 72.7696 | 72.7849 | 71.8246 | 72.3562 |
| Style separability | 0.3544 | 0.3602 | 0.2823 | 0.2917 |
| Calibration distance (lower is better) | 0.0804 | 0.1037 | 0.0948 | 0.0497 |

The correction passes both gates and improves scores in these samples, but four-player calibration distance worsens. No universal calibration or playing-strength claim is made. Ten-player evidence remains a 300-hand diagnostic; five-rollout simulations do not predict exact action frequencies with the normal 500-rollout equity setting. Correct short-stack play is demonstrated directly by the real-entry fixtures rather than inferred from aggregate scores.

Artifacts:

- [Primary](2026-11-02-short-stack-call-primary.json), [evaluation](2026-11-02-short-stack-call-primary-evaluation.json).
- [Ten-player diagnostic](2026-11-02-short-stack-call-ten-player.json), [evaluation](2026-11-02-short-stack-call-ten-player-evaluation.json).

Baseline artifacts are the corresponding `2026-10-30-actual-position-*` reports. To reproduce use `benchmark_ai_system_multi_seed()` for primary or `benchmark_ai_system_multi_seed(seeds=[0,1,2], hands_per_seed=100, player_count=10)` for the diagnostic and evaluate against its declared protocol.
