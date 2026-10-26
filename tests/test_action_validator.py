from texas_holdem.ai.action_validator import validate_action
from texas_holdem.ai.decision_provider import ActionResponse, GameStateSnapshot, VisiblePlayerSnapshot


def snapshot(**overrides):
    data = dict(
        game_id="g1",
        hand_id="h1",
        phase="flop",
        player_name="P1",
        position=0,
        hole_cards=["A♠", "A♥"],
        community_cards=["2♣", "7♦", "J♠"],
        pot_size=100,
        current_bet=30,
        amount_to_call=20,
        player_chips=80,
        visible_players=[VisiblePlayerSnapshot("P1", 80, 10, False, False, 0)],
        action_history=[],
        legal_actions=["fold", "call", "raise"],
        min_raise=60,
        dealer_position=0,
        small_blind=5,
        big_blind=10,
    )
    data.update(overrides)
    return GameStateSnapshot(**data)


def test_invalid_action_falls_back_to_check_when_legal():
    result = validate_action(snapshot(amount_to_call=0, legal_actions=["check", "raise", "fold"]), ActionResponse("dance", 50))
    assert result.is_valid is False
    assert result.action == "check"
    assert result.amount == 0
    assert result.original_action == "dance"
    assert "illegal" in result.reason.lower()


def test_invalid_action_falls_back_to_fold_without_check():
    result = validate_action(snapshot(), ActionResponse("check", 0))
    assert result.is_valid is False
    assert result.action == "fold"
    assert result.amount == 0
    assert "check" in result.reason.lower()


def test_raise_below_minimum_is_invalid_and_fallbacks():
    result = validate_action(snapshot(), ActionResponse("raise", 40))
    assert result.is_valid is False
    assert result.action == "fold"
    assert result.original_amount == 40
    assert "min_raise" in result.reason


def test_raise_above_stack_is_invalid_and_fallbacks():
    result = validate_action(snapshot(), ActionResponse("raise", 120))
    assert result.is_valid is False
    assert result.action == "fold"
    assert "chips" in result.reason.lower()


def test_valid_raise_keeps_amount():
    result = validate_action(snapshot(), ActionResponse("raise", 60))
    assert result.is_valid is True
    assert result.action == "raise"
    assert result.amount == 60


def test_short_stack_all_in_raise_below_minimum_is_allowed():
    result = validate_action(
        snapshot(
            current_bet=0,
            amount_to_call=0,
            player_chips=5,
            visible_players=[VisiblePlayerSnapshot("P1", 5, 0, False, False, 0)],
            legal_actions=["check", "raise", "fold"],
            min_raise=10,
        ),
        ActionResponse("raise", 5),
    )

    assert result.is_valid is True
    assert result.action == "raise"
    assert result.amount == 5
    assert "all-in" in result.reason.lower()


def test_raise_total_can_include_already_committed_chips():
    result = validate_action(
        snapshot(
            player_chips=95,
            min_raise=100,
            visible_players=[VisiblePlayerSnapshot("P1", 95, 5, False, False, 0)],
        ),
        ActionResponse("raise", 100),
    )
    assert result.is_valid is True
    assert result.action == "raise"
    assert result.amount == 100


def test_call_normalizes_to_amount_to_call():
    result = validate_action(snapshot(amount_to_call=20, player_chips=80), ActionResponse("call", 999))
    assert result.is_valid is True
    assert result.action == "call"
    assert result.amount == 20


def test_short_stack_call_normalizes_to_all_in_call_amount():
    result = validate_action(snapshot(amount_to_call=100, player_chips=35), ActionResponse("call", 100))
    assert result.is_valid is True
    assert result.action == "call"
    assert result.amount == 35
    assert "all-in" in result.reason.lower()


def test_all_in_is_allowed_when_legal():
    result = validate_action(snapshot(legal_actions=["fold", "call", "all-in"], player_chips=80), ActionResponse("all-in", 0))
    assert result.is_valid is True
    assert result.action == "all-in"
    assert result.amount == 80


def test_exception_like_inputs_do_not_raise():
    result = validate_action(snapshot(), ActionResponse(None, "bad"))
    assert result.is_valid is False
    assert result.action == "fold"
