# Profile Calibration WARN Prioritization

Date: 2026-05-25

## Scope

Inputs:

- `docs/reports/2026-05-16-phase3-profile-calibration-target-bands.md`
- `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json`

This report prioritizes Stage 3.2 profile calibration WARNs into four categories: style fidelity issue, quality issue, metric definition issue, and sample-size issue.

This is a documentation/evidence slice only. It does not modify target bands, benchmark thresholds, AI policy, evaluator scoring, or production code.

## Artifact Status

The reduced `10 seeds x 100 hands` diagnostic artifact reports `profile_calibration_status = WARN` for all 10 runs. The same report records reduced benchmark gate `PASS`, and its interpretation says poker-quality bands remain healthy while multiple profiles are tighter or lower-participation than their target bands.

## WARN Classification

| WARN group | Evidence from reduced artifact | Classification | Priority | Rationale |
| --- | --- | --- | --- | --- |
| TAG participation and initiative too low | tight_aggressive VPIP, PFR, and call_rate WARN in 10/10 runs; fold_rate WARN in 4/10; showdown_rate WARN in 3/10 | style fidelity issue | High | TAG identity is under-expressed: participation and preflop aggression are below the target-band intent. Quality metrics are not failing, so this is style fidelity rather than poker quality. |
| LAG participation and initiative too low | loose_aggressive VPIP, PFR, and call_rate WARN in 10/10 runs; showdown_rate WARN in 8/10; fold_rate WARN in 3/10 | style fidelity issue | High | LAG should be visibly looser and more aggressive, but observed VPIP/PFR/call-rate are below target. This is evidence-backed enough for a future style-calibration slice, but not enough to tune without focused public decision fixtures. |
| Calling-station not sticky enough | calling_station call_rate WARN in 10/10; VPIP, fold_rate, showdown_rate WARN in 8/10 | style fidelity issue | High | The profile still folds too often and calls too little relative to target identity, despite the previous negative-equity call fix. Any future work must avoid reintroducing bad calls by using public pot-odds fixtures. |
| Nit aggression factor above band | nit aggression_factor WARN in 8/10; call_rate WARN in 8/10; VPIP WARN in 7/10 | style fidelity issue | Medium | The nit profile is tight as intended but may be too raise-weighted in the few hands it plays. This needs spot-level review before tuning because low participation can distort aggression factor. |
| Average decision score and poor/blunder bands | No listed average decision score or poor/blunder-rate WARNs in the target-band report | quality issue | Low / none active | The current WARN set does not show a quality failure requiring immediate AI policy repair. |
| Aggression factor for sparse profiles | TAG/LAG/calling-station/nit aggression-factor WARNs appear in fewer or lower-volume situations | metric definition issue | Medium | Aggression factor can swing when call/check/fold denominators are small. Treat isolated aggression-factor WARNs as definition-sensitive until paired with fixture evidence. |
| Showdown-rate WARNs in 100-hand reduced runs | loose_aggressive showdown_rate WARN 8/10; calling_station showdown_rate WARN 8/10; TAG showdown_rate WARN 3/10 | sample-size issue | Medium | Showdown rate is outcome/path dependent in 100-hand reduced runs. It supports watchlisting profile stickiness but should not alone trigger tuning. |

## Future Candidate Slices

The following candidate slices are evidence-backed enough to name, but they still require focused public-information fixtures before code changes:

1. `tag-lag-preflop-participation-fixtures`
   - Target: TAG/LAG VPIP and PFR under-expression.
   - Evidence: TAG and LAG VPIP/PFR WARN in 10/10 reduced runs.
   - Required fixture shape: public preflop decision state, position/action history, legal actions, amount to call, stack sizes, and acting-seat private hand.

2. `calling-station-sticky-but-not-negative-ev-fixtures`
   - Target: calling-station call-rate/fold-rate under-expression without reintroducing negative-equity calls.
   - Evidence: call_rate WARN in 10/10 and fold_rate WARN in 8/10, plus post-tuning residual negative-equity call watchlist.
   - Required fixture shape: public pot-odds state and acting-seat hand class where a call is defensible, plus guard fixtures where equity is below pot odds.

3. `nit-aggression-factor-denominator-review`
   - Target: determine whether nit aggression WARN is real style drift or denominator artifact.
   - Evidence: aggression_factor WARN in 8/10 while nit VPIP is low.
   - Required work: metric/report review first; policy tuning only after fixture-backed public examples.

## Deferred Items

- Do not change calibration target bands to make WARNs disappear.
- Do not make broad AI policy changes from the reduced artifact alone.
- Do not treat sample-size-sensitive showdown-rate WARNs as standalone policy defects.
- Do not begin platform/API/WebSocket/auth/external-agent runtime work from this report.

## Verification

Artifact status command:

```bash
python3 - <<'PY'
import json
from pathlib import Path
artifact = json.loads(Path('docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json').read_text())
statuses = []
for run in artifact.get('runs', []):
    statuses.append(run.get('profile_calibration_status'))
print('profile_calibration_statuses', statuses)
if not statuses:
    raise SystemExit('no profile calibration statuses found')
PY
```

Observed output:

```text
profile_calibration_statuses ['WARN', 'WARN', 'WARN', 'WARN', 'WARN', 'WARN', 'WARN', 'WARN', 'WARN', 'WARN']
```
