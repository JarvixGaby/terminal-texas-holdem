# Calling-station call-over-raise repair, 2026-10-26

## Decision

Keep a narrow postflop policy change for the built-in `calling_station` profile: when facing a bet with estimated equity of at least 60%, prefer a legal call over the generic strong-hand re-raise roll. Free-action value betting, weaker-hand calls and folds, other archetypes, betting legality, and benchmark metric definitions remain as before.

## Diagnosis

In a 200-hand seed-0 public-action diagnostic before this change, the calling-station seat made 56 postflop raises and only 29 postflop calls. The generic strong-hand branches were still re-raising despite this profile's low aggression setting. This slice targets that observable persona mismatch rather than widening calls with weak equity; a broader close-price postflop call candidate failed the primary completion gate on 2026-10-25 and remains rejected.

## Evidence

Both compared artifacts use seeds 0–9, 500 requested hands per seed, four AI players, 10,000 starting chips, and five equity simulations per AI decision. Values are arithmetic means of per-seed profile metrics.

| Measure | 2026-10-25 kept policy | 2026-10-26 call-over-raise |
| --- | ---: | ---: |
| Primary gate | PASS | PASS |
| Hands completed | 5,000 | 5,000 |
| Illegal action rate | 0 | 0 |
| Calling-station VPIP | 22.98% | 22.80% |
| Calling-station call rate | 24.31% | 27.33% |
| Calling-station fold rate | 44.48% | 46.05% |
| Calling-station aggression factor | 0.8043 | 0.5328 |
| Calling-station poor/blunder rate | 1.74% | 1.34% |
| Calling-station average decision score | 72.83 | 72.59 |
| Style separability score | 0.2817 | 0.3096 |

The full automated suite passed 317 tests. Focused fixtures verify that the calling station calls with strong and medium-strong postflop equity while another archetype can still re-raise. The profile's calibration status remains WARN in every seed: its 45% call-rate target, 30% VPIP floor, and 35% fold-rate ceiling are still unmet. The small decision-score decline and fold-rate increase are visible tradeoffs; this benchmark supports a more distinct passive style, not a stronger-play claim.

## Artifacts

- Previous accepted policy: `2026-10-25-calling-station-preflop-only-primary.json`.
- New primary benchmark: `2026-10-26-calling-station-call-over-raise-primary.json`.
- Gate evaluation: `2026-10-26-calling-station-call-over-raise-primary-evaluation.json`.
