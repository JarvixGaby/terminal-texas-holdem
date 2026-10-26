from texas_holdem.engine.engine_events import EngineEvent
from texas_holdem.ai.action_validator import ValidatedAction
from texas_holdem.engine.card import Card, Rank, Suit
from texas_holdem.ai.decision_provider import ActionResponse, DecisionProvider
from texas_holdem.engine.game import TexasHoldemGame
from texas_holdem.history.game_history import GameHistoryManager
from texas_holdem.engine.player import AIPlayer, HumanPlayer


def make_game():
    players = [AIPlayer("AI-1", 100), AIPlayer("AI-2", 100)]
    game = TexasHoldemGame(players, small_blind=5, big_blind=10)
    game.current_game_id = "test-hand"
    game.active_players = players
    return game


class FixedProvider(DecisionProvider):
    def __init__(self, action: str, amount: int = 0):
        self.action = action
        self.amount = amount

    def decide(self, state):
        return ActionResponse(
            self.action,
            self.amount,
            metadata={"source": "test"},
            raw_response=(self.action, self.amount),
        )


def test_game_can_subscribe_to_engine_events():
    game = make_game()
    events = []

    game.subscribe_to_events(events.append)
    game._emit_event("phase_started", public_payload={"phase": "preflop"})

    assert len(events) == 1
    assert isinstance(events[0], EngineEvent)
    assert events[0].type == "phase_started"
    assert events[0].hand_id == "test-hand"
    assert events[0].phase == "preflop"
    assert events[0].public_payload == {"phase": "preflop"}


def test_deal_flop_emits_cards_dealt_event_without_private_cards():
    game = make_game()
    game.deck.reset()
    events = []
    game.subscribe_to_events(events.append)

    game._deal_flop()

    event = events[-1]
    serialized = repr(event.to_dict())
    assert event.type == "cards_dealt"
    assert event.phase == "flop"
    assert event.public_payload["community_cards"] == [str(card) for card in game.community_cards]
    assert event.private_payload_by_player == {}
    assert "AI-1" not in serialized
    assert "AI-2" not in serialized


def test_game_can_render_street_deal_prompt_from_engine_event():
    game = make_game()
    game.deck.reset()
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    game._deal_flop()

    assert "\n发放翻牌..." in lines


def test_display_community_cards_emits_and_renders_public_cards():
    game = make_game()
    game.community_cards = ["AS", "KD", "7C"]
    events = []
    lines = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=lines.append)

    game._display_community_cards()

    displayed = [event for event in events if event.type == "community_cards_displayed"]
    assert displayed[-1].public_payload["community_cards"] == ["AS", "KD", "7C"]
    assert lines == ["公共牌: AS KD 7C"]


def test_display_game_state_emits_and_renders_public_state():
    game = make_game()
    game.pot = 15
    game.current_bet = 10
    game.dealer_position = 0
    game.active_players[0].current_bet = 5
    game.active_players[1].current_bet = 10
    game.active_players[1].fold()
    events = []
    lines = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=lines.append)

    game._display_game_state()

    displayed = [event for event in events if event.type == "game_state_displayed"]
    payload = displayed[-1].public_payload
    serialized = repr(payload)
    assert payload["pot"] == 15
    assert payload["current_bet"] == 10
    assert payload["players"][0]["is_dealer"] is True
    assert payload["players"][1]["is_folded"] is True
    assert "hand" not in serialized.lower()
    assert "deck" not in serialized.lower()
    assert lines == [
        "\n当前彩池: 15",
        "当前最高下注: 10",
        "AI-1: 100 筹码, 本轮下注: 5 (D)",
        "AI-2: 100 筹码, 本轮下注: 10 [已弃牌]",
    ]


