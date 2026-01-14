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

__all__ = [
    "AdaptationModule",
    "AdaptationAction",
    "StateVector",
    "AdaptationDecision",
    "RuleBasedModule",
    "FuzzyLogicModule"
]
