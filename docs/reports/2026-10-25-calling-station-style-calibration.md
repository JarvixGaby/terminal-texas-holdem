# Calling-station style calibration, 2026-10-25

## Decision

Keep a narrow preflop-only adjustment for the built-in `calling_station` profile. It lowers that profile's passive entry threshold, raises its chance to call after selecting a playable hand, and gives close blind/raise prices a wider tolerance. The existing guards still fold clearly negative prices. No poker legality rule, public agent contract, benchmark metric definition, or other archetype profile changed.

The first candidate also let the profile call close postflop prices more often. Reject that candidate: its primary benchmark ended early in seeds 0, 1, and 3, so the completion gate failed. That postflop branch was removed before the accepted run.

## Evidence

All three runs used the same primary protocol: seeds 0–9, 500 requested hands per seed, four AI players, 10,000 starting chips, and five equity simulations per AI decision. Values below are means across the ten seeds, not pooled action rates.

| Measure | 2026-10-15 baseline | Rejected preflop + postflop | Kept preflop-only |
| --- | ---: | ---: | ---: |
| Primary gate | PASS | FAIL (completion) | PASS |
| Hands completed | 5,000 | 4,613 | 5,000 |
| Calling-station VPIP | 14.22% | 22.52% | 22.98% |
| Calling-station call rate | 17.51% | 25.91% | 24.31% |
| Calling-station fold rate | 55.71% | 40.65% | 44.48% |
| Calling-station poor/blunder rate | 0.69% | 1.84% | 1.74% |
| Calling-station average decision score | 73.03 | 72.98 | 72.83 |
| Style separability score | 0.2500 | 0.2911 | 0.2817 |
| Illegal action rate | 0 | 0 | 0 |

The rejected run stopped at hands 345, 374, and 394 for seeds 0, 1, and 3. The kept run completed every seed. Full automated suite: 315 passed. The new focused regression verifies a playable suited king is called by this profile at a close late-position blind price while the nit profile folds; existing negative-price fixtures still pass.

The profile's own calibration status remains WARN in every seed. Its call-rate target begins at 45%, VPIP target at 30%, and fold-rate ceiling is 35%; the kept policy does not meet those bands. This is a measurable style improvement, not a fully calibrated calling station or a claim of stronger poker play. The slightly higher poor/blunder rate and lower decision score are tradeoffs to watch in the next fixture-backed tuning slice.

## Artifacts

- Baseline: `2026-10-15-companion-position-primary-benchmark.json`.
- Rejected candidate: `2026-10-25-calling-station-style-calibration.json` and its `-evaluation.json` gate result.
- Kept candidate: `2026-10-25-calling-station-preflop-only-primary.json` and its `-evaluation.json` gate result.
