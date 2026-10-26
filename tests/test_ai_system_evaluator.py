import json

from texas_holdem.analytics.ai_system_evaluator import (
    AISystemEvaluationReport,
    benchmark_ai_system,
    benchmark_ai_system_multi_seed,
    evaluate_ai_system,
    evaluate_benchmark_gates,
    summarize_ai_evaluations,
)
from texas_holdem.analytics.headless_simulation import SimulationResult


def test_evaluate_ai_system_returns_report_and_dict():
    report = evaluate_ai_system(num_hands=3, player_count=4)
    assert isinstance(report, AISystemEvaluationReport)
    assert report.hands_played > 0
    assert report.total_actions > 0
    assert 0 <= report.illegal_action_rate <= 1
    assert 0 <= report.average_decision_score <= 100
    assert sum(report.grade_distribution.values()) > 0
    assert set(report.final_stacks.keys()) == {"AI-1", "AI-2", "AI-3", "AI-4"}
    as_dict = report.to_dict()
    assert as_dict["hands_played"] == report.hands_played
    assert as_dict["hands"] == report.hands_played
    assert as_dict["actions"] == report.total_actions
    assert as_dict["final_stacks"] == report.final_stacks
    assert "style_separability_score" in as_dict
    assert "vpip_spread" in as_dict
    assert "pfr_spread" in as_dict
    assert "aggression_spread" in as_dict
    assert "call_rate_spread" in as_dict