def test_display_active_players_emits_and_renders_public_panel():
    game = make_game()
    third = AIPlayer("AI-3", 100)
    game.active_players.append(third)
    game.pot = 25
    game.current_bet = 10
    game.dealer_position = 0
    game.active_players[0].current_bet = 5
    game.active_players[1].current_bet = 10
    game.active_players[1].is_all_in = True
    third.fold()
    events = []
    lines = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=lines.append)

    game._display_active_players()

    displayed = [event for event in events if event.type == "active_players_displayed"]
    payload = displayed[-1].public_payload
    serialized = repr(payload)
    assert payload["pot"] == 25
    assert payload["current_bet"] == 10
    assert payload["active_count"] == 2
    assert payload["players"][0]["is_dealer"] is True
    assert payload["players"][1]["is_all_in"] is True
    assert payload["players"][2]["is_folded"] is True
    assert "hand" not in serialized.lower()
    assert "deck" not in serialized.lower()
    assert lines == [
        "\n==================================================",
        "📊 当前在场玩家状态",
        "==================================================",
        "  🎮 AI-1: 100 筹码, 本轮下注: 5 (D)",
        "  🎮 AI-2: 100 筹码, 本轮下注: 10 [全押]",
        "  ❌ AI-3: 已弃牌",
        "\n💰 当前彩池: 25",
        "📈 最高下注: 10",
        "👥 在场玩家: 2/3",
    ]


def test_start_new_hand_emits_public_hand_started_event(tmp_path):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    events = []
    game.subscribe_to_events(events.append)

    assert game.start_new_hand() is True

    started = [event for event in events if event.type == "hand_started"]
    assert len(started) == 1
    event = started[0]
    payload = event.public_payload
    serialized = repr(event.to_dict()).lower()
    assert event.hand_id == game.current_game_id
    assert event.phase == "preflop"
    assert payload == {
        "players": ["AI-1", "AI-2"],
        "small_blind": 5,
        "big_blind": 10,
        "dealer_position": 0,
        "phase": "preflop",
        "pot": 0,
        "current_bet": 0,
    }
    assert event.private_payload_by_player == {}
    assert "hole" not in serialized
    assert "deck" not in serialized


def test_play_hand_routes_start_display_through_renderer(tmp_path, monkeypatch, capsys):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    monkeypatch.setattr(game, "_betting_round", lambda: False)
    monkeypatch.setattr(game, "_handle_early_winner", lambda: None)
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game.play_hand() is True

    stdout = capsys.readouterr().out
    assert "\n==================================================\n开始新的一手牌\n==================================================" not in stdout
    assert lines[:3] == [
        "\n==================================================",
        "开始新的一手牌",
        "==================================================",
    ]


def test_play_hand_routes_completion_display_through_renderer(tmp_path, monkeypatch, capsys):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.current_game_id = game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.pot = 15
    game.active_players[1].fold()
    monkeypatch.setattr(game, "start_new_hand", lambda: True)
    monkeypatch.setattr(game, "_betting_round", lambda: False)
    monkeypatch.setattr(game, "_show_instant_replay", lambda final_hands, winner_names: None)
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game.play_hand() is True

    stdout = capsys.readouterr().out
    completion_lines = [
        "\n==============================",
        "本手结束",
        "==============================",
        "\n🏆 AI-1 获胜！（其他玩家都已弃牌）",
        "💰 获得彩池: 15 筹码",
    ]
    assert "\n==============================\n游戏结束\n==============================" not in stdout
    assert "\n🏆 AI-1 获胜！（其他玩家都已弃牌）" not in stdout
    assert "💰 获得彩池: 15 筹码" not in stdout
    assert lines == completion_lines


def test_winner_routes_announcement_through_renderer_for_early_fold(tmp_path, monkeypatch, capsys):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.current_game_id = game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.pot = 15
    game.active_players[1].fold()
    monkeypatch.setattr(game, "_show_instant_replay", lambda final_hands, winner_names: None)
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    events = []
    lines = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=lines.append)

    game._handle_early_winner()

    stdout = capsys.readouterr().out
    announced = [event for event in events if event.type == "winner_announced"]
    assert len(announced) == 1
    event = announced[0]
    assert event.public_payload == {
        "winner_names": ["AI-1"],
        "winner_reason": "fold",
        "total_pot": 15,
    }
    assert event.private_payload_by_player == {}
    serialized = repr(event.to_dict()).lower()
    assert "hole" not in serialized
    assert "deck" not in serialized
    assert "\n🏆 AI-1 获胜！（其他玩家都已弃牌）" not in stdout
    assert lines.count("\n🏆 AI-1 获胜！（其他玩家都已弃牌）") == 1
    assert lines[:4] == [
        "\n==============================",
        "本手结束",
        "==============================",
        "\n🏆 AI-1 获胜！（其他玩家都已弃牌）",
    ]
    assert lines[4] == "💰 获得彩池: 15 筹码"


