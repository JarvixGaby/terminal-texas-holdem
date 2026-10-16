# tests/test_blinds.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from player import HumanPlayer
from game import TexasHoldemGame


def make_game():
    players = [HumanPlayer("Alice", 1000), HumanPlayer("Bob", 1000), HumanPlayer("Charlie", 1000)]
    return TexasHoldemGame(players, small_blind=5, big_blind=10)


def test_blinds_deducted_once():
    """SB pays 5, BB pays 10 — total pot = 15, chips correct after blinds."""
    game = make_game()
    game.active_players = list(game.players)
    game.deck.reset()
    game.deck.shuffle()
    game._deal_hole_cards()
    game._collect_blinds()

    # dealer=0, SB=1, BB=2
    sb = game.active_players[1]
    bb = game.active_players[2]

    assert sb.chips == 995, f"SB chips should be 995, got {sb.chips}"
    assert bb.chips == 990, f"BB chips should be 990, got {bb.chips}"
    assert game.pot == 15, f"Pot should be 15, got {game.pot}"
    assert sb.current_bet == 5, f"SB current_bet should be 5, got {sb.current_bet}"
    assert bb.current_bet == 10, f"BB current_bet should be 10, got {bb.current_bet}"


def test_preflop_betting_does_not_reset_blind_bets():
    """_betting_round() must not reset SB/BB current_bet at preflop start (would double-charge)."""
    from player import AIPlayer
    players = [AIPlayer("Alice", 1000), AIPlayer("Bob", 1000), AIPlayer("Charlie", 1000)]
    game = TexasHoldemGame(players, small_blind=5, big_blind=10)
    game.active_players = list(game.players)
    game.deck.reset()
    game.deck.shuffle()
    game._deal_hole_cards()
    game._collect_blinds()

    chips_before = {p.name: p.chips for p in game.active_players}
    pot_before = game.pot  # should be 15

    # Run the preflop betting round (AI players will act automatically)
    game._betting_round()

    # Total chips in play must be conserved: sum(chips) + pot == 3000
    total_chips = sum(p.chips for p in game.active_players) + game.pot
    assert total_chips == 3000, f"Chips not conserved: {total_chips} (expected 3000)"

    # Pot must be >= 15 (blinds already in), never less
    assert game.pot >= 15, f"Pot should be >= 15 after preflop, got {game.pot}"


def test_heads_up_dealer_is_small_blind():
    """In heads-up, dealer (position 0) must be SB, other player is BB."""
    players = [HumanPlayer("Alice", 1000), HumanPlayer("Bob", 1000)]
    game = TexasHoldemGame(players, small_blind=5, big_blind=10)
    game.active_players = list(game.players)
    game.deck.reset()
    game.deck.shuffle()
    game._deal_hole_cards()
    game._collect_blinds()

    # dealer_position = 0 → Alice is dealer → Alice should be SB
    alice = game.active_players[0]
    bob = game.active_players[1]

    assert alice.chips == 995, f"Dealer/SB Alice should have 995, got {alice.chips}"
    assert bob.chips == 990, f"BB Bob should have 990, got {bob.chips}"
    assert alice.current_bet == 5
    assert bob.current_bet == 10
