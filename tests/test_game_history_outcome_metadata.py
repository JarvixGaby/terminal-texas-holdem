import json
import pytest

from texas_holdem.history.game_history import GameHistoryManager


def test_finish_game_persists_explicit_outcome_metadata(tmp_path):
    history_file = tmp_path / "history.json"
    manager = GameHistoryManager(history_file=str(history_file))
    manager.start_new_game_record(["AI-1", "AI-2"], small_blind=5, big_blind=10, dealer_position=0)
    manager.start_new_phase("river", [], pot_size=100, current_bet=20)

    outcome_metadata = {
        "ended_by_fold": False,
        "went_to_showdown": True,
        "winner_reason": "showdown",
        "street_reach": {
            "AI-1": {"saw_flop": True, "saw_turn": True, "saw_river": True},
            "AI-2": {"saw_flop": True, "saw_turn": True, "saw_river": True},
        },
    }

    manager.finish_game(
        final_hands=[
            {"player_name": "AI-1", "hole_cards": [], "final_chips": 120, "hand_rank": "Pair", "winnings": 100},
            {"player_name": "AI-2", "hole_cards": [], "final_chips": 80, "hand_rank": "High Card", "winnings": 0},
        ],
        total_pot=100,
        winner_names=["AI-1"],
        outcome_metadata=outcome_metadata,
    )

    raw_records = json.loads(history_file.read_text(encoding="utf-8"))
    assert raw_records[0]["outcome_metadata"] == outcome_metadata

    loaded = manager.get_game_by_id(raw_records[0]["game_id"])
    assert loaded.outcome_metadata == outcome_metadata


def test_legacy_history_records_default_to_empty_outcome_metadata(tmp_path):
    history_file = tmp_path / "legacy-history.json"
    legacy_record = {
        "game_id": "legacy-1",
        "timestamp": 1.0,
        "date_time": "2026-05-08 00:00:00",
        "players": ["AI-1", "AI-2"],
        "small_blind": 5,
        "big_blind": 10,
        "dealer_position": 0,
        "phases": [],
        "final_hands": [],
        "total_pot": 0,
        "winner_names": [],
        "duration_seconds": 0.0,
    }
    history_file.write_text(json.dumps([legacy_record]), encoding="utf-8")

    manager = GameHistoryManager(history_file=str(history_file))
    loaded = manager.get_game_by_id("legacy-1")

    assert loaded.outcome_metadata == {}


def test_damaged_history_is_preserved_and_current_hand_can_be_retried(tmp_path):
    history_file = tmp_path / "history.json"
    damaged_bytes = b'{"incomplete":'
    history_file.write_bytes(damaged_bytes)
    manager = GameHistoryManager(history_file=str(history_file))
    manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)

    with pytest.raises(ValueError, match="无法读取历史牌局文件"):
        manager.finish_game([], 0, ["AI-1"])

    assert history_file.read_bytes() == damaged_bytes
    assert manager.current_game_record is not None
    assert list(tmp_path.glob(".game_history_*.tmp")) == []


def test_history_save_replaces_file_and_leaves_no_temporary_file(tmp_path):
    history_file = tmp_path / "history.json"
    manager = GameHistoryManager(history_file=str(history_file))
    for index in range(2):
        manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, index)
        manager.finish_game([], 0, ["AI-1"])

    assert len(json.loads(history_file.read_text(encoding="utf-8"))) == 2
    assert list(tmp_path.glob(".game_history_*.tmp")) == []


def test_history_replace_failure_keeps_last_complete_record(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    manager = GameHistoryManager(history_file=str(history_file))
    manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 0)
    manager.finish_game([], 0, ["AI-1"])
    original = history_file.read_bytes()

    manager.start_new_game_record(["AI-1", "AI-2"], 5, 10, 1)
    monkeypatch.setattr("texas_holdem.history.game_history.os.replace", lambda *args: (_ for _ in ()).throw(OSError("disk error")))
    with pytest.raises(OSError, match="disk error"):
        manager.finish_game([], 0, ["AI-2"])

    assert history_file.read_bytes() == original
    assert manager.current_game_record is not None
    assert list(tmp_path.glob(".game_history_*.tmp")) == []
