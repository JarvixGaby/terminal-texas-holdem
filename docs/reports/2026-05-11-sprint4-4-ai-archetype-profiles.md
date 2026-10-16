# Sprint 4 Slice 4.4 - AI Archetype Profiles

Date: 2026-05-11

## Scope

Added a minimal immutable AI archetype profile/config layer in `ai_profiles.py`.

This module is intentionally separate from observed opponent models such as
`advanced_ai_engine.OpponentProfile`; it describes selectable built-in AI
persona targets for later strategy slices.

## Profiles

Defined six archetypes:

- `nit`
- `tight_aggressive`
- `loose_aggressive`
- `calling_station`
- `maniac`
- `balanced`

Each profile includes JSON-compatible target tendency fields:

- `vpip_target`
- `pfr_target`
- `aggression_bias`
- `call_bias`
- `bluff_frequency`
- `three_bet_frequency`
- `cbet_frequency`
- `fold_to_cbet_bias`
- `showdown_stickiness`
- `sizing_bias`

## Guardrails

- No preflop archetype behavior was implemented in this slice.
- Existing `AdvancedAIEngine("name")` construction remains compatible without profile selection.
- Profile numeric fields are validated in the inclusive `0.0` to `1.0` range.
- `pfr_target` cannot exceed `vpip_target`.

## Verification

```text
python3 -m pytest -q tests/test_ai_profiles.py
4 passed

python3 -m pytest -q tests/test_ai_tuning.py tests/test_ai_system_evaluator.py
4 passed

python3 -m pytest -q
194 passed
```
