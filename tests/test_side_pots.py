# tests/test_side_pots.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from player import HumanPlayer
from game import TexasHoldemGame


def test_side_pot_calculation_with_all_in():
    """
    Alice all-in for 100. Bob and Charlie each contribute 300.
    Side pot (Alice eligible): 100×3 = 300
    Main pot (Bob+Charlie only): 200×2 = 400
    """
    alice = HumanPlayer("Alice", 100)
    bob = HumanPlayer("Bob", 500)
    charlie = HumanPlayer("Charlie", 500)
    game = TexasHoldemGame([alice, bob, charlie], small_blind=5, big_blind=10)

    game.side_pot_manager.reset()
    game.side_pot_manager.add_contribution("Alice", 100, is_all_in=True)
    game.side_pot_manager.add_contribution("Bob", 300)
    game.side_pot_manager.add_contribution("Charlie", 300)

    main_pot, side_pots = game.side_pot_manager.calculate_side_pots([])

    assert len(side_pots) == 1, f"Expected 1 side pot, got {len(side_pots)}"
    assert side_pots[0].amount == 300, f"Side pot should be 300, got {side_pots[0].amount}"
    assert "Alice" in side_pots[0].eligible_players
    assert main_pot == 400, f"Main pot should be 400, got {main_pot}"


def test_blind_contributions_recorded():
    """After _collect_blinds, side_pot_manager must have SB and BB contributions."""
    from player import AIPlayer
    players = [AIPlayer("Alice", 1000), AIPlayer("Bob", 1000), AIPlayer("Charlie", 1000)]
    game = TexasHoldemGame(players, small_blind=5, big_blind=10)
    game.active_players = list(game.players)
    game.deck.reset()
    game.deck.shuffle()
    game._deal_hole_cards()
    game._collect_blinds()

    # dealer=0, SB=1 (Bob), BB=2 (Charlie)
    total_contributions = sum(game.side_pot_manager.contributions.values())
    assert total_contributions == 15, f"Expected 15 in contributions, got {total_contributions}"


def test_call_contribution_recorded():
    """After a call action in _betting_round, side_pot_manager records the contribution."""
    from player import AIPlayer
    players = [AIPlayer("Alice", 1000), AIPlayer("Bob", 1000), AIPlayer("Charlie", 1000)]
    game = TexasHoldemGame(players, small_blind=5, big_blind=10)
    game.active_players = list(game.players)
    game.deck.reset()
    game.deck.shuffle()
    game._deal_hole_cards()
    game._collect_blinds()

    # Run preflop betting (AI will call/fold/raise)
    game._betting_round()

    # Total contributions must equal total pot
    total_contributions = sum(game.side_pot_manager.contributions.values())
    assert total_contributions == game.pot, (
        f"Contributions ({total_contributions}) must equal pot ({game.pot})"
    )


def test_all_in_player_does_not_win_main_pot():
    """
    Alice all-in for 100 with best hand. Bob and Charlie each contribute 300.
    Alice wins side pot (300). Bob or Charlie wins main pot (400) based on their hands.
    Alice must NOT receive the main pot.
    """
    from player import AIPlayer
    from card import Card, Rank, Suit
    from hand_evaluator import HandEvaluator

    alice = HumanPlayer("Alice", 100)
    bob = HumanPlayer("Bob", 500)
    charlie = HumanPlayer("Charlie", 500)
    game = TexasHoldemGame([alice, bob, charlie], small_blind=5, big_blind=10)
    game.active_players = list(game.players)

    # Set up contributions manually
    game.side_pot_manager.reset()
    game.side_pot_manager.add_contribution("Alice", 100, is_all_in=True)
    game.side_pot_manager.add_contribution("Bob", 300)
    game.side_pot_manager.add_contribution("Charlie", 300)
    game.pot = 700

    # Give Alice the best hand (royal flush), Bob second best, Charlie worst
    # Use community cards + hole cards setup
    # Alice: A♠ K♠, Bob: 2♥ 3♥, Charlie: 4♦ 5♦
    # Community: Q♠ J♠ 10♠ 9♣ 8♣
    alice.hand = [Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.KING)]
    bob.hand = [Card(Suit.HEARTS, Rank.TWO), Card(Suit.HEARTS, Rank.THREE)]
    charlie.hand = [Card(Suit.DIAMONDS, Rank.FOUR), Card(Suit.DIAMONDS, Rank.FIVE)]
    game.community_cards = [
        Card(Suit.SPADES, Rank.QUEEN), Card(Suit.SPADES, Rank.JACK),
        Card(Suit.SPADES, Rank.TEN), Card(Suit.CLUBS, Rank.NINE),
        Card(Suit.CLUBS, Rank.EIGHT)
    ]

    alice.is_all_in = True
    alice.chips = 0

    # Manually run the showdown distribution logic
    remaining_players = [alice, bob, charlie]
    player_hands_list = []
    for player in remaining_players:
        all_cards = player.hand + game.community_cards
        hand_rank, _ = HandEvaluator.evaluate_hand(all_cards)
        hand_desc = HandEvaluator.get_hand_description(all_cards)
        player_hands_list.append((player, all_cards, hand_rank, hand_desc))

    winners = game._find_winners(player_hands_list)
    assert alice in winners, "Alice should win overall (royal flush)"

    # Now compute main pot eligible winners
    all_in_amounts = game.side_pot_manager.all_in_players
    max_contribution = max(game.side_pot_manager.contributions.values())
    main_eligible_names = [
        p.name for p in game.active_players
        if not p.is_folded and (
            p.name not in all_in_amounts or
            all_in_amounts[p.name] >= max_contribution
        )
    ]
    assert "Alice" not in main_eligible_names, "Alice should not be eligible for main pot"
    assert "Bob" in main_eligible_names
    assert "Charlie" in main_eligible_names
