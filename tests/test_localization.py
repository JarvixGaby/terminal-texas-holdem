import ast
import os
import re
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import localization
from game_history import GamePhase, GameRecord, PlayerAction, PlayerHand
from player_evaluation import PlayerEvaluationSystem


ROOT = Path(__file__).resolve().parents[1]


def test_language_is_first_prompt_and_main_menu_is_translated(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env.pop("TERM", None)
    for choice, expected, excluded in (
        ("1", "开始新游戏", "New game"),
        ("2", "New game", "开始新游戏"),
    ):
        result = subprocess.run(
            [sys.executable, str(ROOT / "main.py")],
            input=f"{choice}\n\n6\ny\n",
            cwd=tmp_path, env=env, text=True, capture_output=True, timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.startswith("选择语言 / Choose language:")
        assert expected in result.stdout
        assert excluded not in result.stdout.split("> ", 1)[-1]
        if choice == "2":
            assert not re.search(r"[\u4e00-\u9fff]", result.stdout.split("> ", 1)[-1])
        assert "🎮" not in result.stdout


def test_visible_game_and_replay_literals_have_english_translations():
    localization.LANGUAGE = "en"
    try:
        for filename in ("main.py", "game.py", "quick_replay_system.py", "history_viewer.py"):
            tree = ast.parse((ROOT / filename).read_text())
            for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
                func = call.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                if name not in {"print", "input", "safe_int_input", "safe_str_input", "safe_choice_input", "safe_confirm_input"}:
                    continue
                for arg in call.args:
                    for node in ast.walk(arg):
                        if isinstance(node, ast.Constant) and isinstance(node.value, str):
                            assert not re.search(r"[\u4e00-\u9fff]", localization.translate(node.value)), (filename, node.value)
    finally:
        localization.LANGUAGE = "zh"


def test_chinese_action_labels_are_only_for_terminal_session():
    from game import TexasHoldemGame

    game = object.__new__(TexasHoldemGame)
    assert game._get_human_display_actions(["check", "raise", "fold"], 0) == ["check", "bet", "fold"]
    with localization.terminal_language("zh"):
        assert game._get_human_display_actions(["check", "raise", "fold"], 0) == ["过牌", "下注", "弃牌"]


def test_chinese_betting_command_keeps_internal_action_values(monkeypatch, capsys):
    from game import TexasHoldemGame

    game = object.__new__(TexasHoldemGame)
    game.assistant_enabled = False
    game._display_active_players = lambda: None
    game._get_legal_actions = lambda *args: ["call", "raise", "fold"]
    player = SimpleNamespace(name="Hero", chips=500, get_hand_string=lambda: "A♠ K♠")
    monkeypatch.setattr("builtins.input", lambda prompt="": "弃牌")
    with localization.terminal_language("zh"):
        assert game._get_human_action(player, 10) == ("fold", 0)
    assert "可选动作: 跟注, 加注, 弃牌" in capsys.readouterr().out


def test_player_name_is_not_translated(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "小鱼")
    with localization.terminal_language("en"):
        assert input("请输入您的姓名: ") == "小鱼"
        print("小鱼 的回合")
    assert "小鱼's turn" in capsys.readouterr().out


def test_card_suits_survive_emoji_reduction():
    for language in ("zh", "en"):
        with localization.terminal_language(language):
            assert "A♠ K♥ Q♦ J♣" in localization.translate("🃏 A♠ K♥ Q♦ J♣")
            assert "🃏" not in localization.translate("🃏 A♠ K♥ Q♦ J♣")


def test_style_review_reads_saved_list_history(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    records = []
    for index in range(10):
        records.append(asdict(GameRecord(
            game_id=f"hand-{index}", timestamp=float(index), date_time="2026-10-15",
            players=["Hero", "Bot"], small_blind=5, big_blind=10, dealer_position=0,
            phases=[GamePhase("preflop", [], 20, 10, [PlayerAction("Hero", "raise", 20, 500, 480, 1.0)])],
            final_hands=[PlayerHand("Hero", ["A♠", "K♠"], 520, True, "高牌", 20)],
            total_pot=20, winner_names=["Hero"], duration_seconds=1.0,
        )))
    import json
    Path("game_history.json").write_text(json.dumps(records), encoding="utf-8")
    system = PlayerEvaluationSystem()
    result = system.get_comprehensive_evaluation("Hero")
    assert result["games_analyzed"] == 10
    assert result["style_distribution"]


def test_english_history_replay_and_training_use_one_language(tmp_path):
    import json

    records = [asdict(GameRecord(
        game_id=f"hand-{index}", timestamp=float(index), date_time="2026-10-15",
        players=["Hero", "Bot"], small_blind=5, big_blind=10, dealer_position=0,
        phases=[GamePhase("preflop", [], 20, 10, [PlayerAction("Hero", "raise", 20, 500, 480, 1.0)])],
        final_hands=[PlayerHand("Hero", ["A♠", "K♠"], 520, True, "高牌", 20)],
        total_pot=20, winner_names=["Hero"], duration_seconds=1.0,
    )) for index in range(10)]
    (tmp_path / "game_history.json").write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    responses = [
        "2", "", "2", "1", "Hero", "", "2", "", "3", "hand-9", "",
        "4", "Hero", "4", "", "5", "", "6", "1", "", "q", "",
        "7", "3", "Hero", "", "5", "Hero", "", "6", "y",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env.pop("TERM", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="\n".join(responses) + "\n", cwd=tmp_path, env=env,
        text=True, capture_output=True, timeout=15,
    )
    output = result.stdout.split("> ", 1)[-1]
    assert result.returncode == 0, result.stderr
    assert "Quick replay" in output
    assert "Training focus" in output
    assert "Hands analyzed: 10" in output
    assert not re.search(r"[\u4e00-\u9fff]", output)
    assert not result.stderr