def test_summarize_ai_evaluations_counts_illegal_risk_tags():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=2,
        hand_summaries=[
            {
                "actions": 2,
                "decision_evaluations": [
                    {"grade": "blunder", "score": 5, "risk_tags": ["illegal_action"]},
                    {"grade": "good", "score": 80, "risk_tags": []},
                ],
            }
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert report.total_actions == 2
    assert report.illegal_action_rate == 0.5
    assert report.grade_distribution == {"blunder": 1, "good": 1}
    assert report.average_decision_score == 42.5


def test_evaluate_ai_system_handles_no_data_safely():
    report = evaluate_ai_system(num_hands=0, player_count=4)
    assert report.hands_played == 0
    assert report.total_actions == 0
    assert report.illegal_action_rate == 0
    assert report.average_decision_score == 0
    assert report.grade_distribution == {}
    assert report.errors == []
    assert report.style_separability_score == 0
    assert report.vpip_spread == 0
    assert report.pfr_spread == 0
    assert report.aggression_spread == 0
    assert report.call_rate_spread == 0


def _style_separability_simulation() -> SimulationResult:
    hand_summaries = []
    actions_by_player = {
        "Nit": ["fold", "fold", "fold", "call"],
        "LAG": ["raise", "raise", "raise", "call"],
        "Station": ["call", "call", "call", "call"],
    }
    styles = {
        "Nit": "nit",
        "LAG": "loose_aggressive",
        "Station": "calling_station",
    }
    for hand_index in range(4):
        action_records = []
        for player_name, actions in actions_by_player.items():
            action_records.append(
                {
                    "phase": "preflop",
                    "player_name": player_name,
                    "action": actions[hand_index],
                    "decision_evaluation": {"grade": "good", "score": 70},
                }
            )
        hand_summaries.append(
            {
                "actions": len(action_records),
                "ai_styles": styles,
                "winner_names": ["Station"],
                "final_hands": [
                    {"player_name": "Nit", "is_winner": False},
                    {"player_name": "LAG", "is_winner": False},
                    {"player_name": "Station", "is_winner": True},
                ],
                "outcome_metadata": {
                    "blind_positions": {"small_blind": "Nit", "big_blind": "LAG"},
                    "forced_blinds": [
                        {"player_name": "Nit", "blind_type": "small_blind", "amount": 5, "is_forced": True},
                        {"player_name": "LAG", "blind_type": "big_blind", "amount": 10, "is_forced": True},
                    ],
                },
                "action_records": action_records,
            }
        )
    return SimulationResult(
        hands_requested=4,
        hands_completed=4,
        total_actions=12,
        final_stacks={"Nit": 90, "LAG": 100, "Station": 110},
        hand_summaries=hand_summaries,
    )


def test_style_separability_metrics_use_observed_profile_action_data():
    report = summarize_ai_evaluations(_style_separability_simulation())

    assert report.vpip_spread == 0.75
    assert report.pfr_spread == 0.75
    assert report.aggression_spread == 3.0
    assert report.call_rate_spread == 0.75
    assert report.style_separability_score == 0.75

    as_dict = report.to_dict()
    assert as_dict["style_separability_score"] == 0.75
    assert as_dict["vpip_spread"] == 0.75
    assert as_dict["pfr_spread"] == 0.75
    assert as_dict["aggression_spread"] == 3.0
    assert as_dict["call_rate_spread"] == 0.75


def test_profile_calibration_reports_target_band_distance_and_status():
    report = summarize_ai_evaluations(_style_separability_simulation())
    as_dict = report.to_dict()

    assert as_dict["profile_calibration_status"] == "WARN"
    assert as_dict["profile_calibration_distance"] > 0
    calibration = as_dict["profile_calibration"]

    nit = calibration["nit"]
    assert nit["status"] == "WARN"
    assert nit["metrics"]["vpip"] == {
        "observed": 0.25,
        "target_min": 0.08,
        "target_max": 0.18,
        "status": "WARN",
        "distance": 0.07,
    }
    assert nit["metrics"]["pfr"]["status"] == "PASS"

    lag = calibration["loose_aggressive"]
    assert lag["metrics"]["vpip"]["status"] == "WARN"
    assert lag["metrics"]["call_rate"]["status"] == "PASS"

    station = calibration["calling_station"]
    assert station["metrics"]["call_rate"]["status"] == "PASS"
    assert station["metrics"]["average_decision_score"]["status"] == "PASS"
    json.dumps(as_dict, ensure_ascii=False)


def test_profile_calibration_is_empty_without_known_profile_metrics():
    report = summarize_ai_evaluations(SimulationResult(hands_requested=0, hands_completed=0, total_actions=0))

    as_dict = report.to_dict()

    assert as_dict["profile_calibration"] == {}
    assert as_dict["profile_calibration_status"] == "NOT_RUN"
    assert as_dict["profile_calibration_distance"] == 0.0


def test_style_separability_returns_zero_for_fewer_than_two_profiles():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=2,
        final_stacks={"AI-1": 100, "AI-2": 100},
        hand_summaries=[
            {
                "actions": 2,
                "ai_styles": {"AI-1": "balanced", "AI-2": "balanced"},
                "winner_names": ["AI-1"],
                "final_hands": [
                    {"player_name": "AI-1", "is_winner": True},
                    {"player_name": "AI-2", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "raise"},
                    {"phase": "preflop", "player_name": "AI-2", "action": "call"},
                ],
            }
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert report.style_separability_score == 0
    assert report.vpip_spread == 0
    assert report.pfr_spread == 0
    assert report.aggression_spread == 0
    assert report.call_rate_spread == 0

def test_stack_concentration_metrics_detect_winner_take_all_risk():
    simulation = SimulationResult(
        hands_requested=3,
        hands_completed=3,
        total_actions=0,
        final_stacks={"AI-1": 2800, "AI-2": 200, "AI-3": 0, "AI-4": 0},
        hand_summaries=[
            {"final_hands": [{"player_name": "AI-1", "final_chips": 1200}, {"player_name": "AI-2", "final_chips": 900}, {"player_name": "AI-3", "final_chips": 900}, {"player_name": "AI-4", "final_chips": 1000}]},
            {"final_hands": [{"player_name": "AI-1", "final_chips": 1800}, {"player_name": "AI-2", "final_chips": 700}, {"player_name": "AI-3", "final_chips": 0}, {"player_name": "AI-4", "final_chips": 500}]},
            {"final_hands": [{"player_name": "AI-1", "final_chips": 2800}, {"player_name": "AI-2", "final_chips": 200}, {"player_name": "AI-3", "final_chips": 0}, {"player_name": "AI-4", "final_chips": 0}]},
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert report.largest_stack_share == 2800 / 3000
    assert report.bustout_rate == 0.5
    assert report.hands_until_first_bust == 2
    assert round(report.stack_gini, 4) == 0.7167
    as_dict = report.to_dict()
    assert as_dict["largest_stack_share"] == 2800 / 3000
    assert as_dict["bustout_rate"] == 0.5
    assert as_dict["hands_until_first_bust"] == 2
    assert round(as_dict["stack_gini"], 4) == 0.7167

def test_stack_concentration_uses_settled_final_chips_before_action_chips():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=1,
        final_stacks={"AI-1": 1500, "AI-2": 500},
        hand_summaries=[
            {
                "final_hands": [
                    {"player_name": "AI-1", "final_chips": 1500},
                    {"player_name": "AI-2", "final_chips": 500},
                ],
                "action_records": [
                    {"player_name": "AI-1", "action": "all-in", "chips_after": 0},
                ],
            }
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert report.hands_until_first_bust is None


def test_benchmark_transcript_samples_summarize_public_hand_flow():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=4,
        final_stacks={"AI-1": 1150, "AI-2": 850},
        hand_summaries=[
            {
                "hand_index": 1,
                "phase_boards": {
                    "preflop": [],
                    "flop": ["A♠", "K♦", "7♣"],
                },
                "winner_names": ["AI-1"],
                "total_pot": 300,
                "outcome_metadata": {
                    "went_to_showdown": False,
                    "winner_reason": "fold",
                },
                "final_hands": [
                    {"player_name": "AI-1", "hole_cards": ["A♥", "Q♥"], "is_winner": True},
                    {"player_name": "AI-2", "hole_cards": ["9♣", "9♦"], "is_winner": False},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "raise", "amount": 30},
                    {"phase": "preflop", "player_name": "AI-2", "action": "call", "amount": 30},
                    {"phase": "flop", "player_name": "AI-1", "action": "bet", "amount": 80},
                    {"phase": "flop", "player_name": "AI-2", "action": "fold", "amount": 0},
                ],
            }
        ],
    )

    report = summarize_ai_evaluations(simulation)

    assert len(report.transcript_samples) == 1
    sample = report.transcript_samples[0]
    assert sample["hand_number"] == 1
    assert sample["flags"] == ["c-bet", "fold-to-cbet"]
    assert "Hand 1" in sample["text"]
    assert "preflop: AI-1 raise 30; AI-2 call 30" in sample["text"]
    assert "flop board: A♠ K♦ 7♣" in sample["text"]
    assert "flop: AI-1 bet 80; AI-2 fold" in sample["text"]
    assert "result: AI-1 won 300 by fold" in sample["text"]
    assert "A♥" not in sample["text"]
    assert "9♣" not in sample["text"]
    json.dumps(report.to_dict(), ensure_ascii=False)


def test_poor_blunder_audit_samples_include_classification_without_private_state():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=1,
        final_stacks={"AI-1": 900, "AI-2": 1100},
        hand_summaries=[
            {
                "hand_index": 7,
                "ai_styles": {"AI-1": "nit"},
                "phase_boards": {"flop": ["A♠", "7♦", "2♣"]},
                "action_records": [
                    {
                        "phase": "flop",
                        "player_name": "AI-1",
                        "action": "fold",
                        "amount": 0,
                        "pot": 180,
                        "to_call": 20,
                        "hole_cards": ["A♥", "K♥"],
                        "deck": ["Q♣"],
                        "private_ai_internals": {"hidden": True},
                        "decision_evaluation": {
                            "grade": "poor",
                            "score": 35,
                            "risk_tags": ["overfold", "hidden:AKs"],
                            "reasoning": "Folded despite strong made hand; hole_cards A♥ K♥ should stay private",
                            "equity": 0.72,
                            "pot_odds": 0.10,
                        },
                    }
                ],
            }
        ],
    )

    sample = summarize_ai_evaluations(simulation).to_dict()["poor_blunder_samples"][0]

    assert sample["hand_number"] == 7
    assert sample["player_name"] == "AI-1"
    assert sample["profile"] == "nit"
    assert sample["phase"] == "flop"
    assert sample["action"] == "fold"
    assert sample["grade"] == "poor"
    assert sample["classification"] == "overfold"
    assert sample["risk_tags"] == ["overfold"]
    assert sample["public_board"] == ["A♠", "7♦", "2♣"]
    dumped = json.dumps(sample, ensure_ascii=False)
    assert "hole_cards" not in dumped
    assert "A♥" not in dumped
    assert "K♥" not in dumped
    assert "deck" not in dumped
    assert "private_ai_internals" not in dumped
    assert "hidden:AKs" not in dumped


def test_poor_blunder_audit_splits_negative_pot_odds_calls_by_public_equity_edge():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=1,
        final_stacks={"AI-1": 980, "AI-2": 1020},
        hand_summaries=[
            {
                "hand_index": 2,
                "ai_styles": {"AI-1": "calling_station"},
                "phase_boards": {},
                "action_records": [
                    {
                        "phase": "preflop",
                        "player_name": "AI-1",
                        "action": "call",
                        "amount": 30,
                        "decision_evaluation": {
                            "grade": "blunder",
                            "score": 15,
                            "risk_tags": ["negative_pot_odds_call"],
                            "equity": 0.22,
                            "pot_odds": 0.35,
                        },
                    }
                ],
            }
        ],
    )

    sample = summarize_ai_evaluations(simulation).to_dict()["poor_blunder_samples"][0]

    assert sample["classification"] == "pot-odds call mistake"
    assert sample["audit_split"] == "true_negative_equity_call"
    assert sample["equity_edge"] == -0.13
    assert sample["audit_basis"] == "public_equity_vs_pot_odds"


def test_poor_blunder_audit_marks_positive_edge_pot_odds_tags_as_evaluator_candidates():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=1,
        final_stacks={"AI-1": 980, "AI-2": 1020},
        hand_summaries=[
            {
                "hand_index": 3,
                "ai_styles": {"AI-1": "calling_station"},
                "phase_boards": {"flop": ["A♠", "7♦", "2♣"]},
                "action_records": [
                    {
                        "phase": "flop",
                        "player_name": "AI-1",
                        "action": "call",
                        "amount": 30,
                        "decision_evaluation": {
                            "grade": "poor",
                            "score": 35,
                            "risk_tags": ["negative_pot_odds_call"],
                            "equity": 0.48,
                            "pot_odds": 0.35,
                        },
                    }
                ],
            }
        ],
    )

    sample = summarize_ai_evaluations(simulation).to_dict()["poor_blunder_samples"][0]

    assert sample["classification"] == "pot-odds call mistake"
    assert sample["audit_split"] == "evaluator_false_positive_candidate"
    assert sample["equity_edge"] == 0.13
    assert sample["public_board"] == ["A♠", "7♦", "2♣"]


