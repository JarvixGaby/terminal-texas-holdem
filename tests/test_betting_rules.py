from texas_holdem.engine.betting_rules import NoLimitBettingRules


def test_no_limit_min_raise_uses_last_full_raise_increment():
    rules = NoLimitBettingRules(big_blind=10)

    assert rules.minimum_raise_total(current_bet=10, last_full_raise_increment=10) == 20
    assert rules.minimum_raise_total(current_bet=25, last_full_raise_increment=15) == 40


def test_short_stack_all_in_below_minimum_is_legal_but_not_full_raise():
    rules = NoLimitBettingRules(big_blind=10)

    assert rules.is_raise_legal(
        target_total=25,
        current_bet=20,
        player_current_bet=20,
        player_chips=5,
        last_full_raise_increment=10,
    )
    assert not rules.is_full_raise(
        target_total=25,
        previous_current_bet=20,
        last_full_raise_increment=10,
    )


def test_full_raise_reopens_action():
    rules = NoLimitBettingRules(big_blind=10)

    assert rules.is_full_raise(
        target_total=30,
        previous_current_bet=20,
        last_full_raise_increment=10,
    )


def test_legal_actions_allow_short_all_in_bet_when_below_big_blind():
    rules = NoLimitBettingRules(big_blind=10)

    actions = rules.legal_actions(
        amount_to_call=0,
        current_bet=0,
        player_current_bet=0,
        player_chips=5,
        last_full_raise_increment=10,
    )

    assert actions == ["check", "raise", "fold"]
