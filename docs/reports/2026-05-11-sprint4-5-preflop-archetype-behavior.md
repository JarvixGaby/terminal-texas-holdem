# Sprint 4 Slice 4.5 - Preflop Archetype Behavior

Date: 2026-05-11

## Scope

Integrated explicit `ai_profiles.py` archetype profiles into `AdvancedAIEngine`
preflop decisions when an archetype is selected.

Default construction remains compatible: `AdvancedAIEngine("name")` continues to
use the prior range-table path unless an `archetype_name` or `archetype_profile`
is provided.

## Behavior

The preflop integration uses a minimal subset of profile fields:

- `vpip_target`
- `pfr_target`
- `call_bias`
- `aggression_bias`
- `three_bet_frequency`
- `sizing_bias`

The goal is observable style separation, not exact solver ranges. Deterministic
scenario-batch tests now verify:

- `nit` VPIP tendency is lower than `tight_aggressive` and `loose_aggressive`.
- `calling_station` call tendency is higher than `tight_aggressive`.
- `maniac` and `tight_aggressive` raise tendency is higher than `calling_station`.
- Every sampled action remains legal through `ActionValidator`.

## Guardrails

- No postflop c-bet, fold-to-cbet, showdown, or bet-sizing strategy was added.
- No canonical hand-ranking or No-Limit Hold'em rule semantics changed.
- Existing free-check and premium-hand sanity guards remain covered.
- Follow-up review found the archetype-enabled preflop path could still fold AA
  when a premium hand missed randomized raise/call branches. The archetype path
  now preserves style-specific raise frequency while forcing common premium
  hands with chips available to continue as call or raise when facing ordinary
  preflop action.

## Verification

```text
python3 -m pytest -q tests/test_ai_scenario_sanity.py
RED before fix:
10 failed, 21 passed

GREEN after fix:
33 passed

python3 -m pytest -q tests/test_ai_scenario_sanity.py tests/test_ai_system_evaluator.py
36 passed

python3 -m pytest -q
207 passed
```
