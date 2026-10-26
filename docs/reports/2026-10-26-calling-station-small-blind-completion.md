# Calling-station small-blind completion, 2026-10-26

## Decision

Keep a small-blind-only preflop exception for the built-in `calling_station` profile. When its normal entry range would fold, it may complete the small blind if it can pay the call and estimated equity meets or exceeds the public pot-odds price. The existing negative-price guards still apply. Other positions, archetypes, postflop policy, poker legality, and benchmark metric definitions remain unchanged.

## Diagnosis

In a 300-hand seed-0 diagnostic before this change, the calling-station profile folded 52 times in the small blind; 50 of those folds came from the entry-range threshold. The same diagnostic showed high-price folds at the cutoff and button, where a wider call would be less defensible. This candidate therefore widens only the cheaper small-blind completion spot.

A reduced 10-seed × 100-hand screen completed all 1,000 hands with zero illegal actions. Its calling-station means were VPIP 32.9%, call rate 31.22%, fold rate 35.99%, and poor/blunder rate 1.31%. These are diagnostic figures; the primary comparison below is the acceptance evidence.

## Primary comparison

Both artifacts use seeds 0–9, 500 requested hands per seed, four AI players, 10,000 starting chips, and five equity simulations per AI decision. Values are arithmetic means of per-seed profile metrics.

| Measure | Previous accepted policy | Small-blind completion |
| --- | ---: | ---: |
| Primary gate | PASS | PASS |
| Hands completed | 5,000 | 5,000 |
| Illegal action rate | 0 | 0 |
| Calling-station VPIP | 22.80% | 35.11% |
| Calling-station call rate | 27.33% | 32.10% |
| Calling-station fold rate | 46.05% | 32.81% |
| Calling-station aggression factor | 0.5328 | 0.5705 |
| Calling-station poor/blunder rate | 1.34% | 1.32% |
| Calling-station average decision score | 72.59 | 72.20 |
| Style separability score | 0.3096 | 0.3473 |

All ten seeds completed 500 hands and the full automated suite passed 318 tests. The new regression verifies that the calling station completes a small blind with an outside-range hand only when the price is covered, while a nit still folds and negative-price calls remain folds.

The profile calibration remains WARN. VPIP passed its 30–50% band in all ten seeds, and fold rate passed its ceiling in eight seeds. Call rate missed the 45% floor in all ten seeds; showdown rate also remained below its target in all ten seeds. Average decision score fell by about 0.39 points while poor/blunder rate stayed approximately flat. This supports more recognizable passive play under the existing primary gate; it does not establish fully calibrated or stronger poker play.

## Artifacts

- Previous accepted policy: `2026-10-26-calling-station-call-over-raise-primary.json`.
- New primary benchmark: `2026-10-26-calling-station-small-blind-completion-primary.json`.
- Gate evaluation: `2026-10-26-calling-station-small-blind-completion-primary-evaluation.json`.
