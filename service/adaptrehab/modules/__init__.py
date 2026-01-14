"""
Adaptation modules package.

Contains all AI algorithm implementations that follow the AMI interface.
"""

from adaptrehab.modules.base_module import (
    AdaptationModule,
    AdaptationAction,
    StateVector,
    AdaptationDecision
)
from adaptrehab.modules.rule_based import RuleBasedModule
from adaptrehab.modules.fuzzy_logic import FuzzyLogicModule
from adaptrehab.modules.reinforcement_learning import ReinforcementLearningModule

__all__ = [
    "AdaptationModule",
    "AdaptationAction",
    "StateVector",
    "AdaptationDecision",
    "RuleBasedModule",
    "FuzzyLogicModule",
    "ReinforcementLearningModule"
]
