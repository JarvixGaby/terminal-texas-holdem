# tests/test_dealer.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from texas_holdem.engine.player import HumanPlayer
from texas_holdem.engine.game import TexasHoldemGame


def test_dealer_position_stable_after_player_busts():
    """Dealer position should cycle over all original players, not shrink when one busts."""
    players = [HumanPlayer("A", 1000), HumanPlayer("B", 1000),
               HumanPlayer("C", 1000), HumanPlayer("D", 1000)]
    game = TexasHoldemGame(players)
    game.active_players = list(game.players)

    # Simulate D busting out
    game.players[3].chips = 0
    game.active_players = [p for p in game.players if p.chips > 0]  # 3 players

    game.dealer_position = 3  # was pointing at D
    game._move_dealer()

    # Should wrap using total players count (4), not active (3)
    assert game.dealer_position == 0, f"Expected 0, got {game.dealer_position}"
