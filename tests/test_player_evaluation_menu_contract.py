from player_evaluation import PlayerEvaluationSystem


def test_evaluate_player_style_alias_returns_comprehensive_evaluation(monkeypatch):
    system = PlayerEvaluationSystem()
    expected = {"player_name": "Hero", "style_distribution": {"紧凶": 100.0}}

    monkeypatch.setattr(system, "get_comprehensive_evaluation", lambda player_name: expected)

    assert system.evaluate_player_style("Hero") == expected
