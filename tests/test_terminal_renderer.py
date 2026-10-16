from engine_events import EngineEvent
from terminal_renderer import TerminalEventRenderer


def test_terminal_renderer_renders_hand_started():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="hand_started",
        hand_id="hand-1",
        phase="preflop",
        public_payload={
            "players": ["AI-1", "AI-2", "AI-3"],
            "small_blind": 5,
            "big_blind": 10,
            "dealer_position": 0,
            "phase": "preflop",
            "pot": 0,
            "current_bet": 0,
        },
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == ["\n==================================================", "开始新的一手牌", "=================================================="]


def test_terminal_renderer_keeps_phase_started_silent_until_explicitly_rendered():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="phase_started",
        hand_id="hand-1",
        phase="flop",
        public_payload={
            "phase": "flop",
            "community_cards": ["AS", "KD", "7C"],
            "pot": 30,
            "current_bet": 0,
        },
    )

    handled = renderer.render(event)

    assert handled is False
    assert lines == []


def test_terminal_renderer_keeps_betting_round_completed_silent_until_explicitly_rendered():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    completed = renderer.render(
        EngineEvent(
            type="betting_round_completed",
            hand_id="hand-1",
            phase="turn",
            public_payload={
                "phase": "turn",
                "continued": True,
                "pot": 80,
                "current_bet": 0,
                "active_player_names": ["AI-1", "AI-2", "AI-3"],
                "iteration_count": 3,
            },
        )
    )

    assert completed is False
    assert lines == []


def test_terminal_renderer_renders_betting_round_started():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="betting_round_started",
        hand_id="hand-1",
        phase="preflop",
        public_payload={
            "phase": "preflop",
            "pot": 15,
            "current_bet": 10,
            "active_player_names": ["AI-1", "AI-2"],
        },
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == ["\nPREFLOP 阶段下注开始"]


def test_terminal_renderer_renders_showdown_started():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="showdown_started",
        hand_id="hand-1",
        phase="river",
        public_payload={
            "phase": "river",
            "pot": 120,
            "community_cards": ["A♥", "K♦", "7♣", "2♠", "9♥"],
            "player_names": ["AI-1", "AI-2"],
        },
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == ["\n==============================", "摊牌阶段", "=============================="]


def test_terminal_renderer_renders_player_hand_revealed():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="player_hand_revealed",
        hand_id="hand-1",
        phase="river",
        public_payload={
            "player_name": "AI-1",
            "hole_cards": ["A♣", "3♠"],
            "hand_description": "一对A",
        },
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == ["AI-1: A♣ 3♠ - 一对A"]


def test_terminal_renderer_renders_cards_dealt_event():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="cards_dealt",
        hand_id="hand-1",
        phase="flop",
        public_payload={"community_cards": ["AS", "KD", "7C"]},
        metadata={"street": "flop"},
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == ["\n发放翻牌..."]


def test_terminal_renderer_renders_turn_and_river_deal_prompts():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    renderer.render(
        EngineEvent(
            type="cards_dealt",
            hand_id="hand-1",
            phase="turn",
            metadata={"street": "turn"},
        )
    )
    renderer.render(
        EngineEvent(
            type="cards_dealt",
            hand_id="hand-1",
            phase="river",
            metadata={"street": "river"},
        )
    )

    assert lines == ["\n发放转牌...", "\n发放河牌..."]


def test_terminal_renderer_renders_call_and_raise_action_applied_events():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    call_handled = renderer.render(
        EngineEvent(
            type="action_applied",
            hand_id="hand-1",
            phase="preflop",
            public_payload={
                "player_name": "AI-1",
                "action": "call",
                "amount": 10,
                "chips_before": 100,
                "chips_after": 90,
                "pot_size": 25,
                "current_bet": 10,
            },
        )
    )
    raise_handled = renderer.render(
        EngineEvent(
            type="action_applied",
            hand_id="hand-1",
            phase="preflop",
            public_payload={
                "player_name": "AI-2",
                "action": "raise",
                "amount": 30,
                "chips_before": 100,
                "chips_after": 70,
                "pot_size": 55,
                "current_bet": 40,
            },
        )
    )

    assert call_handled is True
    assert raise_handled is True
    assert lines == ["AI-1 跟注: 10", "AI-2 加注到: 40"]


def test_terminal_renderer_renders_fold_action_applied():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    handled = renderer.render(
        EngineEvent(
            type="action_applied",
            hand_id="hand-1",
            phase="preflop",
            public_payload={
                "player_name": "AI-1",
                "action": "fold",
                "amount": 0,
                "chips_before": 100,
                "chips_after": 100,
                "pot_size": 15,
                "current_bet": 10,
            },
        )
    )

    assert handled is True
    assert lines == ["✅ AI-1 弃牌"]


def test_terminal_renderer_renders_check_action_applied():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    handled = renderer.render(
        EngineEvent(
            type="action_applied",
            hand_id="hand-1",
            phase="flop",
            public_payload={
                "player_name": "Hero",
                "action": "check",
                "amount": 0,
                "chips_before": 100,
                "chips_after": 100,
                "pot_size": 15,
                "current_bet": 0,
            },
        )
    )

    assert handled is True
    assert lines == ["✅ Hero 过牌"]


def test_terminal_renderer_renders_validation_failed():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    handled = renderer.render(
        EngineEvent(
            type="validation_failed",
            hand_id="hand-1",
            phase="preflop",
            public_payload={
                "player_name": "AI-1",
                "original_action": "check",
                "original_amount": 0,
                "fallback_action": "fold",
                "reason": "check illegal when facing a bet",
            },
        )
    )

    assert handled is True
    assert lines == ["❌ AI-1 动作验证失败: check illegal when facing a bet，已改为 fold"]