def test_street_deal_methods_emit_phase_started_events():
    game = make_game()
    game.deck.reset()
    events = []
    game.subscribe_to_events(events.append)

    game._deal_flop()
    game._deal_turn()
    game._deal_river()

    started = [event for event in events if event.type == "phase_started"]
    assert [event.phase for event in started] == ["flop", "turn", "river"]
    assert [event.public_payload["phase"] for event in started] == ["flop", "turn", "river"]
    assert [len(event.public_payload["community_cards"]) for event in started] == [3, 4, 5]
    for event in started:
        serialized = repr(event.to_dict()).lower()
        assert event.public_payload["pot"] == game.pot
        assert event.public_payload["current_bet"] == game.current_bet
        assert event.private_payload_by_player == {}
        assert "hole" not in serialized
        assert "deck" not in serialized


def test_betting_round_emits_started_and_completed_events(monkeypatch):
    game = make_game()
    hero, villain = game.active_players
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 15
    game.ai_action_delay_seconds = 0
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    game.set_decision_provider(hero.name, FixedProvider("call", 10))
    game.set_decision_provider(villain.name, FixedProvider("check", 0))
    events = []
    game.subscribe_to_events(events.append)

    assert game._betting_round() is True

    started = [event for event in events if event.type == "betting_round_started"]
    completed = [event for event in events if event.type == "betting_round_completed"]
    assert len(started) == 1
    assert len(completed) == 1
    assert started[0].phase == "preflop"
    assert started[0].public_payload == {
        "phase": "preflop",
        "pot": 15,
        "current_bet": 10,
        "active_player_names": ["AI-1", "AI-2"],
    }
    payload = completed[0].public_payload
    serialized = repr(completed[0].to_dict()).lower()
    assert payload["phase"] == "preflop"
    assert payload["continued"] is True
    assert payload["active_player_names"] == ["AI-1", "AI-2"]
    assert payload["pot"] == 25
    assert payload["current_bet"] == 10
    assert payload["iteration_count"] >= 1
    assert completed[0].private_payload_by_player == {}
    assert "hole" not in serialized
    assert "deck" not in serialized


def test_betting_round_routes_start_display_through_renderer(monkeypatch, capsys):
    game = make_game()
    hero, villain = game.active_players
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 15
    game.ai_action_delay_seconds = 0
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    game.set_decision_provider(hero.name, FixedProvider("call", 10))
    game.set_decision_provider(villain.name, FixedProvider("check", 0))
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game._betting_round() is True

    stdout = capsys.readouterr().out
    assert "\nPREFLOP 阶段下注开始" not in stdout
    assert "\nPREFLOP 阶段下注开始" in lines


def test_betting_round_routes_completion_display_through_renderer(monkeypatch, capsys):
    game = make_game()
    hero, villain = game.active_players
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 15
    game.ai_action_delay_seconds = 0
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    game.set_decision_provider(hero.name, FixedProvider("call", 10))
    game.set_decision_provider(villain.name, FixedProvider("check", 0))

    class SpyRenderer:
        def __init__(self):
            self.events = []

        def render(self, event):
            self.events.append(event)
            return False

    spy_renderer = SpyRenderer()
    game._terminal_event_renderer = spy_renderer
    game.render_terminal_events = True

    assert game._betting_round() is True

    stdout = capsys.readouterr().out
    completed = [
        event for event in spy_renderer.events if event.type == "betting_round_completed"
    ]
    assert len(completed) == 1
    assert completed[0].public_payload["continued"] is True
    assert stdout == ""


