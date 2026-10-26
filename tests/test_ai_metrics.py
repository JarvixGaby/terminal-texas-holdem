import json

from texas_holdem.analytics.ai_system_evaluator import (
    PlayerPokerMetrics,
    benchmark_ai_system,
    summarize_ai_evaluations,
)
from texas_holdem.analytics.headless_simulation import SimulationResult


def synthetic_simulation():
    return SimulationResult(
        hands_requested=2,
        hands_completed=2,
        total_actions=8,
        final_stacks={"AI-1": 120, "AI-2": 80},
        hand_summaries=[
            {
                "actions": 5,
                "winner_names": ["AI-1"],
                "final_hands": [
                    {"player_name": "AI-1", "is_winner": True},
                    {"player_name": "AI-2", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "call", "amount": 10, "decision_evaluation": {"grade": "good", "score": 80}},
                    {"phase": "preflop", "player_name": "AI-2", "action": "raise", "amount": 30, "decision_evaluation": {"grade": "poor", "score": 30}},
                    {"phase": "flop", "player_name": "AI-1", "action": "raise", "amount": 40, "decision_evaluation": {"grade": "excellent", "score": 95}},
                    {"phase": "flop", "player_name": "AI-2", "action": "call", "amount": 40, "decision_evaluation": {"grade": "questionable", "score": 55}},
                    {"phase": "turn", "player_name": "AI-2", "action": "fold", "amount": 0, "decision_evaluation": {"grade": "poor", "score": 20}},
                ],
            },
            {
                "actions": 3,
                "winner_names": ["AI-2"],
                "final_hands": [
                    {"player_name": "AI-2", "is_winner": True},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "fold", "amount": 0, "decision_evaluation": {"grade": "poor", "score": 10}},
                    {"phase": "preflop", "player_name": "AI-2", "action": "check", "amount": 0, "decision_evaluation": {"grade": "good", "score": 75}},
                    {"phase": "flop", "player_name": "AI-2", "action": "raise", "amount": 20, "decision_evaluation": {"grade": "blunder", "score": 5}},
                ],
            },
        ],
    )


def test_summarize_ai_evaluations_reports_player_poker_metrics():
    report = summarize_ai_evaluations(synthetic_simulation())

    assert set(report.player_metrics) == {"AI-1", "AI-2"}
    ai1 = report.player_metrics["AI-1"]
    ai2 = report.player_metrics["AI-2"]
    assert isinstance(ai1, PlayerPokerMetrics)

    assert ai1.hands_played == 2
    assert ai1.vpip == 0.5
    assert ai1.pfr == 0.0
    assert ai1.aggression_factor == 1.0
    assert ai1.fold_rate == 1 / 3
    assert ai1.showdown_rate == 0.5
    assert ai1.win_rate == 0.5
    assert ai1.poor_blunder_rate == 1 / 3
    assert ai1.average_decision_score == 61.666666666666664

    assert ai2.hands_played == 2
    assert ai2.vpip == 0.5
    assert ai2.pfr == 0.5
    assert ai2.aggression_factor == 2.0
    assert ai2.fold_rate == 0.2
    assert ai2.showdown_rate == 1.0
    assert ai2.win_rate == 0.5
    assert ai2.poor_blunder_rate == 0.6

    as_dict = report.to_dict()
    assert as_dict["player_metrics"]["AI-2"]["pfr"] == 0.5
    assert as_dict["player_metrics"]["AI-2"]["poor_blunder_rate"] == 0.6


def test_blind_aware_preflop_metrics_use_opportunities_and_ignore_forced_blinds():
    simulation = SimulationResult(
        hands_requested=2,
        hands_completed=2,
        total_actions=4,
        final_stacks={"SB": 100, "BB": 100},
        hand_summaries=[
            {
                "actions": 2,
                "winner_names": ["BB"],
                "outcome_metadata": {
                    "went_to_showdown": False,
                    "blind_positions": {"small_blind": "SB", "big_blind": "BB"},
                    "forced_blinds": [
                        {"player_name": "SB", "blind_type": "small_blind", "amount": 5, "is_forced": True},
                        {"player_name": "BB", "blind_type": "big_blind", "amount": 10, "is_forced": True},
                    ],
                },
                "final_hands": [
                    {"player_name": "SB", "is_winner": False},
                    {"player_name": "BB", "is_winner": True},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "SB", "action": "fold", "decision_evaluation": {"grade": "good", "score": 70}},
                    {"phase": "preflop", "player_name": "BB", "action": "check", "decision_evaluation": {"grade": "good", "score": 70}},
                ],
            },
            {
                "actions": 2,
                "winner_names": ["BB"],
                "outcome_metadata": {
                    "went_to_showdown": False,
                    "blind_positions": {"small_blind": "SB", "big_blind": "BB"},
                    "forced_blinds": [
                        {"player_name": "SB", "blind_type": "small_blind", "amount": 5, "is_forced": True},
                        {"player_name": "BB", "blind_type": "big_blind", "amount": 10, "is_forced": True},
                    ],
                },
                "final_hands": [
                    {"player_name": "SB", "is_winner": False},
                    {"player_name": "BB", "is_winner": True},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "SB", "action": "call", "amount": 10, "decision_evaluation": {"grade": "good", "score": 70}},
                    {"phase": "preflop", "player_name": "BB", "action": "raise", "amount": 30, "decision_evaluation": {"grade": "good", "score": 70}},
                ],
            },
        ],
    )

    report = summarize_ai_evaluations(simulation)

    sb = report.player_metrics["SB"]
    bb = report.player_metrics["BB"]
    assert sb.preflop_opportunities == 2
    assert bb.preflop_opportunities == 2
    assert sb.preflop_vpip_hands == 1
    assert sb.preflop_raise_hands == 0
    assert sb.vpip == 0.5
    assert sb.pfr == 0.0
    assert bb.preflop_vpip_hands == 1
    assert bb.preflop_raise_hands == 1
    assert bb.vpip == 0.5
    assert bb.pfr == 0.5