def test_poor_blunder_audit_uses_nested_public_metrics_for_pot_odds_split():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=1,
        final_stacks={"AI-1": 980, "AI-2": 1020},
        hand_summaries=[
            {
                "hand_index": 4,
                "ai_styles": {"AI-1": "calling_station"},
                "action_records": [
                    {
                        "phase": "turn",
                        "player_name": "AI-1",
                        "action": "call",
                        "amount": 30,
                        "decision_evaluation": {
                            "grade": "poor",
                            "score": 35,
                            "risk_tags": ["negative_pot_odds_call"],
                            "metrics": {"equity": 0.18, "pot_odds": 0.30},
                        },
                    }
                ],
            }
        ],
    )

    sample = summarize_ai_evaluations(simulation).to_dict()["poor_blunder_samples"][0]

    assert sample["equity"] == 0.18
    assert sample["pot_odds"] == 0.30
    assert sample["audit_split"] == "true_negative_equity_call"
    assert sample["equity_edge"] == -0.12


def test_showdown_transcript_may_include_revealed_final_hands():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=2,
        final_stacks={"AI-1": 1200, "AI-2": 800},
        hand_summaries=[
            {
                "hand_index": 1,
                "phase_boards": {"river": ["A♠", "K♦", "7♣", "2♥", "2♠"]},
                "winner_names": ["AI-1"],
                "total_pot": 400,
                "outcome_metadata": {
                    "went_to_showdown": True,
                    "winner_reason": "showdown",
                },
                "final_hands": [
                    {"player_name": "AI-1", "hole_cards": ["A♥", "Q♥"], "hand_rank": "two pair", "is_winner": True},
                    {"player_name": "AI-2", "hole_cards": ["9♣", "9♦"], "hand_rank": "two pair", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "river", "player_name": "AI-1", "action": "bet", "amount": 100},
                    {"phase": "river", "player_name": "AI-2", "action": "call", "amount": 100},
                ],
            }
        ],
    )

    sample = summarize_ai_evaluations(simulation).transcript_samples[0]

    assert "showdown: AI-1 [A♥ Q♥] two pair; AI-2 [9♣ 9♦] two pair" in sample["text"]
    assert sample["flags"] == ["no-obvious-issue"]