def test_betting_round_routes_call_print_through_action_applied_renderer(monkeypatch, capsys):
    game = make_game()
    hero, villain = game.active_players
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 15
    game.ai_action_delay_seconds = 0
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    game.set_decision_provider(hero.name, FixedProvider("call", 10))
    game.set_decision_provider(villain.name, FixedProvider("check", 0))
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game._betting_round() is True

    stdout = capsys.readouterr().out
    assert "AI-1 跟注: 10" not in stdout
    assert "AI-1 跟注: 10" in lines


def test_betting_round_routes_raise_print_through_action_applied_renderer(monkeypatch, capsys):
    game = make_game()
    hero, villain = game.active_players
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 15
    game.ai_action_delay_seconds = 0
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    game.set_decision_provider(hero.name, FixedProvider("raise", 20))
    game.set_decision_provider(villain.name, FixedProvider("call", 20))
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game._betting_round() is True

    stdout = capsys.readouterr().out
    assert "AI-1 加注到: 20" not in stdout
    assert "AI-1 加注到: 20" in lines


def test_betting_round_routes_fold_through_action_applied_renderer(monkeypatch, capsys):
    hero = HumanPlayer("Hero", 100)
    villain = AIPlayer("AI-2", 100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.current_game_id = "test-hand"
    game.active_players = [hero, villain]
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 15
    game.ai_action_delay_seconds = 0
    game.assistant_enabled = False
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    monkeypatch.setattr("builtins.input", lambda _prompt: "fold")
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game._betting_round() is False

    stdout = capsys.readouterr().out
    assert "✅ Hero 弃牌" not in stdout
    assert "✅ Hero 弃牌" in lines


def test_betting_round_routes_check_through_action_applied_renderer(monkeypatch, capsys):
    hero = HumanPlayer("Hero", 100)
    villain = AIPlayer("AI-2", 100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.current_game_id = "test-hand"
    game.active_players = [hero, villain]
    game.game_phase = "flop"
    game.current_bet = 0
    hero.current_bet = 0
    villain.current_bet = 0
    game.pot = 15
    game.ai_action_delay_seconds = 0
    game.assistant_enabled = False
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    monkeypatch.setattr("builtins.input", lambda _prompt: "check")
    game.set_decision_provider(villain.name, FixedProvider("check", 0))
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game._betting_round() is True

    stdout = capsys.readouterr().out
    assert "✅ Hero 过牌" not in stdout
    assert "✅ Hero 过牌" in lines


def test_record_processed_action_emits_action_applied_event():
    game = make_game()
    events = []
    game.subscribe_to_events(events.append)
    game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.history_manager.start_new_phase("preflop", [], 15, 10)
    game.last_action_response = ActionResponse("call", 10)
    game.last_validated_action = ValidatedAction("call", 10, True, "ok", "call", 10)

    game._record_processed_action(
        game.active_players[0],
        "call",
        10,
        chips_before=100,
        amount_to_call=10,
        legal_actions=["call", "raise", "fold"],
        min_raise=20,
        decision_pot_size=15,
        decision_player_chips=100,
        decision_current_bet=10,
    )

    action_events = [event for event in events if event.type == "action_applied"]
    assert action_events[-1].public_payload["player_name"] == "AI-1"
    assert action_events[-1].public_payload["action"] == "call"
    assert action_events[-1].public_payload["amount"] == 10


def test_invalid_provider_action_emits_validation_failed_event():
    game = make_game()
    events = []
    game.subscribe_to_events(events.append)
    game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.history_manager.start_new_phase("preflop", [], 15, 10)
    game.last_action_response = ActionResponse("check", 0)
    game.last_validated_action = ValidatedAction("fold", 0, False, "check illegal when facing a bet", "check", 0)

    game._record_processed_action(
        game.active_players[0],
        "fold",
        0,
        chips_before=100,
        amount_to_call=10,
        legal_actions=["call", "raise", "fold"],
        min_raise=20,
        decision_pot_size=15,
        decision_player_chips=100,
        decision_current_bet=10,
    )

    failed_events = [event for event in events if event.type == "validation_failed"]
    assert failed_events[-1].public_payload["player_name"] == "AI-1"
    assert failed_events[-1].public_payload["fallback_action"] == "fold"
    assert "check illegal" in failed_events[-1].public_payload["reason"]


def test_validation_routes_failure_display_through_renderer(monkeypatch, capsys):
    game = make_game()
    hero, villain = game.active_players
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 15
    game.ai_action_delay_seconds = 0
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])
    game.set_decision_provider(hero.name, FixedProvider("check", 0))
    game.set_decision_provider(villain.name, FixedProvider("check", 0))
    lines = []
    game.enable_terminal_event_rendering(print_fn=lines.append)

    assert game._betting_round() is False

    stdout = capsys.readouterr().out
    validation_line = "❌ AI-1 动作验证失败: illegal action: check，已改为 fold"
    fallback_line = "✅ AI-1 弃牌"
    assert validation_line not in stdout
    assert lines.count(validation_line) == 1
    assert lines.index(validation_line) < lines.index(fallback_line)


