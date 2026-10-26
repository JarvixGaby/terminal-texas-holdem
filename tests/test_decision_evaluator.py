import pytest

from texas_holdem.ai.decision_evaluator import (
    DecisionContext,
    DecisionEvaluation,
    calculate_pot_odds,
    evaluate_decision,
)


def test_decision_context_defaults_use_independent_empty_lists():
    first = DecisionContext()
    second = DecisionContext()

    assert first.phase == "preflop"
    assert first.opponent_count == 1
    assert first.estimated_equity is None

    first.hole_cards.append("As")
    first.legal_actions.append("call")

    assert second.hole_cards == []
    assert second.legal_actions == []


def test_decision_evaluation_defaults_use_independent_containers():
    first = DecisionEvaluation(
        grade="good",
        score=80,
        recommended_action="call",
        reasoning="profitable call",
    )
    second = DecisionEvaluation(
        grade="good",
        score=80,
        recommended_action="call",
        reasoning="profitable call",
    )

    first.risk_tags.append("tag")
    first.metrics["equity"] = 0.5

    assert second.risk_tags == []
    assert second.metrics == {}


@pytest.mark.parametrize(
    "pot_size,amount_to_call,expected",
    [
        (100, 25, 0.2),
        (60, 40, 0.4),
        (100, 0, 0.0),
        (100, -10, 0.0),
        (-50, 50, 0.0),
        (-49, 50, 0.0),
        (-1, 2, 0.0),
    ],
)
def test_calculate_pot_odds(pot_size, amount_to_call, expected):
    assert calculate_pot_odds(pot_size, amount_to_call) == pytest.approx(expected)


def test_illegal_action_is_blunder_with_low_score():
    evaluation = evaluate_decision(
        DecisionContext(action_taken="raise", legal_actions=["fold", "call"])
    )

    assert evaluation.grade == "blunder"
    assert evaluation.score <= 10
    assert evaluation.recommended_action in {"fold", "call"}
    assert "illegal" in evaluation.reasoning.lower()


def test_action_matching_strips_whitespace_and_ignores_case():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=25,
            estimated_equity=0.35,
            action_taken=" CALL ",
            legal_actions=["Fold", "Call"],
        )
    )

    assert evaluation.grade in {"good", "excellent"}
    assert evaluation.recommended_action == "call"


def test_all_in_action_variant_is_treated_as_raise_like_for_risk_rule():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=10,
            player_chips=100,
            estimated_equity=0.15,
            action_taken=" ALL_IN ",
            amount=100,
            legal_actions=["fold", "call", "all-in"],
        )
    )

    assert evaluation.grade == "poor"
    assert "high_risk_bluff" in evaluation.risk_tags


def test_all_in_is_legal_when_raise_is_legal_and_player_shoves():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=10,
            player_chips=100,
            estimated_equity=0.45,
            action_taken="all-in",
            amount=100,
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade != "blunder"
    assert "illegal_action" not in evaluation.risk_tags


def test_all_in_recommendation_filters_raise_like_actions_when_possible():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=10,
            player_chips=100,
            estimated_equity=0.15,
            action_taken="all-in",
            amount=100,
            legal_actions=["fold", "call", "all-in"],
        )
    )

    assert evaluation.recommended_action == "fold"


def test_illegal_raise_amount_is_blunder_with_low_score():
    evaluation = evaluate_decision(
        DecisionContext(
            action_taken="raise",
            amount=20,
            min_raise=40,
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade == "blunder"
    assert evaluation.score <= 10
    assert evaluation.recommended_action != "raise"
    assert "minimum raise" in evaluation.reasoning.lower()


def test_short_stack_all_in_raise_below_minimum_is_not_illegal():
    evaluation = evaluate_decision(
        DecisionContext(
            action_taken="raise",
            amount=9,
            min_raise=10,
            player_chips=9,
            pot_size=77,
            amount_to_call=0,
            estimated_equity=0.94,
            legal_actions=["check", "raise"],
        )
    )

    assert evaluation.grade != "blunder"
    assert "illegal_raise_amount" not in evaluation.risk_tags


def test_call_far_below_pot_odds_is_blunder_and_tagged():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=50,
            estimated_equity=0.10,
            action_taken="call",
            legal_actions=["fold", "call"],
        )
    )

    assert evaluation.grade in {"poor", "blunder"}
    assert evaluation.score <= 40
    assert evaluation.recommended_action == "fold"
    assert "negative_pot_odds_call" in evaluation.risk_tags
    assert evaluation.metrics["pot_odds"] == pytest.approx(1 / 3)
    assert evaluation.metrics["equity_edge"] == pytest.approx(0.10 - (1 / 3))