def test_showdown_transcript_excludes_folded_players_private_cards():
    simulation = SimulationResult(
        hands_requested=1,
        hands_completed=1,
        total_actions=4,
        final_stacks={"AI-1": 0, "AI-2": 1200, "AI-3": 800},
        hand_summaries=[
            {
                "hand_index": 1,
                "phase_boards": {"river": ["A♠", "K♦", "7♣", "2♥", "2♠"]},
                "winner_names": ["AI-2"],
                "total_pot": 400,
                "outcome_metadata": {
                    "went_to_showdown": True,
                    "winner_reason": "showdown",
                },
                "final_hands": [
                    {"player_name": "AI-1", "hole_cards": ["3♣", "4♦"], "hand_rank": "folded", "is_winner": False},
                    {"player_name": "AI-2", "hole_cards": ["A♥", "Q♥"], "hand_rank": "two pair", "is_winner": True},
                    {"player_name": "AI-3", "hole_cards": ["9♣", "9♦"], "hand_rank": "two pair", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "fold", "amount": 0},
                    {"phase": "river", "player_name": "AI-2", "action": "bet", "amount": 100},
                    {"phase": "river", "player_name": "AI-3", "action": "call", "amount": 100},
                ],
            }
        ],
    )

    sample = summarize_ai_evaluations(simulation).transcript_samples[0]

    assert "AI-2 [A♥ Q♥] two pair" in sample["text"]
    assert "AI-3 [9♣ 9♦] two pair" in sample["text"]
    assert "AI-1" not in sample["text"].split("showdown:", 1)[1]
    assert "3♣" not in sample["text"]
    assert "4♦" not in sample["text"]


