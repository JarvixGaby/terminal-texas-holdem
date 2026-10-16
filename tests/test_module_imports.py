"""Module import smoke tests for baseline repository health."""

import importlib


MODULES = [
    "card",
    "game",
    "hand_coach",
    "hand_evaluator",
    "main",
    "optimized_odds_calculator",
    "quick_replay_system",
    "side_pot_manager",
    "training_center",
]


def test_core_modules_import_cleanly():
    for module_name in MODULES:
        importlib.import_module(module_name)
