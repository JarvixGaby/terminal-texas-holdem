"""Training center behavior tests for local trainer UX."""

from training_center import LocalTrainerCenter


def test_training_center_returns_onboarding_plan_when_history_is_insufficient():
    report = LocalTrainerCenter().build_report(
        "新玩家",
        {"error": "数据不足", "message": "需要至少10局游戏数据才能进行评测"},
    )

    assert report.player_name == "新玩家"
    assert report.status == "needs_more_hands"
    assert report.headline == "先建立可分析的样本"
    assert report.focus_areas[0]["title"] == "完成10手可复盘样本"
    assert "开始新游戏" in report.next_session_plan[0]
    assert "数据不足" in report.format_text()


def test_training_center_prioritizes_loose_passive_leaks_from_stats():
    evaluation = {
        "player_name": "Hero",
        "primary_style": {"name": "跟注站", "percentage": 62.0},
        "style_distribution": {"跟注站": 62.0, "鱼": 18.0, "平衡": 20.0},
        "current_stats": {
            "hands_played": 42,
            "vpip": 48.0,
            "pfr": 12.0,
            "aggression_factor": 0.7,
            "fold_to_bet": 18.0,
        },
        "suggestions": ["💪 建议增加主动性，多使用加注而不是被动跟注"],
    }

    report = LocalTrainerCenter().build_report("Hero", evaluation)

    assert report.status == "ready"
    assert report.headline == "本轮训练重点：减少松弱跟注"
    titles = [area["title"] for area in report.focus_areas]
    assert titles[:3] == ["收紧入局范围", "提高翻前主动性", "少做自动跟注"]
    assert any("先加注或弃牌" in item for item in report.next_session_plan)
    formatted = report.format_text()
    assert "VPIP 48.0%" in formatted
    assert "PFR 12.0%" in formatted
    assert "少做自动跟注" in formatted


def test_training_center_recognizes_solid_tag_and_gives_maintenance_plan():
    evaluation = {
        "player_name": "Hero",
        "primary_style": {"name": "紧凶", "percentage": 55.0},
        "style_distribution": {"紧凶": 55.0, "平衡": 35.0, "松凶": 10.0},
        "current_stats": {
            "hands_played": 80,
            "vpip": 24.0,
            "pfr": 18.0,
            "aggression_factor": 2.4,
            "fold_to_bet": 36.0,
        },
        "suggestions": ["✅ 紧凶风格很好，继续保持选择性和侵略性的平衡"],
    }

    report = LocalTrainerCenter().build_report("Hero", evaluation)

    assert report.headline == "本轮训练重点：保持紧凶质量"
    assert report.focus_areas[0]["title"] == "保持选择性进攻"
    assert any("复盘最大底池" in item for item in report.next_session_plan)