def test_public_transcript_safety_covers_all_in_side_pot_and_early_winner_shapes():
    simulation = SimulationResult(
        hands_requested=3,
        hands_completed=3,
        total_actions=6,
        final_stacks={"AI-1": 1600, "AI-2": 900, "AI-3": 500},
        hand_summaries=[
            {
                "hand_index": 1,
                "phase_boards": {"river": ["A♠", "K♦", "7♣", "2♥", "2♠"]},
                "winner_names": ["AI-1"],
                "total_pot": 900,
                "outcome_metadata": {"went_to_showdown": True, "winner_reason": "showdown"},
                "final_hands": [
                    {"player_name": "AI-1", "hole_cards": ["A♥", "Q♥"], "hand_rank": "two pair", "is_winner": True},
                    {"player_name": "AI-2", "hole_cards": ["9♣", "9♦"], "hand_rank": "two pair", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "turn", "player_name": "AI-1", "action": "all-in", "amount": 300},
                    {"phase": "turn", "player_name": "AI-2", "action": "call", "amount": 300},
                ],
            },
            {
                "hand_index": 2,
                "phase_boards": {"river": ["Q♠", "J♦", "7♣", "4♥", "3♠"]},
                "winner_names": ["AI-2"],
                "total_pot": 1200,
                "outcome_metadata": {"went_to_showdown": True, "winner_reason": "side_pot_showdown"},
                "final_hands": [
                    {"player_name": "AI-1", "hole_cards": ["6♥", "6♦"], "hand_rank": "folded", "is_winner": False},
                    {"player_name": "AI-2", "hole_cards": ["Q♥", "T♥"], "hand_rank": "pair", "is_winner": True},
                    {"player_name": "AI-3", "hole_cards": ["J♣", "T♣"], "hand_rank": "pair", "is_winner": False},
                ],
                "action_records": [
                    {"phase": "flop", "player_name": "AI-1", "action": "fold", "amount": 0},
                    {"phase": "river", "player_name": "AI-2", "action": "call", "amount": 100},
                    {"phase": "river", "player_name": "AI-3", "action": "all-in", "amount": 100},
                ],
            },
            {
                "hand_index": 3,
                "phase_boards": {},
                "winner_names": ["AI-3"],
                "total_pot": 30,
                "outcome_metadata": {"went_to_showdown": False, "winner_reason": "fold"},
                "final_hands": [
                    {"player_name": "AI-3", "hole_cards": ["8♣", "8♦"], "is_winner": True},
                ],
                "action_records": [
                    {"phase": "preflop", "player_name": "AI-1", "action": "fold", "amount": 0},
                    {"phase": "preflop", "player_name": "AI-2", "action": "fold", "amount": 0},
                ],
            },
        ],
    )

    samples = summarize_ai_evaluations(simulation).transcript_samples
    combined = "\n".join(sample["text"] for sample in samples)

    assert "all-in 300" in combined
    assert "showdown: AI-1 [A♥ Q♥] two pair; AI-2 [9♣ 9♦] two pair" in combined
    assert "AI-2 [Q♥ T♥] pair" in combined
    assert "AI-3 [J♣ T♣] pair" in combined
    assert "6♥" not in combined
    assert "6♦" not in combined
    assert "8♣" not in combined
    assert "8♦" not in combined
    assert all(sample["flags"] == ["no-obvious-issue"] for sample in samples)


