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

__all__ = [
    "AdaptationModule",
    "AdaptationAction",
    "StateVector",
    "AdaptationDecision"
]