def test_decision_feedback_routes_display_through_renderer(monkeypatch, capsys):
    hero = HumanPlayer("Hero", 100)
    villain = AIPlayer("AI-2", 100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.current_game_id = "test-hand"
    game.active_players = [hero, villain]
    game.game_phase = "preflop"
    game.current_bet = 10
    game.pot = 25
    game.history_manager.start_new_game_record(["Hero", "AI-2"], 5, 10, 0)
    game.history_manager.start_new_phase("preflop", [], 25, 10)
    evaluation = {
        "grade": "good",
        "score": 80.0,
        "recommended_action": "call",
        "reasoning": "Call is supported.",
    }
    monkeypatch.setattr(game, "_evaluate_player_decision", lambda *args, **kwargs: evaluation)
    events = []
    lines = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=lines.append)

    game._record_processed_action(
        hero,
        "call",
        10,
        chips_before=100,
        amount_to_call=10,
        legal_actions=["call", "raise", "fold"],
        min_raise=20,
        decision_pot_size=25,
        decision_player_chips=100,
        decision_current_bet=10,
    )

    stdout = capsys.readouterr().out
    feedback_events = [event for event in events if event.type == "decision_feedback_displayed"]
    assert len(feedback_events) == 1
    event = feedback_events[0]
    expected_feedback = "📊 训练提示: good 80/100 | 建议倾向: call | Call is supported."
    assert event.public_payload == {
        "player_name": "Hero",
        "message": expected_feedback,
    }
    assert event.private_payload_by_player == {}
    serialized = repr(event.to_dict()).lower()
    assert "hole" not in serialized
    assert "deck" not in serialized
    assert expected_feedback not in stdout
    assert lines.count("Hero 跟注: 10") == 1
    assert lines.count(expected_feedback) == 1
    assert lines.index("Hero 跟注: 10") < lines.index(expected_feedback)

    game._record_processed_action(
        villain,
        "check",
        0,
        chips_before=100,
        amount_to_call=0,
        legal_actions=["check", "raise", "fold"],
        min_raise=20,
        decision_pot_size=25,
        decision_player_chips=100,
        decision_current_bet=10,
    )

    assert len([event for event in events if event.type == "decision_feedback_displayed"]) == 1
    assert lines.count(expected_feedback) == 1


def test_early_winner_emits_hand_completed_without_private_payload(tmp_path, monkeypatch):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game._show_instant_replay = lambda final_hands, winner_names: None
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    game.pot = 15
    game.active_players[1].fold()
    events = []
    game.subscribe_to_events(events.append)
    game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)

    game._handle_early_winner()

    completed = [event for event in events if event.type == "hand_completed"][-1]
    serialized = repr(completed.to_dict())
    assert completed.public_payload["winner_names"] == ["AI-1"]
    assert completed.public_payload["total_pot"] == 15
    assert completed.public_payload["outcome_metadata"]["ended_by_fold"] is True
    assert completed.private_payload_by_player == {}
    assert "hole_cards" not in serialized