def test_multi_seed_benchmark_reports_mean_std_min_max(monkeypatch, tmp_path):
    calls = []

    def fake_evaluate_ai_system(num_hands, player_count, starting_chips, seed, ai_equity_simulations=None):
        calls.append((num_hands, player_count, starting_chips, seed, ai_equity_simulations))
        return AISystemEvaluationReport(
            hands_played=num_hands,
            total_actions=10 + seed,
            illegal_action_rate=seed / 100,
            average_decision_score=50 + seed,
            grade_distribution={"good": seed},
            final_stacks={"AI-1": 1000 + seed},
            style_separability_score=seed / 10,
            vpip_spread=seed / 20,
            pfr_spread=seed / 25,
            aggression_spread=seed / 5,
            call_rate_spread=seed / 50,
            profile_calibration_distance=seed / 100,
        )

    monkeypatch.setattr("texas_holdem.analytics.ai_system_evaluator.evaluate_ai_system", fake_evaluate_ai_system)
    output_path = tmp_path / "multi-seed.json"

    report = benchmark_ai_system_multi_seed(
        seeds=[1, 2, 3],
        hands_per_seed=7,
        player_count=4,
        starting_chips=1000,
        output_path=str(output_path),
    )

    assert calls == [(7, 4, 1000, 1, 5), (7, 4, 1000, 2, 5), (7, 4, 1000, 3, 5)]
    assert report["benchmark"]["seeds"] == [1, 2, 3]
    assert report["benchmark"]["hands_per_seed"] == 7
    assert report["benchmark"]["ai_equity_simulations"] == 5
    assert report["runs"][0]["seed"] == 1
    assert report["summary"]["average_decision_score"] == {
        "mean": 52.0,
        "std": 0.816496580927726,
        "min": 51,
        "max": 53,
    }
    assert report["summary"]["total_actions"]["mean"] == 12.0
    assert report["summary"]["illegal_action_rate"]["max"] == 0.03
    assert report["summary"]["profile_calibration_distance"] == {
        "mean": 0.02,
        "std": 0.00816496580927726,
        "min": 0.01,
        "max": 0.03,
    }
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["summary"] == report["summary"]


def test_multi_seed_benchmark_writes_progress_after_each_seed(monkeypatch, tmp_path):
    progress_path = tmp_path / "multi-seed-progress.json"
    observed_progress = []

    def fake_evaluate_ai_system(num_hands, player_count, starting_chips, seed, ai_equity_simulations=None):
        if progress_path.exists():
            observed_progress.append(json.loads(progress_path.read_text(encoding="utf-8")))
        return AISystemEvaluationReport(
            hands_played=num_hands,
            total_actions=10 + seed,
            illegal_action_rate=0.0,
            average_decision_score=70 + seed,
            grade_distribution={"good": 10 + seed},
            final_stacks={"AI-1": 1000 + seed},
            style_separability_score=0.2,
            vpip_spread=0.1,
            pfr_spread=0.1,
            aggression_spread=0.5,
            call_rate_spread=0.1,
        )

    monkeypatch.setattr("texas_holdem.analytics.ai_system_evaluator.evaluate_ai_system", fake_evaluate_ai_system)

    report = benchmark_ai_system_multi_seed(
        seeds=[1, 2, 3],
        hands_per_seed=7,
        player_count=4,
        starting_chips=1000,
        progress_path=str(progress_path),
    )

    assert observed_progress[0]["status"] == "running"
    assert observed_progress[0]["completed_seeds"] == [1]
    assert observed_progress[0]["completed_seed_count"] == 1
    assert observed_progress[0]["total_seed_count"] == 3
    assert observed_progress[0]["runs"][0]["seed"] == 1

    final_progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert final_progress["status"] == "completed"
    assert final_progress["completed_seeds"] == [1, 2, 3]
    assert final_progress["summary"] == report["summary"]
    assert final_progress["runs"] == report["runs"]


