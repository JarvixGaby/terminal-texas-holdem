from texas_holdem.engine.engine_events import EngineEvent


def test_engine_event_serializes_public_and_private_payloads():
    event = EngineEvent(
        type="cards_dealt",
        hand_id="hand-1",
        phase="flop",
        public_payload={"community_cards": ["AS", "KS", "QS"]},
        private_payload_by_player={"Hero": {"hole_cards": ["JS", "TS"]}},
        metadata={"source": "test"},
    )

    data = event.to_dict()

    assert data["type"] == "cards_dealt"
    assert data["hand_id"] == "hand-1"
    assert data["phase"] == "flop"
    assert data["public_payload"]["community_cards"] == ["AS", "KS", "QS"]
    assert data["private_payload_by_player"]["Hero"]["hole_cards"] == ["JS", "TS"]
    assert data["metadata"]["source"] == "test"


def test_engine_event_defaults_do_not_share_mutable_payloads():
    first = EngineEvent(type="phase_started", hand_id="h1", phase="preflop")
    second = EngineEvent(type="phase_started", hand_id="h2", phase="flop")

    first.public_payload["changed"] = True

    assert "changed" not in second.public_payload
