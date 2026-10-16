from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json

from decision_provider import ActionResponse
import headless_simulation
from headless_simulation import (
    SimulationResult,
    run_ai_only_simulation,
)


def assert_headless_event_visibility_contract(engine_events):
    for event in engine_events:
        assert event.get("private_payload_by_player") == {}
        serialized_public_payload = repr(event.get("public_payload", {})).lower()
        assert "deck" not in serialized_public_payload
        if event.get("type") == "player_hand_revealed":
            assert event.get("public_payload", {}).get("hole_cards")
        else:
            assert "hole_cards" not in serialized_public_payload


def test_run_ai_only_simulation_completes_small_batch_without_input():
    result = run_ai_only_simulation(num_hands=3, player_count=4, starting_chips=500, small_blind=5, big_blind=10)
    assert isinstance(result, SimulationResult)
    assert result.hands_requested == 3
    assert result.hands_completed == 3
    assert set(result.final_stacks.keys()) == {"AI-1", "AI-2", "AI-3", "AI-4"}
    assert result.total_actions > 0
    assert len(result.hand_summaries) == result.hands_completed
    assert len(result.errors) == 0
    assert all(summary["actions"] > 0 for summary in result.hand_summaries)
    assert all("action_records" in summary for summary in result.hand_summaries)
    assert all(len(summary["action_records"]) == summary["actions"] for summary in result.hand_summaries)
    assert all("decision_evaluations" in summary for summary in result.hand_summaries)
    assert all("outcome_metadata" in summary for summary in result.hand_summaries)
    assert all("ai_styles" in summary for summary in result.hand_summaries)
    assert any(summary["ai_styles"] for summary in result.hand_summaries)
    for summary in result.hand_summaries:
        outcome = summary["outcome_metadata"]
        assert set(outcome) >= {
            "ended_by_fold",
            "went_to_showdown",
            "winner_reason",
            "street_reach",
            "blind_positions",
            "forced_blinds",
        }
        assert isinstance(outcome["ended_by_fold"], bool)
        assert isinstance(outcome["went_to_showdown"], bool)
        assert outcome["winner_reason"] in {"showdown", "fold", "invalid_all_fold"}
        assert set(outcome["street_reach"]) <= set(result.final_stacks)
        for reach in outcome["street_reach"].values():
            assert set(reach) == {"saw_flop", "saw_turn", "saw_river"}
        assert set(outcome["blind_positions"]) == {"small_blind", "big_blind"}
        assert len(outcome["forced_blinds"]) == 2
        assert {blind["blind_type"] for blind in outcome["forced_blinds"]} == {"small_blind", "big_blind"}
        assert all(blind["is_forced"] is True for blind in outcome["forced_blinds"])


def test_run_ai_only_simulation_assigns_distinct_default_ai_profiles():
    result = run_ai_only_simulation(num_hands=1, player_count=4, starting_chips=500)

    assert result.errors == []
    first_styles = result.hand_summaries[0]["ai_styles"]
    assert set(first_styles) == {"AI-1", "AI-2", "AI-3", "AI-4"}
    assert len(set(first_styles.values())) == 4
    assert "advanced" not in set(first_styles.values())


def test_run_ai_only_simulation_does_not_modify_real_runtime_data_files():
    watched_paths = [Path("game_history.json"), Path("player_stats.json")]
    before = {path: path.read_bytes() if path.exists() else None for path in watched_paths}

    result = run_ai_only_simulation(num_hands=2, player_count=4, starting_chips=500)

    assert result.errors == []
    after = {path: path.read_bytes() if path.exists() else None for path in watched_paths}
    assert after == before


def test_run_ai_only_simulation_handles_bad_arguments_safely():
    result = run_ai_only_simulation(num_hands=2, player_count=1)
    assert result.hands_requested == 2
    assert result.hands_completed == 0
    assert result.errors
    assert result.final_stacks == {}


def test_run_ai_only_simulation_normalizes_dealer_when_players_bust():
    result = run_ai_only_simulation(num_hands=20, player_count=4, starting_chips=120, small_blind=5, big_blind=10)
    assert result.hands_completed > 0
    assert result.errors == []


