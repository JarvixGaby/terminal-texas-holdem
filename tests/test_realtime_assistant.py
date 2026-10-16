from card import Card, Rank, Suit
from realtime_assistant import RealtimeAssistant, SuggestedAction


def make_card(rank: Rank, suit: Suit) -> Card:
    return Card(suit, rank)


def test_preflop_trash_offsuit_facing_raise_prefers_fold_despite_raw_pot_odds():
    assistant = RealtimeAssistant()

    analysis = assistant.analyze(
        hole_cards=[make_card(Rank.NINE, Suit.CLUBS), make_card(Rank.THREE, Suit.DIAMONDS)],
        community_cards=[],
        pot_size=43,
        bet_to_call=18,
        player_chips=1005,
        position=0,
        total_players=4,
        num_opponents=1,
    )

    assert analysis.current_hand == "翻牌前: 93o"
    assert analysis.suggested_action == SuggestedAction.FOLD
    assert "实现率" in analysis.reasoning or "可玩性" in analysis.reasoning


def test_preflop_pair_can_continue_when_price_is_good():
    assistant = RealtimeAssistant()

    analysis = assistant.analyze(
        hole_cards=[make_card(Rank.SIX, Suit.CLUBS), make_card(Rank.SIX, Suit.HEARTS)],
        community_cards=[],
        pot_size=42,
        bet_to_call=10,
        player_chips=1000,
        position=0,
        total_players=4,
        num_opponents=3,
    )

    assert analysis.current_hand == "翻牌前: 66"
    assert analysis.suggested_action in {SuggestedAction.CALL, SuggestedAction.BORDERLINE_CALL, SuggestedAction.RAISE, SuggestedAction.STRONG_RAISE}
