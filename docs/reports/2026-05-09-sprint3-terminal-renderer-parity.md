# Sprint 3 Batch 3 — Terminal Renderer Parity

Date: 2026-05-09

## Objective

Define terminal renderer behavior for newly added lifecycle events before rendering them, so future UX changes require explicit parity tests instead of accidental output changes.

## Outcome

Batch 3 completed with tests only. Lifecycle events remain non-rendered unless a future batch adds explicit expected terminal lines.

## Coverage added

`tests/test_terminal_renderer.py` now asserts:

- `hand_started` returns `False` and emits no terminal lines.
- `phase_started` returns `False` and emits no terminal lines.
- `betting_round_started` returns `False` and emits no terminal lines.
- `betting_round_completed` returns `False` and emits no terminal lines.

The test payloads use the same public field shapes emitted by `game.py` for these events.

## Guardrails checked

- No broad `game.py` rewrite for Batch 3.
- No canonical poker rule changes.
- No terminal lifecycle rendering added without expected-line tests.
- Public payloads remain serializable and contain no private hole-card/deck data.

## Verification

```text
python3 -m pytest -q tests/test_terminal_renderer.py
9 passed in 0.02s

python3 -m pytest -q tests/test_terminal_renderer.py tests/test_game_engine_events.py
24 passed in 0.06s

python3 -m pytest -q
145 passed in 26.51s
```