def test_run_ai_only_simulation_restores_global_ai_engine_managers():
    import advanced_ai_engine
    import smart_ai_system

    original_smart_engines = dict(smart_ai_system.ai_engine_manager.engines)
    original_advanced_engines = dict(advanced_ai_engine.advanced_ai_manager.engines)
    smart_ai_system.ai_engine_manager.engines = {}
    advanced_ai_engine.advanced_ai_manager.engines = {}
    try:
        result = run_ai_only_simulation(num_hands=3, player_count=4, starting_chips=500)
        assert result.errors == []
        assert smart_ai_system.ai_engine_manager.engines == {}
        assert advanced_ai_engine.advanced_ai_manager.engines == {}
    finally:
        smart_ai_system.ai_engine_manager.engines = original_smart_engines
        advanced_ai_engine.advanced_ai_manager.engines = original_advanced_engines


def test_run_ai_only_simulation_can_collect_engine_events():
    result = run_ai_only_simulation(
        num_hands=2,
        player_count=4,
        starting_chips=500,
        collect_events=True,
    )

    assert result.errors == []
    assert result.engine_events
    assert any(event["type"] == "action_applied" for event in result.engine_events)
    assert any(event["type"] == "hand_completed" for event in result.engine_events)
    assert_headless_event_visibility_contract(result.engine_events)


def test_headless_collect_events_allows_public_showdown_reveals(monkeypatch):
    def passive_showdown_decision(self, state):
        if state.amount_to_call > 0:
            return ActionResponse("call", state.amount_to_call)
        return ActionResponse("check", 0)

    monkeypatch.setattr("game.BuiltInAIDecisionProvider.decide", passive_showdown_decision)

    result = run_ai_only_simulation(
        num_hands=1,
        player_count=2,
        starting_chips=500,
        collect_events=True,
    )

    assert result.errors == []
    reveal_events = [
        event for event in result.engine_events
        if event["type"] == "player_hand_revealed"
    ]
    assert reveal_events
    assert all(event["public_payload"]["hole_cards"] for event in reveal_events)
    assert_headless_event_visibility_contract(result.engine_events)


def test_run_ai_only_simulation_summarizes_event_coverage():
    result = run_ai_only_simulation(
        num_hands=1,
        player_count=4,
        starting_chips=500,
        collect_events=True,
    )

    assert result.errors == []
    assert result.event_type_counts["hand_started"] == 1
    assert result.event_type_counts["betting_round_started"] >= 1
    assert result.event_type_counts["action_applied"] >= 1
    assert result.event_type_counts["hand_completed"] == 1

    assert set(result.event_types_by_hand_id) == {
        event["hand_id"] for event in result.engine_events if event.get("hand_id")
    }
    full_hand_event_sets = [set(event_types) for event_types in result.event_types_by_hand_id.values()]
    assert any(
        {
            "hand_started",
            "betting_round_started",
            "action_applied",
            "hand_completed",
        }.issubset(event_types)
        for event_types in full_hand_event_sets
    )


def test_collect_events_full_hand_has_lifecycle_action_and_completion_gate():
    result = run_ai_only_simulation(
        num_hands=1,
        player_count=4,
        starting_chips=500,
        collect_events=True,
    )

    assert result.errors == []
    required_event_types = {
        "hand_started",
        "betting_round_started",
        "betting_round_completed",
        "action_applied",
        "hand_completed",
    }
    assert any(
        required_event_types.issubset(set(event_types))
        for event_types in result.event_types_by_hand_id.values()
    )
    assert_headless_event_visibility_contract(result.engine_events)