def test_terminal_renderer_renders_decision_feedback():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    handled = renderer.render(
        EngineEvent(
            type="decision_feedback_displayed",
            hand_id="hand-1",
            phase="preflop",
            public_payload={
                "player_name": "Hero",
                "message": (
                    "📊 训练提示: good 80/100 | 建议倾向: call | "
                    "Call is supported."
                ),
            },
        )
    )

    assert handled is True
    assert lines == [
        "📊 训练提示: good 80/100 | 建议倾向: call | Call is supported."
    ]


def test_terminal_renderer_renders_hand_completed():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="hand_completed",
        hand_id="hand-1",
        phase="river",
        public_payload={
            "winner_names": ["AI-1"],
            "total_pot": 120,
            "final_hands": [
                {
                    "player_name": "AI-1",
                    "final_chips": 620,
                    "hand_rank": "Pair",
                    "winnings": 120,
                }
            ],
            "outcome_metadata": {"winner_reason": "fold"},
        },
    )

    handled = renderer.render(event)

    assert handled is False
    assert lines == []


def test_terminal_renderer_renders_pot_distributed():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    showdown_handled = renderer.render(
        EngineEvent(
            type="pot_distributed",
            hand_id="hand-1",
            phase="river",
            public_payload={
                "player_name": "AI-1",
                "winnings": 40,
                "winner_reason": "showdown",
                "total_pot": 40,
            },
        )
    )
    fold_handled = renderer.render(
        EngineEvent(
            type="pot_distributed",
            hand_id="hand-2",
            phase="preflop",
            public_payload={
                "player_name": "AI-2",
                "winnings": 15,
                "winner_reason": "fold",
                "total_pot": 15,
            },
        )
    )

    assert showdown_handled is True
    assert fold_handled is True
    assert lines == ["AI-1 获得 40 筹码", "💰 获得彩池: 15 筹码"]


def test_terminal_renderer_renders_winner_announced():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    handled = renderer.render(
        EngineEvent(
            type="winner_announced",
            hand_id="hand-1",
            phase="river",
            public_payload={
                "winner_names": ["AI-1", "AI-2"],
                "winner_reason": "showdown",
                "total_pot": 120,
            },
        )
    )

    assert handled is True
    assert lines == ["\n获胜者: AI-1, AI-2"]


def test_terminal_renderer_renders_fold_winner_announced():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)

    handled = renderer.render(
        EngineEvent(
            type="winner_announced",
            hand_id="hand-1",
            phase="preflop",
            public_payload={
                "winner_names": ["AI-1"],
                "winner_reason": "fold",
                "total_pot": 120,
            },
        )
    )

    assert handled is True
    assert lines == [
        "\n==============================",
        "游戏结束",
        "==============================",
        "\n🏆 AI-1 获胜！（其他玩家都已弃牌）",
    ]


def test_terminal_renderer_renders_community_cards_display():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="community_cards_displayed",
        hand_id="hand-1",
        phase="flop",
        public_payload={"community_cards": ["AS", "KD", "7C"]},
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == ["公共牌: AS KD 7C"]


def test_terminal_renderer_renders_game_state_display():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="game_state_displayed",
        hand_id="hand-1",
        phase="preflop",
        public_payload={
            "pot": 15,
            "current_bet": 10,
            "players": [
                {
                    "name": "AI-1",
                    "chips": 95,
                    "current_bet": 5,
                    "is_dealer": True,
                    "is_folded": False,
                    "is_all_in": False,
                },
                {
                    "name": "AI-2",
                    "chips": 90,
                    "current_bet": 10,
                    "is_dealer": False,
                    "is_folded": True,
                    "is_all_in": False,
                },
            ],
        },
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == [
        "\n当前彩池: 15",
        "当前最高下注: 10",
        "AI-1: 95 筹码, 本轮下注: 5 (D)",
        "AI-2: 90 筹码, 本轮下注: 10 [已弃牌]",
    ]


def test_terminal_renderer_renders_active_players_display():
    lines = []
    renderer = TerminalEventRenderer(print_fn=lines.append)
    event = EngineEvent(
        type="active_players_displayed",
        hand_id="hand-1",
        phase="preflop",
        public_payload={
            "pot": 25,
            "current_bet": 10,
            "active_count": 2,
            "total_players": 3,
            "players": [
                {
                    "name": "AI-1",
                    "chips": 95,
                    "current_bet": 5,
                    "is_dealer": True,
                    "is_folded": False,
                    "is_all_in": False,
                },
                {
                    "name": "AI-2",
                    "chips": 0,
                    "current_bet": 10,
                    "is_dealer": False,
                    "is_folded": False,
                    "is_all_in": True,
                },
                {
                    "name": "AI-3",
                    "chips": 100,
                    "current_bet": 0,
                    "is_dealer": False,
                    "is_folded": True,
                    "is_all_in": False,
                },
            ],
        },
    )

    handled = renderer.render(event)

    assert handled is True
    assert lines == [
        "\n==================================================",
        "📊 当前在场玩家状态",
        "==================================================",
        "  🎮 AI-1: 95 筹码, 本轮下注: 5 (D)",
        "  🎮 AI-2: 0 筹码, 本轮下注: 10 [全押]",
        "  ❌ AI-3: 已弃牌",
        "\n💰 当前彩池: 25",
        "📈 最高下注: 10",
        "👥 在场玩家: 2/3",
    ]
