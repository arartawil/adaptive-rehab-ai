"""
Safety Wrapper - Clinical safety validation layer.

Ensures all adaptation decisions meet safety constraints before execution.
"""

import logging
from typing import Dict, Any, Tuple
from dataclasses import asdict

from adaptrehab.modules.base_module import (
    AdaptationDecision,
    AdaptationAction,
    StateVector
)


logger = logging.getLogger(__name__)


class SafetyWrapper:
    """
    Validates adaptation decisions against clinical safety bounds.
    
    This is a critical component that prevents unsafe adaptations
    regardless of which AI module generated them.
    """
    
    def __init__(self, safety_config: Dict[str, Any]):
        self.config = safety_config
        self.bounds: Dict[str, Any] = {}
        self.violation_log: list = []
        self.enabled = safety_config.get('enabled', True)
        
        # Default safety parameters
        self.max_change_rate = safety_config.get('max_change_rate', 0.2)  # Max 20% change
        self.min_confidence = safety_config.get('min_confidence', 0.3)
        
        logger.info(f"SafetyWrapper initialized (enabled={self.enabled})")
    
    def set_bounds(self, bounds: Dict[str, Any]) -> None:
        """
        Set safety bounds for current task.
        
        Args:
            bounds: Dictionary with min/max values for parameters
                   e.g., {'difficulty': {'min': 0.0, 'max': 1.0}}
        """
        self.bounds = bounds
        logger.info(f"Safety bounds configured: {bounds}")
    
    async def validate_decision(
        self,
        decision: AdaptationDecision,
        current_state: StateVector
    ) -> Tuple[AdaptationDecision, bool]:
        """
        Validate and potentially modify an adaptation decision.
        
        Args:
            decision: Original decision from AI module
            current_state: Current state for context
            
        Returns:
            (validated_decision, was_modified)
        """
        if not self.enabled:
            return decision, False
        
        was_modified = False
        modified_decision = decision
        
        # 1. Check confidence threshold
        if decision.confidence < self.min_confidence:
            logger.warning(f"Low confidence decision: {decision.confidence:.2f}")
            modified_decision = self._create_safe_default(current_state)
            modified_decision.explanation = (
                f"Original confidence too low ({decision.confidence:.2f}). "
                "Defaulting to maintain."
            )
            was_modified = True
            self._log_violation("low_confidence", decision)
        
        # 2. Check parameter bounds
        bounded_params, params_modified = self._apply_parameter_bounds(
            modified_decision.parameters
        )
        if params_modified:
            modified_decision.parameters = bounded_params
            was_modified = True
            self._log_violation("parameter_bounds", decision)
        
        # 3. Check change rate
        rate_limited, rate_modified = self._apply_rate_limiting(
            modified_decision,
            current_state
        )
        if rate_modified:
            modified_decision = rate_limited
            was_modified = True
            self._log_violation("rate_limit", decision)
        
        # 4. Validate action feasibility
        if not self._is_action_feasible(modified_decision, current_state):
            logger.warning("Action not feasible, defaulting to maintain")
            modified_decision = self._create_safe_default(current_state)
            modified_decision.explanation = "Action not feasible. Maintaining current difficulty."
            was_modified = True
            self._log_violation("infeasible_action", decision)
        
        if was_modified:
            logger.info(f"Safety intervention applied: {modified_decision.explanation}")
        
        return modified_decision, was_modified
    
    def _apply_parameter_bounds(
        self,
        parameters: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool]:
        """Apply min/max bounds to parameters."""
        modified = False
        bounded = parameters.copy()
        
        for param_name, value in parameters.items():
            if param_name in self.bounds:
                bounds = self.bounds[param_name]
                
                if isinstance(bounds, dict) and 'min' in bounds and 'max' in bounds:
                    min_val = bounds['min']
                    max_val = bounds['max']
                    
                    if isinstance(value, (int, float)):
                        if value < min_val:
                            bounded[param_name] = min_val
                            modified = True
                            logger.debug(f"{param_name} clamped to min: {min_val}")
                        elif value > max_val:
                            bounded[param_name] = max_val
                            modified = True
                            logger.debug(f"{param_name} clamped to max: {max_val}")
        
        return bounded, modified
    
    def _apply_rate_limiting(
        self,
        decision: AdaptationDecision,
        current_state: StateVector
    ) -> Tuple[AdaptationDecision, bool]:
        """
        Limit rate of change to prevent sudden jumps.
        
        Prevents AI from making drastic changes that might frustrate patients.
        """
        modified = False
        limited_decision = decision
        
        # Check if magnitude exceeds max change rate
        if decision.magnitude > self.max_change_rate:
            limited_decision.magnitude = self.max_change_rate
            limited_decision.explanation += f" [Rate limited to {self.max_change_rate}]"
            modified = True
            logger.debug(f"Magnitude rate limited: {decision.magnitude} -> {self.max_change_rate}")
        
        return limited_decision, modified
    
    def _is_action_feasible(
        self,
        decision: AdaptationDecision,
        current_state: StateVector
    ) -> bool:
        """Check if action is feasible given current state."""
        
        # Get current difficulty if available (convert from string if needed)
        current_difficulty = current_state.task_state.get('difficulty', 0.5)
        if isinstance(current_difficulty, str):
            current_difficulty = float(current_difficulty)
        
        # Can't increase if already at max
        if decision.action == AdaptationAction.INCREASE:
            if 'difficulty' in self.bounds:
                max_diff = self.bounds['difficulty'].get('max', 1.0)
                if current_difficulty >= max_diff:
                    return False
        
        # Can't decrease if already at min
        elif decision.action == AdaptationAction.DECREASE:
            if 'difficulty' in self.bounds:
                min_diff = self.bounds['difficulty'].get('min', 0.0)
                if current_difficulty <= min_diff:
                    return False
        
        return True
    
    def _create_safe_default(self, current_state: StateVector) -> AdaptationDecision:
        """Create a safe default decision (maintain current state)."""
        return AdaptationDecision(
            action=AdaptationAction.MAINTAIN,
            magnitude=0.0,
            parameters={},
            confidence=1.0,
            explanation="Safety override: maintaining current difficulty"
        )
    
    def _log_violation(self, violation_type: str, decision: AdaptationDecision) -> None:
        """Log safety violations for analysis."""
        self.violation_log.append({
            'type': violation_type,
            'decision': asdict(decision),
            'timestamp': None  # Add timestamp in production
        })
        
        # Keep log size manageable
        if len(self.violation_log) > 1000:
            self.violation_log = self.violation_log[-1000:]
    
    def get_violation_stats(self) -> Dict[str, int]:
        """Get statistics on safety violations."""
        stats = {}
        for violation in self.violation_log:
            v_type = violation['type']
            stats[v_type] = stats.get(v_type, 0) + 1
        return stats
    
    def clear_violations(self) -> None:
        """Clear violation log."""
        self.violation_log.clear()