def _gate_run(**overrides):
    data = {
        "hands_played": 500,
        "total_actions": 25,
        "illegal_action_rate": 0.0,
        "average_decision_score": 72.0,
        "grade_distribution": {"good": 25},
        "final_stacks": {"AI-1": 10000, "AI-2": 10000},
        "errors": [],
        "player_metrics": {
            "AI-1": {
                "vpip": 0.4,
                "pfr": 0.2,
                "aggression_factor": 1.0,
                "call_rate": 0.2,
                "fold_rate": 0.2,
                "showdown_rate": 0.1,
                "win_rate": 0.5,
                "poor_blunder_rate": 0.0,
                "average_decision_score": 62.0,
                "hands_played": 500,
                "actions": 12,
            }
        },
        "profile_metrics": {
            "nit": {"average_decision_score": 72.0, "poor_blunder_rate": 0.0},
            "tight_aggressive": {"average_decision_score": 72.0, "poor_blunder_rate": 0.0},
            "loose_aggressive": {"average_decision_score": 72.0, "poor_blunder_rate": 0.0},
            "calling_station": {"average_decision_score": 72.0, "poor_blunder_rate": 0.0},
        },
        "weakest_profile": "nit",
        "style_separability_score": 0.2,
        "vpip_spread": 0.1,
        "pfr_spread": 0.1,
        "aggression_spread": 0.2,
        "call_rate_spread": 0.1,
        "largest_stack_share": 0.5,
        "bustout_rate": 0.0,
        "hands_until_first_bust": None,
        "stack_gini": 0.0,
        "transcript_samples": [
            {"hand_number": 1, "text": "Hand 1 | preflop: AI-1 raise 30 | result: AI-1 won 60 by fold", "flags": ["no-obvious-issue"]}
        ],
        "benchmark": {"seed": 0},
        "seed": 0,
    }
    data.update(overrides)
    return data


