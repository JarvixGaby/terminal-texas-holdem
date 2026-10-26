# -*- coding: utf-8 -*-
"""Structured engine events emitted by the poker engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class EngineEvent:
    type: str
    hand_id: str
    phase: str
    public_payload: Dict[str, Any] = field(default_factory=dict)
    private_payload_by_player: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ShowdownStartedEvent(EngineEvent):
    """Public event emitted when the hand reaches showdown."""


@dataclass(frozen=True)
class PlayerHandRevealedEvent(EngineEvent):
    """Public event emitted when a showdown player's hole cards are revealed."""


@dataclass(frozen=True)
class WinnerAnnouncedEvent(EngineEvent):
    """Public event emitted when the hand winner announcement is ready."""


@dataclass(frozen=True)
class PotDistributedEvent(EngineEvent):
    """Public event emitted when visible pot winnings are distributed."""


@dataclass(frozen=True)
class DecisionFeedbackDisplayedEvent(EngineEvent):
    """Public event emitted when compact human decision feedback is displayed."""
