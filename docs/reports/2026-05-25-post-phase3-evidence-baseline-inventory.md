# Post-Phase-3 Evidence Baseline Inventory
Date: 2026-05-25

## Purpose

This inventory establishes the current evidence baseline after Phase 3 and the 2026-05-22 targeted calling-station negative-equity call loop. It separates primary benchmark evidence from reduced diagnostic evidence and post-tuning evidence so future claims, tuning slices, and platform-readiness decisions do not overstate what the artifacts prove.

This report is documentation-only. It does not modify production code, tests, benchmark artifacts, historical report bodies, runtime data, benchmark thresholds, public/private contracts, WebSocket/API/auth scope, or external-agent runtime behavior.

## Executive Summary

- The strongest current gate evidence remains the post-calibration primary `10 seeds x 500 hands` benchmark from 2026-05-13. Its machine-readable gate evaluation is clean `PASS`; this supports a local benchmark baseline claim for legality, completion, required metrics, transcript safety, profile coverage, decision-quality soft gates, and style separability under that protocol.
- Stage 3.2 through Stage 3.5 evidence is mostly reduced `10 seeds x 100 hands` diagnostic evidence. It is useful for measurement, calibration, safety-sample review, poor/blunder taxonomy, and candidate prioritization. It must not be used as a broad long-run strength claim.
- The 2026-05-22 calling-station negative-equity call loop reached its explicit reduced-artifact target: total `pot-odds call mistake` samples reached `6`, `calling_station` concentration reached `2`, and the final full test suite was recorded as `279 passed`. This supports targeted evaluator/policy consistency improvement for the named diagnostic class only.
- Platform/WebSocket/auth/external-agent runtime work remains blocked by evidence and contract gates: no post-tuning primary rerun, unresolved profile calibration WARNs, remaining poor/blunder classes, no headless/action API readiness inventory, no local external-agent harness/fixture corpus, no local arena evidence, and no explicit maintainer authorization for platform slices.

## Evidence Map

### Primary gate evidence

