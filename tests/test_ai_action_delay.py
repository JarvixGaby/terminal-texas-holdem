from game import TexasHoldemGame
from player import AIPlayer


def test_ai_action_delay_uses_injected_delay_function():
    calls = []
    game = TexasHoldemGame([AIPlayer("AI-1", 100), AIPlayer("AI-2", 100)])
    game.delay_fn = calls.append
    game.ai_action_delay_seconds = 0.25

    game._delay_after_ai_action()

    assert calls == [0.25]


def test_ai_action_delay_can_be_disabled_for_headless_flow():
    calls = []
    game = TexasHoldemGame([AIPlayer("AI-1", 100), AIPlayer("AI-2", 100)])
    game.delay_fn = calls.append
    game.ai_action_delay_seconds = 0

    game._delay_after_ai_action()

    assert calls == []
