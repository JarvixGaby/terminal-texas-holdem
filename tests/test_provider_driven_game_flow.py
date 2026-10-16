from action_validator import ValidatedAction
from decision_provider import ActionResponse, DecisionProvider
from game import TexasHoldemGame
from player import AIPlayer, HumanPlayer


class FixedProvider(DecisionProvider):
    def __init__(self, action, amount=0):
        self.action = action
        self.amount = amount
        self.seen_state = None

    def decide(self, state):
        self.seen_state = state
        return ActionResponse(self.action, self.amount, metadata={"source": "test"}, raw_response=(self.action, self.amount))


class SequenceProvider(DecisionProvider):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.states = []

    def decide(self, state):
        self.calls += 1
        self.states.append(state)
        action, amount = self.responses.pop(0)
        return ActionResponse(action, amount, metadata={"source": "test"}, raw_response=(action, amount))


def make_game():
    players = [AIPlayer("AI-1", 100), AIPlayer("AI-2", 100), AIPlayer("AI-3", 100)]
    game = TexasHoldemGame(players, small_blind=5, big_blind=10)
    game.active_players = players
    game.current_game_id = "test-hand"
    game.game_phase = "preflop"
    return game, players


def test_game_builds_public_snapshot_for_decision_provider_without_private_leaks():
    game, players = make_game()
    players[0].hand = ["PRIVATE-A", "PRIVATE-B"]
    players[1].hand = ["OPPONENT-A", "OPPONENT-B"]
    game.current_bet = 10
    players[0].current_bet = 5

    snapshot = game._build_game_state_snapshot(players[0], amount_to_call=5, legal_actions=["call", "raise", "fold"], min_raise=20)

    assert snapshot.player_name == "AI-1"
    assert snapshot.amount_to_call == 5
    assert snapshot.legal_actions == ["call", "raise", "fold"]
    assert snapshot.hole_cards == ["PRIVATE-A", "PRIVATE-B"]
    serialized = repr(snapshot)
    assert "OPPONENT-A" not in serialized
    assert "OPPONENT-B" not in serialized
    assert "deck" not in serialized.lower()


def test_get_player_action_uses_provider_and_validator_fallback_for_illegal_action():
    game, players = make_game()
    provider = FixedProvider("check", 0)
    game.set_decision_provider(players[0].name, provider)
    game.current_bet = 20
    players[0].current_bet = 0

    action, amount = game._get_player_action(players[0], amount_to_call=20)

    assert action == "fold"
    assert amount == 0
    assert provider.seen_state.amount_to_call == 20
    assert game.last_action_response.action == "check"
    assert isinstance(game.last_validated_action, ValidatedAction)
    assert game.last_validated_action.is_valid is False
    assert "illegal action" in game.last_validated_action.reason


