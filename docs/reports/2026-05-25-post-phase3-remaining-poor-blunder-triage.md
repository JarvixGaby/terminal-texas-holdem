# Post-Phase-3 Remaining Poor/Blunder Triage

Date: 2026-05-25

## Scope

Input artifact:

- `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json`

This report reviews the remaining reduced-artifact poor/blunder samples after the calling-station negative-equity call loop. It uses only sanitized decision-time fields present in the artifact: classification, profile, phase, action, amount, public board, equity, pot odds, grade, score, risk tags, and audit split. It does not infer from deck order, opponent private cards, folded/non-showdown cards, or private AI internals.

This is documentation/evidence triage only. It does not tune AI policy, evaluator scoring, profile bands, benchmark thresholds, or runtime code.

## Aggregate Summary

The post-tuning artifact contains 22 remaining poor/blunder samples.

| Dimension | Counts |
| --- | --- |
| Classification | overfold 12; pot-odds call mistake 6; low-equity bluff 4 |
| Audit split | true_negative_equity_call 6 |
| Profile | nit 12; calling_station 4; loose_aggressive 4; tight_aggressive 2 |
| Street | preflop 11; flop 5; turn 3; river 3 |
| Action | fold 12; call 6; raise 4 |

Top public action patterns:

| Pattern | Count | Candidate classification |
| --- | ---: | --- |
| nit / preflop / fold / overfold | 6 | evaluator calibration candidate |
| low-equity bluff / preflop / raise, split between nit and loose_aggressive | 4 | insufficient public context |
| flop / call / true_negative_equity_call | 5 | variance/watchlist |
| non-preflop fold / overfold across nit, loose_aggressive, calling_station | 6 | insufficient public context |
| tight_aggressive / preflop / call / true_negative_equity_call | 1 | variance/watchlist |

## Candidate Classification

Each candidate below is classified as exactly one of: policy fixture candidate; evaluator calibration candidate; variance/watchlist; insufficient public context.

| Candidate | Public evidence | Classification | Rationale |
| --- | --- | --- | --- |
| Nit preflop overfold | 6 samples; fold action; empty public board; artifact equity 0.6-0.8 versus pot odds 0.25-0.4 | evaluator calibration candidate | The shared public pattern is the evaluator calling preflop folds poor when the artifact equity field is high. The public artifact does not include hole-card class, position pressure, prior action sequence, stack depth, or legal action context, so this is not enough to tune nit policy. The next safe work would be a fixture that reconstructs public decision state plus acting-seat hand, then verifies whether the evaluator is over-penalizing disciplined nit folds. |
| Low-equity preflop raises | 4 samples; preflop raise; empty public board; equity 0.0; risk tag `high_risk_bluff`; profiles nit 2 and loose_aggressive 2 | insufficient public context | The samples lack enough public decision state to distinguish blind steal, short-stack pressure, isolation, legal minimum-raise artifact, or true spew. No shared public trigger beyond "preflop raise with low artifact equity" is present. |
| True negative-equity calls after prior tuning | 6 samples; call action; audit split `true_negative_equity_call`; mostly flop calls with equity 0.2 versus pot odds around 0.25-0.32; profiles calling_station 2, nit 2, tight_aggressive 2 | variance/watchlist | The targeted prior loop reduced this class sharply, and the remaining samples are small, profile-split, and board-split. They are evidence to watch in the next reduced artifact, not enough for a fresh policy fixture. |
| Non-preflop overfolds | 6 samples; turn/river fold actions; public boards differ; equity 0.8-1.0 versus pot odds around 0.21-0.36; profiles nit, loose_aggressive, calling_station | insufficient public context | These look suspicious, but the sanitized fields do not include facing action, action history, legal options, stack state, or acting hand. Without that decision context, tuning would risk using evaluator outputs as labels instead of public-state evidence. |

## Conclusion

There is no shared public decision-time pattern worth immediate AI policy tuning in this artifact.

The strongest actionable thread is an evaluator-calibration candidate for nit preflop overfold labeling, but it needs fixture-backed reconstruction before any evaluator change is accepted. The remaining true negative-equity call samples should stay on a variance/watchlist until another post-tuning reduced artifact shows concentration by profile, street, and public trigger. Low-equity preflop raises and postflop overfolds are insufficient-context findings under the current sanitized sample shape.

## Verification

Artifact summary command:

```bash
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
artifact = json.loads(Path('docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json').read_text())
classes = Counter(); splits = Counter(); profiles = Counter()
for run in artifact.get('runs', []):
    for sample in run.get('poor_blunder_samples', []):
        classes[sample.get('classification')] += 1
        if sample.get('audit_split'):
            splits[sample.get('audit_split')] += 1
        profiles[sample.get('profile')] += 1
print('classes', dict(classes))
print('splits', dict(splits))
print('profiles', dict(profiles))
PY
```

Observed output:

```text
classes {'overfold': 12, 'low-equity bluff': 4, 'pot-odds call mistake': 6}
splits {'true_negative_equity_call': 6}
profiles {'nit': 12, 'tight_aggressive': 2, 'loose_aggressive': 4, 'calling_station': 4}
```
