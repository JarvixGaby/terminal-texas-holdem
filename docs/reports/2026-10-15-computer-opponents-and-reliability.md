# Computer Opponents and Reliability Update

Date: 2026-10-15

## Scope

The user asked for more credible computer opponents and approved the preceding project review's reliability and evaluation recommendations. This slice stays in the local terminal game. It changes no benchmark metric definitions, public snapshot fields, historical artifacts, runtime data paths, or canonical hand ranking.

## Changes

- The terminal game assigns five distinct named archetypes to computer seats: balanced, loose-aggressive, calling-station, tight-aggressive, and maniac. It shows these styles at setup and records the actual archetype in hand history.
- The built-in AI adapter maps the existing public seat index to the AI range manager's blind-relative position. Heads-up position 0 is the button/small blind and position 1 the big blind.
- Hand history writes to a temporary file in the same directory, syncs it, then atomically replaces the previous JSON. A damaged existing file raises an error and remains intact; a failed replace leaves the last complete record on disk and keeps the current record in the history manager's memory.
- Deterministic headless fixtures now check action event/history parity, invalid-action fallback parity, and hand completion/winner parity. Local headless runs serialize concurrent access to shared AI/style globals.
- README requirements and opponent descriptions now match the implemented local game.

## Focused Decision Fixtures

With the same 10-chip preflop call price and 7♣6♣ on the button, the profiles take different lines: nit and TAG fold, LAG and calling-station call, and maniac raises. This fixed decision scenario shows distinct tendencies; it is not proof of broad poker strength.

## Benchmark Evidence

Protocol for each diagnostic run: 10 seeds × 100 hands, 4 players, 10,000 starting chips, 5 equity simulations per decision.

| Measure | Position fix | Late-position open candidate | Interpretation |
| --- | ---: | ---: | --- |
| Reduced gate | PASS | PASS | Declared reduced protocol only |
| Average decision score | 72.851 | 72.945 | Small diagnostic increase |
| Style separability | 0.260 | 0.285 | Small diagnostic increase |
| PFR spread | 0.097 | 0.101 | Still below the intended style distance |
| Illegal action rate | 0 | 0 | Validator boundary preserved |

The late-position open candidate had focused fixtures and a promising reduced run, but its primary 10 × 500 gate failed completion: seed 9 ended after 237 hands with one player holding all 40,000 chips. The candidate policy and its focused test were removed from the final code. Its artifacts remain as clearly marked rejected experiment evidence. Profile calibration remains a separate diagnostic: the position-only reduced run reported WARN for all 10 seeds.

## Primary Benchmark

The final AI code is the position-fix-only version. Its canonical 10 seeds × 500 hands artifact passed all 15 gate checks. It completed 5,000 hands with zero runtime errors and zero illegal actions. Mean decision score was 72.8647 and mean style separability was 0.2500. The position fix corrected a concrete seat-translation defect; these metrics do not demonstrate broad playing-strength improvement. Style calibration reported WARN for all 10 seeds.

## Verification

- Focused AI scenario/profile/tuning tests after candidate rollback: `71 passed`.
- Full suite after candidate rollback: `291 passed`.
- Damaged JSON and failed atomic replacement preserve the prior on-disk history in focused tests.

## Remaining Work

- Profile VPIP/PFR and calling-station call frequency remain below target bands. Each further strategy change needs representative decision fixtures and fresh pre/post evidence.
- JSON history still rewrites all prior records for each hand. Atomic writing addresses corruption risk; a storage scalability change requires a separate compatibility and migration slice.
- Headless simulation still swaps process-global managers for isolation. The local lock prevents simultaneous headless runs from interfering with each other, but a longer-term dependency-injection boundary remains useful.
- A read-only heads-up check found `_get_betting_order()` starts preflop with the big blind when the dealer is the small blind. This needs a separate core-rules task and regression coverage before changing betting flow.
