# Calling-station action opportunities, 2026-10-26

## Scope and method

This is an observational diagnostic of the accepted calling-station policy. No AI decision rule, canonical benchmark metric, target band, or poker legality rule changed. For each of seeds 0–2, the same four built-in profiles played 100 hands with 10,000 starting chips. One run used the fast benchmark setting of five equity simulations per decision; the other used the normal runtime setting of 500. Every engine decision by the calling station was matched in order and action type to its recorded game action. All six runs completed 100 hands with zero errors and zero illegal actions.

`scripts/diagnose_calling_station_opportunities.py` records only aggregate action counts and estimated equity-minus-pot-price buckets. An opportunity is **facing** when the decision input `current_bet` is positive; otherwise it is **free**. The conditional call rate is calls divided by facing opportunities. The existing benchmark `call_rate` remains calls divided by **all** actions. The two settings consume randomness differently and produce different game paths, even with the same seed; this is a configuration comparison, not a paired decision-level experiment.

## Results

The table pools counts across the three seeds. These are reduced 300-hand diagnostics, not the canonical 5,000-hand primary benchmark.

| Measure | Five simulations | 500 simulations |
| --- | ---: | ---: |
| Calling-station actions | 550 | 719 |
| Facing a bet | 373 | 415 |
| Free actions | 177 | 304 |
| Calls | 190 | 254 |
| Conditional call rate | 50.94% | 61.20% |
| Calls / all actions | 34.55% | 35.33% |
| Preflop facing: calls / opportunities | 107 / 256 = 41.80% | 140 / 259 = 54.05% |
| Postflop facing: calls / opportunities | 83 / 117 = 70.94% | 114 / 156 = 73.08% |

Under the 500-simulation setting, the 304 free actions were 245 checks and 59 raises. Of the 415 facing opportunities, 254 were calls, 154 folds, and 7 raises. The 154 folds split into 112 preflop and 42 postflop. Thus the all-action rate stays low even though the station calls most bets it faces, especially after the flop.

## Price and policy diagnosis

For each facing decision, the script compares estimated equity with `current_bet / (pot_size + current_bet)`. Under 500 simulations, 103 of 112 preflop folds had estimated equity below that immediate price; 87 were more than ten percentage points below. This supports retaining the existing negative-price protections. Nine preflop folds covered the immediate price, but range, position, future betting, and estimation still matter; none is automatically a profitable call.

Postflop, 27 of 42 folds had estimated equity at or above the immediate price: 5/10 on the flop, 14/19 on the turn, and 8/13 on the river. Fourteen of those 27 were at least ten percentage points above the price. This is a specific set of decisions worth reviewing with public-context fixtures. The current postflop policy has absolute equity branches, so a hand below its 45% medium-hand threshold can fold even when a small bet offers a lower immediate price. These counts identify candidates for inspection, not proven mistakes or an instruction to call all of them.

At the observed 719-action volume, a 45% all-action call rate would require at least 324 calls, 70 more than observed. Even hypothetically converting all 36 price-covered folds to calls while keeping every other action and future path fixed would yield 290/719 = 40.33%. Real policy changes alter later actions and the denominator, so this arithmetic is a scale check rather than a forecast. It shows why a broad fold-to-call switch is not supported by this sample.

The accepted 5,000-hand fast primary benchmark remains PASS with zero illegal actions. Its station calls increased from 2,726 to 2,942 after the medium-equity check change, but station actions also increased from 8,493 to 9,106. More passive checks and later-street actions absorbed most of the call-rate gain. The primary benchmark uses five simulations; the 300-hand runtime diagnostic does not establish a stable long-run runtime rate.

## Next decision

Keep both rates visible in diagnostics: conditional calling when facing a bet, and the existing calls/all-actions benchmark rate. Before any policy tuning, inspect the 27 postflop price-covered folds with repeatable public-context fixtures, especially turn and river choices, then require the existing quality and primary legality/completion gates. Do not change the 45% target or benchmark metric definition on the basis of this reduced diagnostic alone.

## Artifacts and command

- Runtime setting: `2026-10-26-calling-station-runtime-opportunities.json`.
- Fast setting: `2026-10-26-calling-station-fast-opportunities.json`.
- Reproduce with `/opt/anaconda3/bin/python scripts/diagnose_calling_station_opportunities.py --seeds 0 1 2 --hands-per-seed 100 --rollouts 500 --output <new-path>`; use `--rollouts 5` for the fast comparison. Use a new output path to preserve these historical artifacts.