def test_showdown_routes_start_display_through_renderer(tmp_path, monkeypatch):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.current_game_id = game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.game_phase = "river"
    game.pot = 40
    game.community_cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.SPADES, Rank.TWO),
        Card(Suit.HEARTS, Rank.NINE),
    ]
    game.active_players[0].hand = [
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.SPADES, Rank.THREE),
    ]
    game.active_players[1].hand = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.JACK),
    ]
    monkeypatch.setattr(game, "_show_instant_replay", lambda final_hands, winner_names: None)
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    events = []
    trace = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=trace.append)
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: trace.append(" ".join(str(arg) for arg in args)))

    game._showdown()

    started = [event for event in events if event.type == "showdown_started"]
    assert len(started) == 1
    event = started[0]
    serialized = repr(event.to_dict()).lower()
    assert event.phase == "river"
    assert event.public_payload == {
        "phase": "river",
        "pot": 40,
        "community_cards": ["A♥", "K♦", "7♣", "2♠", "9♥"],
        "player_names": ["AI-1", "AI-2"],
    }
    assert event.private_payload_by_player == {}
    assert "hole" not in serialized
    assert "a♣" not in serialized
    assert "3♠" not in serialized
    assert "q♦" not in serialized
    assert "j♣" not in serialized
    assert trace.count("摊牌阶段") == 1
    assert trace[:3] == ["\n==============================", "摊牌阶段", "=============================="]
    assert trace.index("摊牌阶段") < trace.index("\n参与摊牌的玩家: AI-1, AI-2")


def test_showdown_routes_hand_reveal_through_renderer(tmp_path, monkeypatch):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.current_game_id = game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.game_phase = "river"
    game.pot = 40
    game.community_cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.SPADES, Rank.TWO),
        Card(Suit.HEARTS, Rank.NINE),
    ]
    game.active_players[0].hand = [
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.SPADES, Rank.THREE),
    ]
    game.active_players[1].hand = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.JACK),
    ]
    monkeypatch.setattr(game, "_show_instant_replay", lambda final_hands, winner_names: None)
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    events = []
    trace = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=trace.append)
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: trace.append(" ".join(str(arg) for arg in args)))

    game._showdown()

    reveal_events = [event for event in events if event.type == "player_hand_revealed"]
    assert [event.public_payload["player_name"] for event in reveal_events] == ["AI-1", "AI-2"]
    assert reveal_events[0].public_payload["hole_cards"] == ["A♣", "3♠"]
    assert reveal_events[1].public_payload["hole_cards"] == ["Q♦", "J♣"]
    assert all(event.private_payload_by_player == {} for event in reveal_events)
    assert all("hand_description" in event.public_payload for event in reveal_events)
    assert all(event.to_dict()["public_payload"]["hole_cards"] for event in reveal_events)

    first_reveal_line = (
        f"AI-1: {' '.join(reveal_events[0].public_payload['hole_cards'])} - "
        f"{reveal_events[0].public_payload['hand_description']}"
    )
    second_reveal_line = (
        f"AI-2: {' '.join(reveal_events[1].public_payload['hole_cards'])} - "
        f"{reveal_events[1].public_payload['hand_description']}"
    )
    assert trace.count(first_reveal_line) == 1
    assert trace.count(second_reveal_line) == 1
    assert trace.index("\n参与摊牌的玩家: AI-1, AI-2") < trace.index(first_reveal_line)
    assert trace.index(first_reveal_line) < trace.index(second_reveal_line)


