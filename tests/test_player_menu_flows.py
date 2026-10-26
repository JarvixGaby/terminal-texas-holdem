from types import SimpleNamespace

import main
from texas_holdem.history.game_history import GameHistoryManager, GamePhase, GameRecord, PlayerAction, PlayerHand


def make_ui(monkeypatch):
    record = GameRecord(
        game_id="hand-1",
        timestamp=1.0,
        date_time="2026-10-15 12:00",
        players=["玩家1", "机器人Alice"],
        small_blind=5,
        big_blind=10,
        dealer_position=0,
        phases=[GamePhase("preflop", [], 20, 10, [
            PlayerAction("玩家1", "call", 10, 500, 490, 1.0),
            PlayerAction("机器人Alice", "fold", 0, 495, 495, 2.0),
        ])],
        final_hands=[PlayerHand("玩家1", ["A♠", "K♠"], 510, True, "高牌", 20)],
        total_pot=20,
        winner_names=["玩家1"],
        duration_seconds=2.0,
    )
    manager = GameHistoryManager(history_file="unused-history.json")
    monkeypatch.setattr(manager, "_load_all_games", lambda: [record])
    replayed = []
    ui = object.__new__(main.EnhancedTexasHoldemUI)
    ui.history_viewer = SimpleNamespace(
        history_manager=manager,
        enter_replay_mode=replayed.append,
    )
    ui.optimized_system = None
    ui.game = None
    ui.clear_screen = lambda: None
    return ui, record, replayed


def test_history_menu_reads_saved_hands_and_replay(monkeypatch, capsys):
    ui, record, replayed = make_ui(monkeypatch)
    names = iter(["玩家1", "hand-1", "玩家1"])
    monkeypatch.setattr(main, "safe_str_input", lambda *args, **kwargs: next(names))
    monkeypatch.setattr(main, "safe_int_input", lambda *args, **kwargs: 1)
    monkeypatch.setattr(main, "safe_choice_input", lambda *args, **kwargs: "4")

    ui._view_player_stats()
    ui._browse_recent_games()
    ui._search_specific_game()
    ui._show_data_visualization()
    ui._show_leaderboard()
    ui._quick_replay()

    output = capsys.readouterr().out
    assert "总局数: 1" in output
    assert "hand-1" in output
    assert "动作分布" in output
    assert "1. 玩家1: 1 胜 / 1 手牌" in output
    assert replayed == [record]
    assert "失败" not in output


def test_main_menu_hides_internal_update_messages(monkeypatch, capsys):
    ui, _, _ = make_ui(monkeypatch)
    monkeypatch.setattr(ui, "display_welcome", lambda: None)
    monkeypatch.setattr(main, "safe_choice_input", lambda *args, **kwargs: "6")
    monkeypatch.setattr(main, "safe_confirm_input", lambda *args, **kwargs: True)
    monkeypatch.setattr(main, "log_game_event", lambda *args, **kwargs: None)

    ui.run_game()

    output = capsys.readouterr().out
    assert "玩家风格评测" in output
    assert "优化增强版" not in output
    assert "优化系统管理" not in output
    assert "感谢游戏" in output


def test_new_game_settings_allow_nine_computer_opponents(monkeypatch):
    ui = object.__new__(main.EnhancedTexasHoldemUI)
    ui.clear_screen = lambda: None
    input_calls = []

    def capture_int_input(*args, **kwargs):
        input_calls.append((args, kwargs))
        return kwargs["max_val"]

    monkeypatch.setattr(main, "safe_int_input", capture_int_input)
    monkeypatch.setattr(main, "safe_str_input", lambda *args, **kwargs: "Human")
    monkeypatch.setattr(main, "log_user_action", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        ui, "_get_rule_settings",
        lambda: SimpleNamespace(small_blind=5, big_blind=10, starting_chips=1000),
    )

    settings = ui.get_game_settings()

    assert settings["ai_count"] == 9
    prompt, options = input_calls[0]
    assert "1-9" in prompt[0]
    assert options["min_val"] == 1
    assert options["max_val"] == 9


def test_finished_game_returns_to_menu_without_error(monkeypatch, capsys):
    ui, _, _ = make_ui(monkeypatch)
    players = [SimpleNamespace(name="玩家1", chips=500)]

    class FinishedGame:
        def __init__(self, **kwargs):
            self.players = players

        def is_game_over(self):
            return False

        def play_hand(self):
            return False

    monkeypatch.setattr(main, "TexasHoldemGame", FinishedGame)
    monkeypatch.setattr(main, "log_game_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "log_user_action", lambda *args, **kwargs: None)
    monkeypatch.setattr("builtins.input", lambda *args: "")
    monkeypatch.setattr(ui, "display_game_info", lambda *args: None)

    ui.run_main_game_loop(
        {'small_blind': 5, 'big_blind': 10, 'rules': None}, players,
    )

    output = capsys.readouterr().out
    assert "最终排名" in output
    assert "游戏初始化失败" not in output