def _gate_artifact(**overrides):
    data = {
        "benchmark": {
            "seeds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "hands_per_seed": 500,
            "player_count": 4,
            "starting_chips": 10000,
            "generated_at": "2026-05-12T00:00:00+00:00",
        },
        "summary": {
            "average_decision_score": {"mean": 72.0, "std": 0.0, "min": 72.0, "max": 72.0},
            "total_actions": {"mean": 25.0, "std": 0.0, "min": 25.0, "max": 25.0},
            "illegal_action_rate": {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
            "largest_stack_share": {"mean": 0.5, "std": 0.0, "min": 0.5, "max": 0.5},
            "bustout_rate": {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
        },
        "runs": [_gate_run(seed=seed, benchmark={"seed": seed}) for seed in range(10)],
    }
    data.update(overrides)
    return data


def test_public_transcript_schema_and_showdown_policy_are_reported():
    report = summarize_ai_evaluations(
        SimulationResult(
            hands_requested=1,
            hands_completed=1,
            total_actions=1,
            final_stacks={"AI-1": 1100, "AI-2": 900},
            hand_summaries=[
                {
                    "hand_index": 3,
                    "phase_boards": {"flop": ["A♠", "7♦", "2♣"]},
                    "winner_names": ["AI-1"],
                    "total_pot": 120,
                    "outcome_metadata": {"went_to_showdown": False, "winner_reason": "fold"},
                    "final_hands": [
                        {"player_name": "AI-1", "hole_cards": ["A♥", "K♥"], "is_winner": True},
                        {"player_name": "AI-2", "hole_cards": ["9♣", "9♦"], "is_winner": False},
                    ],
                    "action_records": [{"phase": "flop", "player_name": "AI-2", "action": "fold", "amount": 0}],
                }
            ],
        )
    ).to_dict()

    assert report["public_transcript_schema"] == {
        "version": "phase3.4-public-transcript-v1",
        "sample_fields": ["hand_number", "text", "flags"],
        "allowed_private_cards": "only legally revealed showdown contestants",
        "forbidden_fields": ["deck", "hole_cards", "opponent_hole_cards", "private_ai_internals", "unsafe_seed"],
    }
    assert report["showdown_reveal_policy"] == {
        "showdown": "reveal only players who legally reached showdown",
        "non_showdown": "do not reveal any private hole cards",
        "folded_players": "never reveal folded/non-contesting players' private cards",
    }
    sample_text = report["transcript_samples"][0]["text"]
    assert "A♥" not in sample_text
    assert "K♥" not in sample_text
    assert "9♣" not in sample_text
    assert "9♦" not in sample_text


def test_benchmark_gate_fails_for_audit_sample_private_state_leaks():
    artifact = _gate_artifact(
        runs=[
            _gate_run(
                seed=seed,
                benchmark={"seed": seed},
                poor_blunder_samples=[{"classification": "overfold", "reason": "hole_cards A♥ K♥"}],
            )
            for seed in range(10)
        ]
    )

    result = evaluate_benchmark_gates(artifact)

    assert result["status"] == "FAIL"
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["transcript_safety"]["status"] == "FAIL"
    assert checks["transcript_safety"]["observed"] == "forbidden token in poor_blunder_samples: hole_cards"


def test_benchmark_gate_evaluation_passes_machine_readable_primary_protocol():
    result = evaluate_benchmark_gates(_gate_artifact())

    assert result["gate_version"] == "phase2.2"
    assert result["status"] == "PASS"
    assert result["protocol"] == {
        "seeds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        "hands_per_seed": 500,
        "player_count": 4,
        "starting_chips": 10000,
    }
    assert all(check["status"] == "PASS" for check in result["checks"])
    json.dumps(result, ensure_ascii=False)


def test_benchmark_gate_evaluation_accepts_explicit_reduced_protocol():
    reduced_protocol = {
        "seeds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        "hands_per_seed": 100,
        "player_count": 4,
        "starting_chips": 10000,
    }
    artifact = _gate_artifact(
        benchmark={
            "seeds": reduced_protocol["seeds"],
            "hands_per_seed": 100,
            "player_count": 4,
            "starting_chips": 10000,
            "generated_at": "2026-05-12T00:00:00+00:00",
        },
        runs=[_gate_run(seed=seed, hands_played=100, benchmark={"seed": seed}) for seed in range(10)],
    )

    result = evaluate_benchmark_gates(artifact, expected_protocol=reduced_protocol)

    assert result["status"] == "PASS"
    assert result["protocol"] == reduced_protocol
    assert all(check["status"] == "PASS" for check in result["checks"])



def test_benchmark_gate_evaluation_warns_for_quality_thresholds():
    artifact = _gate_artifact(
        runs=[
            _gate_run(
                seed=0,
                average_decision_score=69.5,
                style_separability_score=0.1,
                grade_distribution={"good": 8, "poor": 2, "blunder": 1},
            ),
            *[_gate_run(seed=seed, benchmark={"seed": seed}) for seed in range(1, 10)],
        ]
    )

    result = evaluate_benchmark_gates(artifact)

    assert result["status"] == "WARN"
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["average_decision_score"]["status"] == "WARN"
    assert checks["style_separability_score"]["status"] == "WARN"
    assert checks["poor_blunder_rate"]["status"] == "WARN"
    assert checks["blunder_rate"]["status"] == "WARN"



def test_benchmark_gate_evaluation_fails_when_required_profiles_are_missing():
    artifact = _gate_artifact(runs=[_gate_run(seed=seed, profile_metrics={"balanced": {}}) for seed in range(10)])

    result = evaluate_benchmark_gates(artifact)

    assert result["status"] == "FAIL"
    checks = {check["name"]: check for check in result["checks"]}
    assert checks["profile_coverage"]["status"] == "FAIL"
    assert checks["profile_coverage"]["observed"] == {
        "seed": 0,
        "missing_profiles": ["calling_station", "loose_aggressive", "nit", "tight_aggressive"],
    }



def test_benchmark_gate_evaluation_fails_for_metadata_illegal_actions_and_transcript_leaks():
    artifact = _gate_artifact(
        benchmark={
            "seeds": [0, 1],
            "hands_per_seed": 100,
            "player_count": 4,
            "starting_chips": 1000,
            "generated_at": "2026-05-12T00:00:00+00:00",
        },
        runs=[
            _gate_run(
                hands_played=99,
                illegal_action_rate=0.01,
                transcript_samples=[
                    {"hand_number": 1, "text": "deck: A♠ K♠ opponent_hole_cards: 2♣ 2♦", "flags": []}
                ],
            )
        ],
    )

    result = evaluate_benchmark_gates(artifact)

    assert result["status"] == "FAIL"
    failures = {check["name"]: check for check in result["checks"] if check["status"] == "FAIL"}
    assert "benchmark_metadata" in failures
    assert "completion" in failures
    assert "illegal_action_rate" in failures
    assert "transcript_safety" in failures
    assert failures["transcript_safety"]["observed"] == "forbidden token: deck"



def test_seeded_single_run_benchmark_is_deterministic_for_same_seed():
    first = benchmark_ai_system(num_hands=2, player_count=4, seed=42).to_dict()
    second = benchmark_ai_system(num_hands=2, player_count=4, seed=42).to_dict()

    ignored_keys = {"generated_at"}
    first_benchmark = {k: v for k, v in first["benchmark"].items() if k not in ignored_keys}
    second_benchmark = {k: v for k, v in second["benchmark"].items() if k not in ignored_keys}
    assert first_benchmark == second_benchmark
    assert first["final_stacks"] == second["final_stacks"]
    assert first["total_actions"] == second["total_actions"]
    assert first["average_decision_score"] == second["average_decision_score"]
    assert first["transcript_samples"] == second["transcript_samples"]
