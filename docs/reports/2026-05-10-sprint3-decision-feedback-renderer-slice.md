# Sprint 3 Slice 12.1 Decision Feedback Renderer

Date: 2026-05-10

## Scope

Routed the existing compact human decision feedback line through a public `decision_feedback_displayed` engine event and `TerminalEventRenderer`.

## Changes

- Added `DecisionFeedbackDisplayedEvent`.
- Emitted `decision_feedback_displayed` from the existing human-only feedback path.
- Added terminal rendering for `decision_feedback_displayed`.
- Preserved the existing compact feedback text format:
  - `📊 决策反馈: <grade> <score>/100 | recommended: <action> | <reasoning>`
- Preserved output ordering after the validated/applied action display line.
- Kept AI-player feedback silent, so headless and AI-only simulation output does not become noisy.

## Event Boundary

`decision_feedback_displayed` uses public serializable payload only:

- `player_name`
- `message`

No private hole cards, deck state, private player state, or decision-provider private state are included.

## TDD Evidence

RED:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_decision_feedback tests/test_game_engine_events.py::test_decision_feedback_routes_display_through_renderer
```

Failed with `TerminalEventRenderer.render()` returning `False` for `decision_feedback_displayed` and no game event emission.

GREEN:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py::test_terminal_renderer_renders_decision_feedback tests/test_game_engine_events.py::test_decision_feedback_routes_display_through_renderer
```

Passed: `2 passed`.

Focused verification:

```bash
python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py tests/test_headless_simulation.py
```

Passed: `57 passed`.

Full verification:

```bash
python3 -m pytest -q
```

Passed: `170 passed`.