def test_human_raise_prompt_uses_same_total_bet_range_as_validator(monkeypatch):
    game, players = make_game()
    hero = players[0]
    game.current_bet = 20
    hero.current_bet = 5
    hero.chips = 95
    answers = iter(["100", "y"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    action, amount = game._handle_raise_action(amount_to_call=15, player=hero)

    assert action == "raise"
    assert amount == 100


def test_human_no_bet_prompt_accepts_bet_alias(monkeypatch, capsys):
    hero = HumanPlayer("Hero", 100)
    villain = AIPlayer("Villain", 100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.active_players = [hero, villain]
    game.current_bet = 0
    game.assistant_enabled = False
    answers = iter(["bet", "20", "y"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    action, amount = game._get_human_action(hero, amount_to_call=0)

    assert action == "raise"
    assert amount == 20
    output = capsys.readouterr().out
    assert "可选动作: check, bet, fold" in output
    assert "可选动作: check, raise, fold" not in output
    assert "下注设置" in output


def test_human_facing_bet_prompt_uses_raise_label(monkeypatch, capsys):
    hero = HumanPlayer("Hero", 100)
    villain = AIPlayer("Villain", 100)
    game = TexasHoldemGame([hero, villain], small_blind=5, big_blind=10)
    game.active_players = [hero, villain]
    game.current_bet = 20
    hero.current_bet = 0
    game.assistant_enabled = False
    answers = iter(["raise", "40", "y"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    action, amount = game._get_human_action(hero, amount_to_call=20)

    assert action == "raise"
    assert amount == 40
    output = capsys.readouterr().out
    assert "可选动作: call, raise, fold" in output
    assert "加注设置" in output


def test_betting_round_ends_after_last_raise_is_called(monkeypatch):
    game, players = make_game()
    hero, villain = players[0], players[1]
    game.active_players = [hero, villain]
    game.game_phase = "preflop"
    game.current_bet = 10
    hero.current_bet = 0
    villain.current_bet = 10
    game.pot = 10
    monkeypatch.setattr(game, "_get_betting_order", lambda: [hero, villain])

    hero_provider = SequenceProvider([("call", 10), ("call", 10)])
    villain_provider = SequenceProvider([("raise", 20), ("raise", 30)])
    game.set_decision_provider(hero.name, hero_provider)
    game.set_decision_provider(villain.name, villain_provider)

    assert game._betting_round() is True

    assert hero.current_bet == 20
    assert villain.current_bet == 20
    assert villain_provider.calls == 1


def test_short_all_in_raise_does_not_reopen_action(monkeypatch):
    game, players = make_game()
    opener, short_stack, caller = players
    game.active_players = [opener, short_stack, caller]
    game.game_phase = "preflop"
    game.current_bet = 20
    opener.current_bet = 20
    short_stack.current_bet = 20
    caller.current_bet = 20
    game.pot = 100
    short_stack.chips = 5
    monkeypatch.setattr(game, "_get_betting_order", lambda: [opener, short_stack, caller])

    opener_provider = SequenceProvider([("check", 0), ("call", 5)])
    short_provider = SequenceProvider([("raise", 25)])
    caller_provider = SequenceProvider([("call", 5)])
    game.set_decision_provider(opener.name, opener_provider)
    game.set_decision_provider(short_stack.name, short_provider)
    game.set_decision_provider(caller.name, caller_provider)

    assert game._betting_round() is True

    assert opener.current_bet == 25
    assert short_stack.current_bet == 25
    assert short_stack.is_all_in is True
    assert caller.current_bet == 25
    assert opener_provider.calls == 2
    assert "raise" not in opener_provider.states[1].legal_actions


def test_minimum_raise_total_tracks_last_full_raise_increment():
    game, players = make_game()
    game.current_bet = 25
    game.last_full_raise_increment = 15

    assert game._get_min_raise_total() == 40


def test_short_stack_can_make_all_in_bet_when_below_minimum():
    game, players = make_game()
    hero = players[0]
    game.current_bet = 0
    hero.current_bet = 0
    hero.chips = 5

    assert "raise" in game._get_legal_actions(hero, amount_to_call=0)


def test_record_processed_action_stores_provider_validation_metadata_in_history():
    game, players = make_game()
    game.history_manager.start_new_game_record([p.name for p in players], 5, 10, 0)
    game.history_manager.start_new_phase("preflop", [], 15, 10)
    game.last_action_response = ActionResponse("check", 0, metadata={"source": "test"}, raw_response=("check", 0))
    game.last_validated_action = ValidatedAction("fold", 0, False, "check illegal when facing a bet", "check", 0)

    game._record_processed_action(
        players[0],
        "fold",
        0,
        chips_before=100,
        amount_to_call=20,
        legal_actions=["call", "raise", "fold"],
        min_raise=40,
        decision_pot_size=15,
        decision_player_chips=100,
        decision_current_bet=20,
    )

    action_record = game.history_manager.current_game_record.phases[-1].actions[-1]
    assert action_record.action == "fold"
    assert action_record.action_metadata["raw_action"] == "check"
    assert action_record.action_metadata["validated_action"] == "fold"
    assert action_record.action_metadata["is_valid"] is False
    assert action_record.action_metadata["provider_metadata"] == {"source": "test"}
