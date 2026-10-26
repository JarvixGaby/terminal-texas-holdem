# Calling-station medium-equity check, 2026-10-26

## Decision

Keep Astra's narrow calling-station policy change. When no bet is faced postflop, the station checks with estimated equity from 45% up to but not including 75%. Explicit flop continuation bets and value bets at 75% or higher still take precedence. Calls when facing a bet, other archetypes, legality, and benchmark metric definitions are unchanged.

## Diagnosis

The calibration `call_rate` counts calls divided by **all** actions, including checks, opening bets, and folds. It is not the rate of calling when facing a bet. In the previous accepted primary artifact, reaching the 45% floor at the same action volume would require roughly 110 additional calls per 500 hands. The reduced audit did not find enough clearly positive-price folded hands to justify broadening calls; the five-rollout fast benchmark also makes individual equity estimates coarse. Two earlier check candidates had no measurable effect in the same-seed diagnostic and were discarded. The retained 45–75% no-bet branch improved passive showdown behavior without introducing weak calls.

## Primary comparison

Both artifacts use seeds 0–9, 500 hands per seed, four AI players, 10,000 starting chips, and five equity simulations per AI decision. Percentages and scores are arithmetic means of per-seed calling-station profile values unless otherwise noted.

| Measure | Previous accepted policy | Astra candidate |
| --- | ---: | ---: |
| Primary gate | PASS | PASS |
| Hands completed | 5,000 | 5,000 |
| Illegal action rate | 0 | 0 |
| Calling-station VPIP | 35.11% | 34.80% |
| Calling-station call rate | 32.10% | 32.23% |
| Calling-station fold rate | 32.81% | 31.45% |
| Calling-station showdown rate | 9.72% | 13.50% |
| Calling-station aggression factor | 0.5705 | 0.3807 |
| Calling-station poor/blunder rate | 1.32% | 1.04% |
| Calling-station decision score | 72.20 | 72.74 |
| Style separability score | 0.3473 | 0.3530 |

All ten seeds completed, no runtime errors occurred, and the full automated suite passed **319 tests**. A focused regression checks the station's medium-equity check, strong value bet, and flop continuation bet against another archetype.

The station's overall profile calibration remains **WARN** on all ten seeds. VPIP passed on all ten; fold rate passed on eight; showdown rate passed on one, up from zero. Call rate remains below its 45% target on all ten seeds. This policy improves the passive character and showdown frequency but does not meet the call-rate target.

## Runtime-equity diagnostic

A separate 30-hand seed-0 run compared the fast benchmark's five equity simulations per decision with the normal 500. Both completed with zero illegal actions. Station call rate was 24.32% with five simulations and 42.86% with 500; showdown rate was 3.33% versus 33.33%. The tiny, path-dependent sample is not an acceptance benchmark. It shows why the five-rollout primary results should not be presented as a prediction of the terminal runtime's exact action frequencies. A larger runtime-equity evaluation would be needed before claiming runtime calibration.

## Artifacts

- Previous accepted policy: `2026-10-26-calling-station-small-blind-completion-primary.json`.
- New primary benchmark: `2026-10-26-calling-station-astra-medium-equity-check-primary.json`.
- Gate evaluation: `2026-10-26-calling-station-astra-medium-equity-check-primary-evaluation.json`.