def test_winner_routes_announcement_through_renderer_for_showdown(tmp_path, monkeypatch):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.current_game_id = game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.game_phase = "river"
    game.pot = 40
    game.community_cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.SPADES, Rank.TWO),
        Card(Suit.HEARTS, Rank.NINE),
    ]
    game.active_players[0].hand = [
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.SPADES, Rank.THREE),
    ]
    game.active_players[1].hand = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.JACK),
    ]
    monkeypatch.setattr(game, "_show_instant_replay", lambda final_hands, winner_names: None)
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    events = []
    trace = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=trace.append)
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: trace.append(" ".join(str(arg) for arg in args)))

    game._showdown()

    announced = [event for event in events if event.type == "winner_announced"]
    assert len(announced) == 1
    event = announced[0]
    assert event.public_payload == {
        "winner_names": ["AI-1"],
        "winner_reason": "showdown",
        "total_pot": 40,
    }
    assert event.private_payload_by_player == {}
    serialized = repr(event.to_dict()).lower()
    assert "hole" not in serialized
    assert "deck" not in serialized
    second_reveal = [event for event in events if event.type == "player_hand_revealed"][1]
    second_reveal_line = (
        f"AI-2: {' '.join(second_reveal.public_payload['hole_cards'])} - "
        f"{second_reveal.public_payload['hand_description']}"
    )
    assert trace.count("\n获胜者: AI-1") == 1
    assert trace.index("\n获胜者: AI-1") > trace.index(second_reveal_line)
    assert trace.index("\n获胜者: AI-1") < trace.index("AI-1 获得 40 筹码")


def test_pot_distribution_routes_display_through_renderer(tmp_path, monkeypatch):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.current_game_id = game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.game_phase = "river"
    game.pot = 40
    game.community_cards = [
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.SEVEN),
        Card(Suit.SPADES, Rank.TWO),
        Card(Suit.HEARTS, Rank.NINE),
    ]
    game.active_players[0].hand = [
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.SPADES, Rank.THREE),
    ]
    game.active_players[1].hand = [
        Card(Suit.DIAMONDS, Rank.QUEEN),
        Card(Suit.CLUBS, Rank.JACK),
    ]
    monkeypatch.setattr(game, "_show_instant_replay", lambda final_hands, winner_names: None)
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    events = []
    trace = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=trace.append)
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: trace.append(" ".join(str(arg) for arg in args)))

    game._showdown()

    distributed = [event for event in events if event.type == "pot_distributed"]
    assert len(distributed) == 1
    event = distributed[0]
    assert event.public_payload == {
        "player_name": "AI-1",
        "winnings": 40,
        "winner_reason": "showdown",
        "total_pot": 40,
    }
    assert event.private_payload_by_player == {}
    serialized = repr(event.to_dict()).lower()
    assert "hole" not in serialized
    assert "deck" not in serialized
    assert "a♣" not in serialized
    assert "3♠" not in serialized
    assert trace.count("AI-1 获得 40 筹码") == 1
    assert trace.index("\n获胜者: AI-1") < trace.index("AI-1 获得 40 筹码")


def test_early_fold_pot_distribution_routes_display_through_renderer(tmp_path, monkeypatch, capsys):
    game = make_game()
    game.history_manager = GameHistoryManager(str(tmp_path / "history.json"))
    game.current_game_id = game.history_manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    game.pot = 15
    game.active_players[1].fold()
    monkeypatch.setattr(game, "_show_instant_replay", lambda final_hands, winner_names: None)
    monkeypatch.setattr("texas_holdem.engine.game.player_style_analyzer.save_stats", lambda: None)
    events = []
    lines = []
    game.subscribe_to_events(events.append)
    game.enable_terminal_event_rendering(print_fn=lines.append)

    game._handle_early_winner()

    stdout = capsys.readouterr().out
    distributed = [event for event in events if event.type == "pot_distributed"]
    assert len(distributed) == 1
    event = distributed[0]
    assert event.public_payload == {
        "player_name": "AI-1",
        "winnings": 15,
        "winner_reason": "fold",
        "total_pot": 15,
    }
    assert event.private_payload_by_player == {}
    serialized = repr(event.to_dict()).lower()
    assert "hole" not in serialized
    assert "deck" not in serialized
    assert "💰 获得彩池: 15 筹码" not in stdout
    assert lines.count("💰 获得彩池: 15 筹码") == 1
    assert lines.index("\n🏆 AI-1 获胜！（其他玩家都已弃牌）") < lines.index("💰 获得彩池: 15 筹码")
