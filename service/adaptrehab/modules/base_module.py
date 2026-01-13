"""
Base Adaptation Module Interface (AMI)

All AI modules must implement this interface to be compatible with the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AdaptationAction(Enum):
    """Standard adaptation actions"""
    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"


@dataclass
class StateVector:
    """Standardized state representation"""
    performance_metrics: Dict[str, float]  # e.g., {'accuracy': 0.8, 'speed': 1.2}
    sensor_data: Dict[str, float]          # e.g., {'hand_velocity': 0.5}
    task_state: Dict[str, Any]             # e.g., {'difficulty': 0.5, 'round': 3}
    timestamp: float
    session_id: str


@dataclass
class AdaptationDecision:
    """Standardized adaptation output"""
    action: AdaptationAction
    magnitude: float  # 0.0-1.0, how much to change
    parameters: Dict[str, Any]  # Specific parameters to adjust
    confidence: float  # 0.0-1.0, confidence in decision
    explanation: str  # Human-readable reasoning


class AdaptationModule(ABC):
    """
    Base interface for all adaptation modules.
    
    This is the Adaptation Module Interface (AMI) that ensures
    interchangeability of different AI algorithms.
    """
    
    def __init__(self, module_id: str):
        self.module_id = module_id
        self.is_initialized = False
        self._last_decision: Optional[AdaptationDecision] = None
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any], patient_profile: Dict[str, Any]) -> bool:
        """
        Initialize the module with configuration and patient data.
        
        Args:
            config: Module-specific configuration parameters
            patient_profile: Patient information (baseline, condition, etc.)
            
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def compute_adaptation(self, state: StateVector) -> AdaptationDecision:
        """
        Compute the next adaptation decision based on current state.
        
        This is the core method called in the adaptation loop.
        
        Args:
            state: Current state vector with performance and sensor data
            
        Returns:
            AdaptationDecision with action, magnitude, and parameters
        """
        pass
    
    @abstractmethod
    async def update(self, reward_signal: float) -> None:
        """
        Update module based on outcome (optional for non-learning algorithms).
        
        For learning-based modules (RL), this provides feedback.
        For rule-based modules, this can be a no-op.
        
        Args:
            reward_signal: Scalar reward (-1.0 to 1.0), higher is better
        """
        pass
    
    @abstractmethod
    def explain(self) -> Dict[str, Any]:
        """
        Return human-readable explanation of the last decision.
        
        Critical for clinical transparency and therapist trust.
        
        Returns:
            Dictionary with explanation details
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Return module metadata and capabilities.
        
        Returns:
            {
                'name': str,
                'version': str,
                'type': 'rule-based' | 'fuzzy' | 'rl',
                'requires_training': bool,
                'supports_explanation': bool,
                'latency_estimate_ms': float
            }
        """
        pass
    
    @abstractmethod
    async def reset(self) -> None:
        """Reset module state (e.g., between sessions)"""
        pass
    
    @abstractmethod
    async def save_checkpoint(self, path: str) -> bool:
        """Save module state/model to disk"""
        pass
    
    @abstractmethod
    async def load_checkpoint(self, path: str) -> bool:
        """Load module state/model from disk"""
        pass
    
    # Helper methods (optional to override)
    
    def validate_state(self, state: StateVector) -> bool:
        """Validate state vector format"""
        return (
            state.performance_metrics is not None
            and state.sensor_data is not None
            and state.task_state is not None
        )
    
    def get_last_decision(self) -> Optional[AdaptationDecision]:
        """Get the last decision made by this module"""
        return self._last_decision