def test_profile_metrics_aggregate_players_by_style_and_fallback_unknown():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=4,
        final_stacks={"AI-1": 200, "AI-2": 100, "AI-3": 0},
        hand_summaries=[
            {
                "actions": 4,
                "winner_names": ["AI-1"],
                "ai_styles": {"AI-1": "tag", "AI-2": "tag"},
                "outcome_metadata": {"went_to_showdown": False},
                "final_hands": [
                    {"player_name": "AI-1", "is_winner": True},
                    {"player_name": "AI-2", "is_winner": False},
                    {"player_name": "AI-3", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "raise", "decision_evaluation": {"grade": "good", "score": 80}},
                    {"phase": "preflop", "player_name": "AI-2", "action": "fold", "decision_evaluation": {"grade": "poor", "score": 25}},
                    {"phase": "preflop", "player_name": "AI-3", "action": "fold", "decision_evaluation": {"grade": "blunder", "score": 5}},
                    {"phase": "flop", "player_name": "AI-1", "action": "check", "decision_evaluation": {"grade": "good", "score": 75}},
                ],
            }
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert set(report.profile_metrics) == {"tag", "unknown"}
    tag = report.profile_metrics["tag"]
    unknown = report.profile_metrics["unknown"]
    assert tag.player_count == 2
    assert tag.hands_played == 2
    assert tag.actions == 3
    assert tag.win_rate == 0.5
    assert tag.poor_blunder_rate == 1 / 3
    assert unknown.player_count == 1
    assert unknown.poor_blunder_rate == 1.0
    assert report.weakest_profile == "unknown"
    as_dict = report.to_dict()
    assert as_dict["profile_metrics"]["unknown"]["player_count"] == 1
    assert as_dict["weakest_profile"] == "unknown"


def test_showdown_rate_uses_explicit_went_to_showdown_when_available():
    simulation = SimulationResult(
        hands_requested=2,
        hands_completed=2,
        total_actions=4,
        final_stacks={"AI-1": 100, "AI-2": 100},
        hand_summaries=[
            {
                "actions": 2,
                "winner_names": ["AI-1"],
                "outcome_metadata": {"went_to_showdown": False, "ended_by_fold": True, "winner_reason": "fold"},
                "final_hands": [
                    {"player_name": "AI-1", "is_winner": True},
                    {"player_name": "AI-2", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "check", "decision_evaluation": {"grade": "good", "score": 70}},
                    {"phase": "preflop", "player_name": "AI-2", "action": "fold", "decision_evaluation": {"grade": "poor", "score": 20}},
                ],
            },
            {
                "actions": 2,
                "winner_names": ["AI-2"],
                "outcome_metadata": {"went_to_showdown": True, "ended_by_fold": False, "winner_reason": "showdown"},
                "final_hands": [
                    {"player_name": "AI-1", "is_winner": False},
                    {"player_name": "AI-2", "is_winner": True},
                ],
                "action_records": [
                    {"phase": "river", "player_name": "AI-1", "action": "check", "decision_evaluation": {"grade": "good", "score": 70}},
                    {"phase": "river", "player_name": "AI-2", "action": "check", "decision_evaluation": {"grade": "good", "score": 70}},
                ],
            },
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert report.player_metrics["AI-1"].showdown_hands == 1
    assert report.player_metrics["AI-1"].showdown_rate == 0.5
    assert report.player_metrics["AI-2"].showdown_hands == 1
    assert report.player_metrics["AI-2"].showdown_rate == 0.5


def test_player_metrics_do_not_count_final_stack_only_players_as_active_each_hand():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=1,
        final_stacks={"AI-1": 100, "AI-2": 0},
        hand_summaries=[
            {
                "actions": 1,
                "winner_names": ["AI-1"],
                "final_hands": [{"player_name": "AI-1", "is_winner": True}],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "check", "decision_evaluation": {"grade": "good", "score": 70}},
                ],
            }
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert report.player_metrics["AI-1"].hands_played == 1
    assert report.player_metrics["AI-2"].hands_played == 0


def test_benchmark_ai_system_writes_json_report(tmp_path):
    output_path = tmp_path / "benchmark.json"
    report = benchmark_ai_system(num_hands=2, player_count=4, output_path=str(output_path))

    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert data["hands_played"] == report.hands_played
    assert data["benchmark"]["hands_requested"] == 2
    assert data["benchmark"]["player_count"] == 4
    assert "player_metrics" in data
    assert set(data["final_stacks"]) == {"AI-1", "AI-2", "AI-3", "AI-4"}
