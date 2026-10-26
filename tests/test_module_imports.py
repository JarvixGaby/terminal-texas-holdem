"""Module import smoke tests for baseline repository health."""

import importlib


MODULES = [
    "texas_holdem.engine.card",
    "texas_holdem.engine.game",
    "texas_holdem.training.hand_coach",
    "texas_holdem.engine.hand_evaluator",
    "main",
    "texas_holdem.ai.optimized_odds_calculator",
    "texas_holdem.history.quick_replay_system",
    "texas_holdem.engine.side_pot_manager",
    "texas_holdem.training.training_center",
    "ai_system_evaluator",
    "agent_state_contract",
]


def test_core_modules_import_cleanly():
    for module_name in MODULES:
        importlib.import_module(module_name)
