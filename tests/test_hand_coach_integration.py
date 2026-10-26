"""Integration coverage for hand-end coach summaries."""

from texas_holdem.engine.game import TexasHoldemGame
from texas_holdem.engine.player import AIPlayer, HumanPlayer


def test_show_instant_replay_prints_non_blocking_hand_coach_summary(monkeypatch, capsys):
    hero = HumanPlayer("Hero", chips=100)
    villain = AIPlayer("Villain", chips=100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.active_players = [hero, villain]
    game.replay_enabled = True
    game.history_manager.start_new_game_record(["Hero", "Villain"], 5, 10, 0)
    game.history_manager.start_new_phase("preflop", [], 30, 10)
    game.history_manager.record_action(
        "Hero",
        "call",
        20,
        100,
        80,
        decision_evaluation={
            "grade": "questionable",
            "score": 55.0,
            "recommended_action": "fold",
            "reasoning": "Preflop call has poor playability/realization.",
            "risk_tags": ["poor_preflop_playability"],
        },
    )
    final_hands = [
        {"player_name": "Hero", "hole_cards": ["A♠", "7♦"], "final_chips": 80, "hand_rank": "已弃牌", "winnings": 0},
        {"player_name": "Villain", "hole_cards": ["K♣", "K♥"], "final_chips": 120, "hand_rank": "其他玩家弃牌", "winnings": 40},
    ]
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")

    game._show_instant_replay(final_hands, ["Villain"])

    output = capsys.readouterr().out
    assert "本手教练快评" in output
    assert "Hero: 复盘 1 个决策" in output
    assert "下一手重点: 翻前少用可玩性差的牌冷跟注" in output
    assert "K♣" not in output
    assert "K♥" not in output
