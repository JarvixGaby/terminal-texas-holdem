# -*- coding: utf-8 -*-
"""Immutable public/private state contract for future external poker agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple

from decision_provider import GameStateSnapshot

_PRIVATE_ACTION_HISTORY_KEYS = {
    "deck",
    "hole_cards",
    "opponent_hole_cards",
    "private_ai_internals",
    "unsafe_seed",
}


@dataclass(frozen=True)
class PublicAgentPlayerState:
    name: str
    chips: int
    current_bet: int
    is_folded: bool
    is_all_in: bool
    position: int


@dataclass(frozen=True)
class ExternalAgentState:
    game_id: str
    hand_id: str
    phase: str
    player_name: str
    position: int
    private_hole_cards: Tuple[str, ...]
    community_cards: Tuple[str, ...]
    pot_size: int
    current_bet: int
    amount_to_call: int
    player_chips: int
    public_players: Tuple[PublicAgentPlayerState, ...]
    action_history: Tuple[Dict[str, Any], ...]
    legal_actions: Tuple[str, ...]
    min_raise: int
    dealer_position: int
    small_blind: int
    big_blind: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def external_agent_state_from_snapshot(snapshot: GameStateSnapshot) -> ExternalAgentState:
    public_players = tuple(
        PublicAgentPlayerState(
            name=player.name,
            chips=player.chips,
            current_bet=player.current_bet,
            is_folded=player.is_folded,
            is_all_in=player.is_all_in,
            position=player.position,
        )
        for player in snapshot.visible_players
    )
    action_history = tuple(_public_action(action) for action in snapshot.action_history)
    return ExternalAgentState(
        game_id=snapshot.game_id,
        hand_id=snapshot.hand_id,
        phase=snapshot.phase,
        player_name=snapshot.player_name,
        position=snapshot.position,
        private_hole_cards=tuple(snapshot.hole_cards),
        community_cards=tuple(snapshot.community_cards),
        pot_size=snapshot.pot_size,
        current_bet=snapshot.current_bet,
        amount_to_call=snapshot.amount_to_call,
        player_chips=snapshot.player_chips,
        public_players=public_players,
        action_history=action_history,
        legal_actions=tuple(snapshot.legal_actions),
        min_raise=snapshot.min_raise,
        dealer_position=snapshot.dealer_position,
        small_blind=snapshot.small_blind,
        big_blind=snapshot.big_blind,
    )


def _public_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe public action event without private game internals."""
    return {
        str(key): _public_value(value)
        for key, value in action.items()
        if str(key) not in _PRIVATE_ACTION_HISTORY_KEYS
    }


def _public_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _public_action(value)
    if isinstance(value, (list, tuple)):
        return [_public_value(item) for item in value]
    return value