def test_action_sequence_fixture_routes_scripted_responses_through_provider_and_validator():
    result = headless_simulation.run_action_sequence_fixture(
        scripted_responses={
            "AI-1": [
                ActionResponse(
                    "call",
                    999,
                    metadata={"note": "normalize call", "deck": ["hidden"]},
                ),
                ActionResponse("check", 0),
                ActionResponse("check", 0),
                ActionResponse("check", 0),
            ],
            "AI-2": [
                ActionResponse(
                    "dance",
                    123,
                    metadata={"private_ai_internals": {"range": "hidden"}},
                ),
                ActionResponse("check", 0),
                ActionResponse("check", 0),
                ActionResponse("check", 0),
            ],
        },
        collect_events=True,
        seed=7,
    )

    assert isinstance(result, headless_simulation.ActionSequenceFixtureResult)
    assert result.errors == []
    assert result.hands_completed == 1
    assert result.provider_call_counts["AI-1"] >= 1
    assert result.provider_call_counts["AI-2"] >= 1

    ai_1_call = next(
        action
        for action in result.action_records
        if action["player_name"] == "AI-1" and action["action"] == "call"
    )
    assert ai_1_call["amount"] == 5
    assert ai_1_call["validation"]["original_action"] == "call"
    assert ai_1_call["validation"]["original_amount"] == 999
    assert ai_1_call["validation"]["is_valid"] is True
    assert ai_1_call["validation"]["reason"] == "normalized to amount_to_call"

    invalid_action = next(
        action
        for action in result.action_records
        if action["validation"]["original_action"] == "dance"
    )
    assert invalid_action["player_name"] == "AI-2"
    assert invalid_action["action"] == "check"
    assert invalid_action["validation"]["is_valid"] is False
    assert "illegal action" in invalid_action["validation"]["reason"]

    assert any(event["type"] == "validation_failed" for event in result.engine_events)
    assert any(event["type"] == "action_applied" for event in result.engine_events)

    applied = [event for event in result.engine_events if event["type"] == "action_applied"]
    assert [
        (event["phase"], event["public_payload"]["player_name"],
         event["public_payload"]["action"], event["public_payload"]["amount"],
         event["public_payload"]["chips_before"], event["public_payload"]["chips_after"])
        for event in applied
    ] == [
        (action["phase"], action["player_name"], action["action"],
         action["amount"], action["chips_before"], action["chips_after"])
        for action in result.action_records
    ]

    failed = [event["public_payload"] for event in result.engine_events
              if event["type"] == "validation_failed"]
    invalid_records = [action for action in result.action_records
                       if action["validation"]["is_valid"] is False]
    assert [
        (event["player_name"], event["original_action"], event["fallback_action"])
        for event in failed
    ] == [
        (action["player_name"], action["validation"]["original_action"], action["action"])
        for action in invalid_records
    ]

    completed = [event for event in result.engine_events if event["type"] == "hand_completed"]
    assert len(completed) == 1
    assert completed[0]["public_payload"]["winner_names"] == result.winner_names
    assert {hand["player_name"]: hand["final_chips"] for hand in
            completed[0]["public_payload"]["final_hands"]} == result.final_stacks


def test_action_sequence_fixture_serializes_public_safely_and_isolates_runtime_files():
    watched_paths = [Path("game_history.json"), Path("player_stats.json")]
    before = {path: path.read_bytes() if path.exists() else None for path in watched_paths}

    provider = headless_simulation.ScriptedDecisionProvider(
        [
            ActionResponse(
                "call",
                999,
                metadata={
                    "safe": "kept",
                    "deck": ["hidden"],
                    "opponent_hole_cards": ["A♠", "A♥"],
                    "private_ai_internals": {"range": "hidden"},
                },
            ),
            ActionResponse("check", 0),
            ActionResponse("check", 0),
            ActionResponse("check", 0),
        ]
    )
    result = headless_simulation.run_action_sequence_fixture(
        scripted_responses={
            "AI-1": provider,
            "AI-2": [
                ActionResponse("check", 0),
                ActionResponse("check", 0),
                ActionResponse("check", 0),
                ActionResponse("check", 0),
            ],
        },
        collect_events=True,
        seed=11,
    )

    after = {path: path.read_bytes() if path.exists() else None for path in watched_paths}
    serialized = json.dumps(result.to_dict(), ensure_ascii=False).lower()

    assert result.errors == []
    assert provider.call_count >= 1
    assert after == before
    assert "safe" in serialized
    assert "deck" not in serialized
    assert "opponent_hole_cards" not in serialized
    assert "private_ai_internals" not in serialized
    assert "private_payload_by_player" in serialized
    assert all(event.get("private_payload_by_player") == {} for event in result.engine_events)


def test_parallel_headless_fixtures_do_not_mix_global_runtime_state():
    watched_paths = [Path("game_history.json"), Path("player_stats.json")]
    before = {path: path.read_bytes() if path.exists() else None for path in watched_paths}

    def run_fixture(seed):
        return headless_simulation.run_action_sequence_fixture(
            scripted_responses={
                "AI-1": [ActionResponse("call", 999), ActionResponse("check")],
                "AI-2": [ActionResponse("check"), ActionResponse("check")],
            },
            seed=seed,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run_fixture, [17, 19]))

    assert all(result.errors == [] and result.hands_completed == 1 for result in results)
    assert all(sum(result.final_stacks.values()) == 200 for result in results)
    assert {path: path.read_bytes() if path.exists() else None for path in watched_paths} == before
