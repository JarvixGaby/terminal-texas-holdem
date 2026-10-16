from game_rules import (
    BettingStructure,
    BlindStructure,
    GameRules,
    StackProfile,
    create_rules,
)


def test_stack_profile_calculates_starting_chips_from_big_blind():
    profile = StackProfile("short", 20)

    assert profile.starting_chips_for(big_blind=10) == 200


def test_create_rules_builds_no_limit_holdem_rule_config():
    rules = create_rules(
        blind_structure=BlindStructure(5, 10),
        stack_profile=StackProfile("standard", 50),
    )

    assert isinstance(rules, GameRules)
    assert rules.variant == "texas_holdem"
    assert rules.betting_structure == BettingStructure.NO_LIMIT
    assert rules.small_blind == 5
    assert rules.big_blind == 10
    assert rules.starting_chips == 500
    assert rules.stack_profile == "standard"
    assert rules.allow_short_all_in is True
    assert rules.max_raises_per_street is None


def test_custom_rules_reject_invalid_blinds():
    try:
        create_rules(
            blind_structure=BlindStructure(10, 10),
            stack_profile=StackProfile("standard", 50),
        )
    except ValueError as exc:
        assert "big blind" in str(exc).lower()
    else:
        raise AssertionError("expected invalid blind structure to raise")