def test_preflop_strong_hand_call_is_not_negative_pot_odds_from_noisy_equity():
    evaluation = evaluate_decision(
        DecisionContext(
            phase="preflop",
            hole_cards=["A♣", "A♠"],
            community_cards=[],
            pot_size=15,
            amount_to_call=10,
            estimated_equity=0.20,
            action_taken="call",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade == "good"
    assert evaluation.recommended_action == "call"
    assert "negative_pot_odds_call" not in evaluation.risk_tags
    assert "preflop_raw_equity_uncertain" in evaluation.risk_tags


def test_preflop_non_strong_pair_call_can_still_be_negative_pot_odds():
    evaluation = evaluate_decision(
        DecisionContext(
            phase="preflop",
            hole_cards=["6♣", "6♦"],
            community_cards=[],
            pot_size=15,
            amount_to_call=10,
            estimated_equity=0.20,
            action_taken="call",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade in {"poor", "blunder"}
    assert "negative_pot_odds_call" in evaluation.risk_tags


def test_profitable_call_is_good_or_excellent():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=25,
            estimated_equity=0.35,
            action_taken="call",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade in {"good", "excellent"}
    assert evaluation.score >= 75
    assert evaluation.recommended_action == "call"
    assert evaluation.metrics["equity"] == pytest.approx(0.35)
    assert evaluation.metrics["pot_odds"] == pytest.approx(0.2)
    assert evaluation.metrics["equity_edge"] == pytest.approx(0.15)


def test_call_exactly_at_pot_odds_is_good():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=25,
            estimated_equity=0.20,
            action_taken="call",
            legal_actions=["fold", "call"],
        )
    )

    assert evaluation.grade == "good"
    assert evaluation.recommended_action == "call"


def test_fold_far_above_pot_odds_is_overfold_poor():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=25,
            estimated_equity=0.55,
            action_taken="fold",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade == "poor"
    assert evaluation.recommended_action == "call"
    assert "overfold" in evaluation.risk_tags


def test_preflop_trash_offsuit_fold_does_not_recommend_call_from_raw_equity_only():
    evaluation = evaluate_decision(
        DecisionContext(
            phase="preflop",
            hole_cards=["9♣", "3♦"],
            community_cards=[],
            pot_size=43,
            amount_to_call=18,
            estimated_equity=0.35,
            action_taken="fold",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade == "good"
    assert evaluation.recommended_action == "fold"
    assert "poor_preflop_playability" in evaluation.risk_tags
    assert "realization" in evaluation.reasoning.lower() or "playability" in evaluation.reasoning.lower()


def test_preflop_trash_offsuit_call_is_questionable_even_when_raw_equity_beats_price():
    evaluation = evaluate_decision(
        DecisionContext(
            phase="preflop",
            hole_cards=["9♣", "3♦"],
            community_cards=[],
            pot_size=43,
            amount_to_call=18,
            estimated_equity=0.35,
            action_taken="call",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade in {"questionable", "poor"}
    assert evaluation.recommended_action == "fold"
    assert "poor_preflop_playability" in evaluation.risk_tags


def test_preflop_playable_pair_still_recommends_profitable_call():
    evaluation = evaluate_decision(
        DecisionContext(
            phase="preflop",
            hole_cards=["6♣", "6♥"],
            community_cards=[],
            pot_size=42,
            amount_to_call=10,
            estimated_equity=0.42,
            action_taken="call",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade in {"good", "excellent"}
    assert evaluation.recommended_action == "call"
    assert "poor_preflop_playability" not in evaluation.risk_tags


def test_preflop_suited_weak_fold_is_not_overfold_from_noisy_raw_equity_only():
    evaluation = evaluate_decision(
        DecisionContext(
            phase="preflop",
            hole_cards=["Q♠", "6♠"],
            community_cards=[],
            pot_size=15,
            amount_to_call=5,
            estimated_equity=0.80,
            action_taken="fold",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade == "good"
    assert evaluation.recommended_action == "fold"
    assert "overfold" not in evaluation.risk_tags


def test_preflop_premium_fold_still_flags_overfold():
    evaluation = evaluate_decision(
        DecisionContext(
            phase="preflop",
            hole_cards=["A♠", "A♥"],
            community_cards=[],
            pot_size=15,
            amount_to_call=5,
            estimated_equity=0.85,
            action_taken="fold",
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade == "poor"
    assert evaluation.recommended_action == "call"
    assert "overfold" in evaluation.risk_tags


def test_strong_equity_check_with_no_bet_misses_value_when_raise_legal():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=0,
            estimated_equity=0.82,
            action_taken="check",
            legal_actions=["check", "raise"],
            min_raise=20,
        )
    )

    assert evaluation.grade == "questionable"
    assert evaluation.recommended_action == "raise"
    assert "missed_value" in evaluation.risk_tags


def test_strong_equity_call_small_bet_misses_value_when_raise_legal():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=200,
            amount_to_call=20,
            estimated_equity=0.80,
            action_taken="call",
            legal_actions=["fold", "call", "raise"],
            min_raise=40,
        )
    )

    assert evaluation.grade == "questionable"
    assert evaluation.recommended_action == "raise"
    assert "missed_value" in evaluation.risk_tags


def test_strong_equity_call_any_bet_misses_value_when_raise_legal():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=50,
            estimated_equity=0.80,
            action_taken="call",
            legal_actions=["fold", "call", "raise"],
            min_raise=100,
        )
    )

    assert evaluation.grade == "questionable"
    assert evaluation.recommended_action == "raise"
    assert "missed_value" in evaluation.risk_tags


def test_strong_equity_call_is_not_missed_value_when_raise_not_legal():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=200,
            amount_to_call=20,
            estimated_equity=0.80,
            action_taken="call",
            legal_actions=["fold", "call"],
        )
    )

    assert evaluation.grade in {"good", "excellent"}
    assert "missed_value" not in evaluation.risk_tags
    assert evaluation.recommended_action == "call"


def test_low_equity_all_in_or_large_raise_is_high_risk_bluff():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=10,
            player_chips=100,
            estimated_equity=0.15,
            action_taken="raise",
            amount=100,
            min_raise=20,
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert evaluation.grade == "poor"
    assert evaluation.score <= 40
    assert evaluation.recommended_action == "fold"
    assert "high_risk_bluff" in evaluation.risk_tags


def test_equity_at_low_equity_boundary_is_not_high_risk_bluff():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=10,
            player_chips=100,
            estimated_equity=0.20,
            action_taken="raise",
            amount=100,
            min_raise=20,
            legal_actions=["fold", "call", "raise"],
        )
    )

    assert "high_risk_bluff" not in evaluation.risk_tags


def test_context_pot_odds_overrides_calculated_value_in_metrics():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=25,
            pot_odds=0.30,
            estimated_equity=0.40,
            action_taken="call",
            legal_actions=["fold", "call"],
        )
    )

    assert evaluation.metrics["pot_odds"] == pytest.approx(0.30)
    assert evaluation.metrics["equity_edge"] == pytest.approx(0.10)


def test_metrics_always_include_required_keys_when_equity_unknown():
    evaluation = evaluate_decision(
        DecisionContext(
            pot_size=100,
            amount_to_call=0,
            estimated_equity=None,
            action_taken="check",
            legal_actions=["check"],
        )
    )

    assert set(evaluation.metrics) >= {"equity", "pot_odds", "equity_edge"}
    assert evaluation.metrics["equity"] is None
    assert evaluation.metrics["equity_edge"] is None
