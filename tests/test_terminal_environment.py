import os

from main import EnhancedTexasHoldemUI


def test_clear_screen_skips_clear_when_term_missing_on_posix(monkeypatch):
    calls = []
    ui = object.__new__(EnhancedTexasHoldemUI)

    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.setattr(os, "system", lambda command: calls.append(command))

    ui.clear_screen()

    assert calls == []