| Evidence | Protocol | Status | What it supports |
| --- | --- | --- | --- |
| `docs/reports/2026-05-13-phase3-primary-benchmark-preflop-fold-calibration.md` | Full primary `10 seeds x 500 hands`, 4 players, starting chips `10000` | Clean machine-readable `PASS` after preflop-fold evaluator calibration | Current canonical local AI benchmark baseline after calibration. Supports completion, no runtime errors, action coverage, `illegal_action_rate == 0.0`, required metrics, transcript availability and safety, profile coverage, average decision score, style separability, poor/blunder rate, blunder rate, and JSON safety under the primary protocol. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-gate-after-preflop-fold-calibration.json` | Machine-readable benchmark artifact for the same primary run | 10 runs, each `500` hands | Source artifact for aggregate metrics: average decision score mean `72.7203`, style separability mean `0.2924`, illegal action rate mean `0.0`, and `18,695` evaluated actions. |
| `docs/reports/2026-05-13-phase3-primary-benchmark-gate-after-preflop-fold-calibration-evaluation.json` | Gate evaluation against the primary protocol | `PASS` | Machine-readable evidence that all configured primary gate checks passed. |

Primary claim boundary: this evidence can be cited as the current canonical Phase 3 primary benchmark gate baseline. It does not prove solver/GTO quality, real-money suitability, public leaderboard strength, external-agent runtime readiness, or online platform readiness.

### Reduced diagnostic evidence

| Evidence | Protocol | Status | What it supports |
| --- | --- | --- | --- |
| `docs/reports/2026-05-16-phase3-profile-calibration-target-bands.md` | Reduced `10 seeds x 100 hands` diagnostic benchmark | Reduced gate `PASS`; profile calibration status `WARN` in `10 / 10` runs | Confirms profile calibration fields work and identifies several archetypes as tighter/lower-participation than target bands. The bands are diagnostic, not primary pass/fail gates. |
| `docs/reports/2026-05-16-phase3-profile-calibration-reduced-benchmark.json` | Machine-readable reduced benchmark artifact | 10 runs, each `100` hands; each run has `profile_calibration_status == WARN` | Source artifact for profile calibration distances and reduced summary metrics. Supports prioritization of profile calibration investigation, not broad AI strength claims. |
| `docs/reports/2026-05-16-phase3-poor-blunder-audit.md` | Reduced `10 seeds x 100 hands` audit artifact | Expected canonical gate mismatch if evaluated as primary; diagnostic evidence only | Adds sanitized poor/blunder samples. Identifies `57` samples across `1000` hands and `4445` actions, with top classes: `pot-odds call mistake` `33`, `overfold` `21`, and low-count `low-equity bluff`. |
| `docs/reports/2026-05-16-phase3-public-private-safety-gate.md` | Local safety-gate and tests over transcript/audit sample payloads | Reported focused safety checks and full suite pass at that time | Supports that transcript samples and poor/blunder audit samples were checked for public/private leakage in the local evidence surface. It does not authorize external-agent runtime or online rooms. |
| `docs/reports/2026-05-16-phase3-evaluation-agent-loop.md` | One reduced-artifact review loop over Stage 3.3/3.4 evidence | Coordinator accepted diagnostic use only | Establishes the evaluation-agent loop roles and the rule that reduced artifacts should guide follow-up review, not become the canonical primary gate. |
| `docs/reports/2026-05-22-phase3-pot-odds-audit-split.md` | Reduced `10 seeds x 100 hands` diagnostic benchmark with public equity-vs-pot-odds split | Reduced protocol `PASS`; `pot_odds_audit_splits {'true_negative_equity_call': 33}` | Shows sampled pot-odds call mistakes in that artifact were supported by public equity-vs-pot-odds evidence rather than obvious evaluator false positives. Narrows the next target to calling-station-heavy negative-equity calls. |

Reduced diagnostic claim boundary: these artifacts can identify candidate error classes, evaluator calibration risks, safety-sample behavior, and profile-target drift. They cannot support a broad long-run AI strength claim, platform readiness claim, or leaderboard-style comparison because they use reduced `10 x 100` protocols and, in some cases, intentionally fail primary-protocol checks when judged as canonical primary artifacts.

### Post-tuning evidence

| Evidence | Protocol | Status | What it supports |
| --- | --- | --- | --- |
| `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning.md` | Targeted Builder/Hacker-style loop over calling-station negative-equity calls, then reduced `10 seeds x 100 hands` benchmark | Final reduced target reached; full suite recorded as `279 passed` | Supports targeted evaluator/policy consistency improvement for the named diagnostic class. It documents narrow policy and evaluator-side changes without weakening thresholds or changing public/private/platform scope. |
| `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json` | Machine-readable post-tuning reduced benchmark artifact | Reduced summary: average decision score mean `72.9465`; poor/blunder classes `overfold: 12`, `low-equity bluff: 4`, `pot-odds call mistake: 6`; pot-odds profiles `tight_aggressive: 2`, `nit: 2`, `calling_station: 2` | Source artifact for the final post-tuning reduced target. It supports the targeted class claim only. |
| `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark-evaluation.json` | Gate evaluation against the explicit reduced protocol | `PASS` | Confirms the post-tuning reduced artifact passed its declared reduced protocol checks. |

Post-tuning claim boundary: the 2026-05-22 loop can be described as a successful targeted diagnostic-class improvement. It cannot be described as broad poker strength improvement because it has not yet been followed by a post-tuning primary `10 x 500` or larger repeated benchmark gate, and remaining classes still need public-context triage.

## Claim Boundaries

### Supported claims

- The current canonical primary benchmark baseline is the 2026-05-13 post-calibration `10 seeds x 500 hands` clean `PASS`.
- The primary baseline supports local benchmark gate claims for legality, completion, zero illegal action rate, required metrics, transcript safety, profile coverage, decision-quality soft thresholds, style separability, poor/blunder threshold, and JSON safety under that exact protocol.
- Stage 3.2 through Stage 3.5 created useful diagnostic surfaces: profile calibration target bands, sanitized poor/blunder audit samples, public/private safety sample checks, and an evaluation-agent review loop.
- The 2026-05-22 pot-odds audit split justified a named follow-up target: calling-station-heavy true negative-equity calls.
- The 2026-05-22 calling-station loop reached its reduced diagnostic target and is evidence of improved evaluator/policy consistency for that targeted class.

### Diagnostic-only claims

- Profile calibration WARNs indicate candidate style-fidelity or participation-rate issues, not primary gate failure.
- `pot-odds call mistake`, `overfold`, and `low-equity bluff` counts are tuning and triage signals from reduced artifacts, not stable long-run population estimates.
- Public/private safety sample checks show the current benchmark/report payloads were scanned in local evidence surfaces. They do not prove safety for future payload types or networked runtime surfaces.
- Builder/Hacker/Evaluator role templates define process discipline and one completed artifact-review loop. They do not by themselves prove future AI changes are safe or strong.

### Unsupported / forbidden claims

- Do not claim broad AI strength improvement from the 2026-05-22 reduced post-tuning artifact.
- Do not claim solver, GTO, real-money, production-grade, or public leaderboard strength.
- Do not treat reduced `10 x 100` artifacts as equivalent to the canonical primary `10 x 500` protocol.
- Do not claim external-agent runtime readiness. The project still lacks a frozen fixture corpus, local contract harness evidence, timeout/invalid-action runtime proof beyond documented stubs, and a completed headless/action API readiness slice.
- Do not claim online platform readiness. Platform/WebSocket/auth/account/matchmaking work is still outside the active plan because the roadmap gates are unmet: post-tuning primary evidence is missing, profile calibration WARNs remain untriaged, remaining poor/blunder classes need public-context review, headless/action readiness is not inventoried, local arena evidence is absent, threat-model/ADR work is absent, and maintainer authorization for platform work has not been given.

## Remaining Evidence Gaps

- No post-tuning primary `10 x 500` or larger benchmark has refreshed the canonical baseline after the 2026-05-22 targeted changes.
- Remaining poor/blunder samples from the post-tuning artifact still need public decision-time triage. Current final reduced counts are `overfold: 12`, `low-equity bluff: 4`, and `pot-odds call mistake: 6`.
- Profile calibration WARNs remain unresolved and should be classified before any broad policy tuning.
- Builder/Hacker candidate-loop discipline exists, but the post-Phase-3 loop should be refreshed or dry-run so future changes require fixture-backed public-information targets, safety verdicts, and pre/post evidence.
- Public/private safety evidence is limited to current local benchmark/report payloads and should be repeated whenever new audit payloads, transcript fields, contract fixtures, or adapter surfaces are introduced.
- Headless/action API readiness, local external-agent harness, local arena evidence, and platform threat-model/ADR work are not complete and should not be bypassed.

## Recommended Next Actions

1. Triage the remaining poor/blunder samples from `docs/reports/2026-05-22-phase3-calling-station-negative-equity-call-tuning-benchmark.json` using only public decision-time context. Classify each candidate as `policy fixture candidate`, `evaluator calibration candidate`, `variance/watchlist`, or `insufficient public context`.
2. Refresh or dry-run the Builder/Hacker candidate loop so future AI policy/evaluator changes require fixture-backed public-information targets, safety verdicts, and pre/post benchmark evidence.

Do not add platform/WebSocket/auth/external-agent runtime tasks to the active plan from this inventory.

## Verification

Checked as part of this inventory:

- New report path: `docs/reports/2026-05-25-post-phase3-evidence-baseline-inventory.md`.
- Required evidence documents and artifacts listed above were verified present.
- This report was added to `docs/index.md`.
- `docs/active_plan.md` was updated only to mark Slice 1 complete and preserve the two later unchecked steps.
- `AGENTS.md` was not modified.
- `git diff --check` passed.
