"""Hand-end coach summary tests."""

from texas_holdem.training.hand_coach import HandCoach


def test_hand_coach_summarizes_worst_human_decision_without_opponent_cards():
    record = {
        "phases": [
            {
                "phase": "preflop",
                "actions": [
                    {
                        "player_name": "Hero",
                        "action": "call",
                        "amount": 20,
                        "decision_evaluation": {
                            "grade": "questionable",
                            "score": 55.0,
                            "recommended_action": "fold",
                            "reasoning": "Preflop call has poor playability/realization.",
                            "risk_tags": ["poor_preflop_playability"],
                        },
                    },
                    {
                        "player_name": "Villain",
                        "action": "raise",
                        "amount": 60,
                        "decision_evaluation": {
                            "grade": "excellent",
                            "score": 92.0,
                            "recommended_action": "raise",
                            "reasoning": "Opponent private note should not leak.",
                        },
                    },
                ],
            },
            {
                "phase": "flop",
                "actions": [
                    {
                        "player_name": "Hero",
                        "action": "fold",
                        "amount": 0,
                        "decision_evaluation": {
                            "grade": "good",
                            "score": 74.0,
                            "recommended_action": "fold",
                            "reasoning": "Fold is fine against pressure.",
                        },
                    }
                ],
            },
        ],
        "final_hands": [
            {"player_name": "Hero", "hole_cards": ["A♠", "7♦"], "winnings": 0},
            {"player_name": "Villain", "hole_cards": ["K♣", "K♥"], "winnings": 100},
        ],
        "winner_names": ["Villain"],
    }

    summary = HandCoach().build_summary(record, "Hero")

    assert summary.player_name == "Hero"
    assert summary.actions_reviewed == 2
    assert summary.average_score == 64.5
    assert summary.worst_decision["phase"] == "preflop"
    assert summary.worst_decision["recommended_action"] == "fold"
    assert summary.primary_tip == "翻前少用可玩性差的牌冷跟注，优先加注或弃牌。"
    formatted = summary.format_text()
    assert "本手教练快评" in formatted
    assert "平均 64.5/100" in formatted
    assert "Villain" not in formatted
    assert "K♣" not in formatted


def test_hand_coach_returns_sample_building_message_when_no_evaluated_actions():
    record = {"phases": [{"phase": "preflop", "actions": []}], "winner_names": []}

    summary = HandCoach().build_summary(record, "Hero")

    assert summary.status == "no_actions"
    assert summary.primary_tip == "本手没有可评估的人类决策；继续完成更多手牌来积累训练样本。"
    assert "继续完成更多手牌" in summary.format_text()


def test_hand_coach_uses_best_available_leak_tip_for_overfold():
    record = {
        "phases": [
            {
                "phase": "turn",
                "actions": [
                    {
                        "player_name": "Hero",
                        "action": "fold",
                        "amount": 0,
                        "decision_evaluation": {
                            "grade": "poor",
                            "score": 30.0,
                            "recommended_action": "call",
                            "reasoning": "Folded despite equity being far above the price offered by pot odds.",
                            "risk_tags": ["overfold"],
                        },
                    }
                ],
            }
        ]
    }

    summary = HandCoach().build_summary(record, "Hero")

    assert summary.primary_tip == "面对下注不要只看绝对牌力，先用底池赔率判断是否过度弃牌。"
    assert "turn fold → 建议 call" in summary.format_text()
