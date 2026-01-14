"""
Fuzzy Logic Adaptation Module

Uses linguistic rules and fuzzy inference for difficulty adaptation.
Example rules:
- IF performance is LOW THEN decrease difficulty
- IF performance is MEDIUM THEN maintain difficulty  
- IF performance is HIGH THEN increase difficulty
"""

import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
import logging

from .base_module import AdaptationModule, StateVector, AdaptationDecision, AdaptationAction


class FuzzyLogicModule(AdaptationModule):
    """
    Fuzzy logic adaptation using linguistic variables and inference rules.
    
    Uses trapezoidal membership functions for:
    - Performance: LOW, MEDIUM, HIGH
    - Difficulty change: DECREASE, MAINTAIN, INCREASE
    
    Rules:
    1. IF performance is LOW THEN decrease difficulty
    2. IF performance is MEDIUM THEN maintain difficulty
    3. IF performance is HIGH THEN increase difficulty
    """
    
    def __init__(self, module_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(module_id)
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.step_size = config.get('step_size', 0.1) if config else 0.1
        self.smooth_factor = config.get('smooth_factor', 0.3) if config else 0.3
        
        # Linguistic variable ranges
        self.perf_range = np.linspace(0, 1, 100)
        self.diff_change_range = np.linspace(-0.2, 0.2, 100)
        
        # Define membership functions
        self._setup_membership_functions()
        
        # History for smoothing
        self.performance_history = []
        self.max_history = 5
        self._last_decision = None
        
        self.logger.info(f"FuzzyLogicModule {module_id} initialized")
        
    def _setup_membership_functions(self):
        """Define trapezoidal membership functions for fuzzy sets."""
        # Performance membership functions (0 to 1)
        # LOW: [0, 0, 0.3, 0.5]
        # MEDIUM: [0.3, 0.5, 0.5, 0.7]
        # HIGH: [0.5, 0.7, 1.0, 1.0]
        
        self.perf_low_params = [0, 0, 0.3, 0.5]
        self.perf_medium_params = [0.3, 0.5, 0.5, 0.7]
        self.perf_high_params = [0.5, 0.7, 1.0, 1.0]
        
        # Difficulty change membership functions (-0.2 to 0.2)
        # DECREASE: [-0.2, -0.2, -0.1, 0]
        # MAINTAIN: [-0.05, 0, 0, 0.05]
        # INCREASE: [0, 0.1, 0.2, 0.2]
        
        self.change_decrease_params = [-0.2, -0.2, -0.1, 0]
        self.change_maintain_params = [-0.05, 0, 0, 0.05]
        self.change_increase_params = [0, 0.1, 0.2, 0.2]
        
    def _trapezoid_membership(self, x: float, params: list) -> float:
        """
        Compute trapezoidal membership function.
        
        Args:
            x: Input value
            params: [a, b, c, d] where:
                - membership is 0 for x <= a
                - linearly increases from a to b
                - membership is 1 for b <= x <= c
                - linearly decreases from c to d
                - membership is 0 for x >= d
                
        Returns:
            Membership degree [0, 1]
        """
        a, b, c, d = params
        
        if x <= a or x >= d:
            return 0.0
        elif a < x < b:
            return (x - a) / (b - a)
        elif b <= x <= c:
            return 1.0
        else:  # c < x < d
            return (d - x) / (d - c)
            
    def _fuzzify_performance(self, performance: float) -> Dict[str, float]:
        """
        Fuzzify performance value into linguistic terms.
        
        Args:
            performance: Performance value [0, 1]
            
        Returns:
            Dictionary of membership degrees for each linguistic term
        """
        return {
            'low': self._trapezoid_membership(performance, self.perf_low_params),
            'medium': self._trapezoid_membership(performance, self.perf_medium_params),
            'high': self._trapezoid_membership(performance, self.perf_high_params)
        }
        
    def _apply_fuzzy_rules(self, fuzzy_perf: Dict[str, float]) -> Dict[str, float]:
        """
        Apply fuzzy inference rules.
        
        Rules:
        1. IF performance is LOW THEN decrease difficulty
        2. IF performance is MEDIUM THEN maintain difficulty
        3. IF performance is HIGH THEN increase difficulty
        
        Args:
            fuzzy_perf: Fuzzified performance values
            
        Returns:
            Fuzzy output for difficulty change
        """
        # Rule outputs (using min for AND, max for aggregation)
        return {
            'decrease': fuzzy_perf['low'],
            'maintain': fuzzy_perf['medium'],
            'increase': fuzzy_perf['high']
        }
        
    def _defuzzify(self, fuzzy_output: Dict[str, float]) -> float:
        """
        Defuzzify using centroid method (center of gravity).
        
        Args:
            fuzzy_output: Fuzzy output values
            
        Returns:
            Crisp difficulty change value
        """
        # Calculate centers of each membership function
        decrease_center = -0.1  # Center of decrease trapezoid
        maintain_center = 0.0   # Center of maintain trapezoid
        increase_center = 0.1   # Center of increase trapezoid
        
        # Weighted average (centroid defuzzification)
        numerator = (
            fuzzy_output['decrease'] * decrease_center +
            fuzzy_output['maintain'] * maintain_center +
            fuzzy_output['increase'] * increase_center
        )
        
        denominator = sum(fuzzy_output.values())
        
        if denominator == 0:
            return 0.0  # No change if all memberships are 0
            
        return numerator / denominator
        
    def _compute_aggregate_performance(self, state: StateVector) -> float:
        """
        Compute aggregate performance metric from state.
        
        Combines multiple metrics into a single performance score.
        """
        metrics = state.performance_metrics
        
        # Extract relevant metrics
        accuracy = metrics.get('accuracy', 0.5)
        success_rate = metrics.get('success_rate', accuracy)
        
        # Error rate (inverted)
        error_rate = metrics.get('error_rate', 1 - accuracy)
        error_score = 1 - error_rate
        
        # Reaction time (faster is better, normalize assuming 0-2 seconds)
        reaction_time = metrics.get('reaction_time', 1.0)
        reaction_score = max(0, 1 - (reaction_time / 2.0))
        
        # Weighted average
        weights = {
            'accuracy': 0.4,
            'success': 0.3,
            'error': 0.2,
            'reaction': 0.1
        }
        
        performance = (
            weights['accuracy'] * accuracy +
            weights['success'] * success_rate +
            weights['error'] * error_score +
            weights['reaction'] * reaction_score
        )
        
        # Add to history for smoothing
        self.performance_history.append(performance)
        if len(self.performance_history) > self.max_history:
            self.performance_history.pop(0)
            
        # Return smoothed performance
        if len(self.performance_history) > 1:
            return np.mean(self.performance_history)
        else:
            return performance
            
    async def compute_adaptation(self, state: StateVector) -> AdaptationDecision:
        """
        Compute adaptation using fuzzy logic inference.
        
        Args:
            state: Current state with performance metrics
            
        Returns:
            Adaptation decision with action and new difficulty
        """
        # Get aggregate performance
        performance = self._compute_aggregate_performance(state)
        
        # Fuzzification
        fuzzy_perf = self._fuzzify_performance(performance)
        
        self.logger.debug(f"Fuzzified performance {performance:.3f}: {fuzzy_perf}")
        
        # Apply fuzzy rules
        fuzzy_output = self._apply_fuzzy_rules(fuzzy_perf)
        
        # Defuzzification
        difficulty_change = self._defuzzify(fuzzy_output)
        
        # Scale by step size
        difficulty_change *= self.step_size
        
        # Get current difficulty
        current_difficulty = state.task_state.get('difficulty', 0.5)
        new_difficulty = np.clip(current_difficulty + difficulty_change, 0.0, 1.0)
        
        # Determine action
        if abs(difficulty_change) < 0.01:
            action = AdaptationAction.MAINTAIN
        elif difficulty_change > 0:
            action = AdaptationAction.INCREASE
        else:
            action = AdaptationAction.DECREASE
            
        # Confidence based on membership strength
        confidence = max(fuzzy_output.values())
        
        # Create explanation
        dominant_term = max(fuzzy_perf, key=fuzzy_perf.get)
        explanation = self._generate_explanation(
            performance, dominant_term, action, confidence
        )
        
        self.logger.info(
            f"Fuzzy decision: perf={performance:.3f}, "
            f"change={difficulty_change:+.3f}, "
            f"action={action.value}, conf={confidence:.2f}"
        )
        
        decision = AdaptationDecision(
            action=action,
            magnitude=abs(difficulty_change),
            confidence=confidence,
            parameters={'difficulty': new_difficulty},
            explanation=explanation
        )
        
        self._last_decision = decision
        return decision
        
    def _generate_explanation(
        self,
        performance: float,
        dominant_term: str,
        action: AdaptationAction,
        confidence: float
    ) -> str:
        """Generate human-readable explanation."""
        perf_desc = {
            'low': 'below target',
            'medium': 'on target',
            'high': 'above target'
        }
        
        action_desc = {
            AdaptationAction.DECREASE: 'Decreasing',
            AdaptationAction.MAINTAIN: 'Maintaining',
            AdaptationAction.INCREASE: 'Increasing'
        }
        
        return (
            f"Performance ({performance:.1%}) is {perf_desc[dominant_term]}. "
            f"{action_desc[action]} difficulty (confidence: {confidence:.0%})"
        )
        
    async def update_feedback(self, reward: float, info: Optional[Dict] = None):
        """
        Update module with feedback.
        
        Fuzzy logic doesn't learn, but we can adjust smoothing.
        """
        # Could adjust smooth_factor based on reward variance
        pass
    
    async def initialize(self, config: Dict[str, Any], patient_profile: Dict[str, Any]) -> bool:
        """Initialize module with patient profile."""
        # Extract any custom configuration from profile
        if 'step_size' in patient_profile:
            self.step_size = patient_profile['step_size']
        if 'smooth_factor' in patient_profile:
            self.smooth_factor = patient_profile['smooth_factor']
        
        self.is_initialized = True
        self.logger.info(f"FuzzyLogicModule initialized for module {self.module_id}")
        return True
    
    async def update(self, reward_signal: float) -> None:
        """Update module with reward signal (no-op for fuzzy logic)."""
        pass
    
    def explain(self) -> Dict[str, Any]:
        """Return explanation of last decision."""
        if not hasattr(self, '_last_decision') or self._last_decision is None:
            return {'explanation': 'No decision made yet'}
        
        return {
            'explanation': self._last_decision.explanation,
            'confidence': self._last_decision.confidence,
            'action': self._last_decision.action.value,
            'parameters': self._last_decision.parameters,
            'method': 'fuzzy_logic_inference'
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return module metadata."""
        return {
            'name': 'Fuzzy Logic Adaptation',
            'version': '1.0.0',
            'type': 'fuzzy',
            'requires_training': False,
            'supports_explanation': True,
            'latency_estimate_ms': 0.5,
            'linguistic_variables': ['LOW', 'MEDIUM', 'HIGH'],
            'rules_count': 3
        }
        
    async def reset(self) -> None:
        """Reset module state."""
        self.performance_history.clear()
        self._last_decision = None
        self.logger.info(f"FuzzyLogicModule {self.module_id} reset")
    
    async def save_checkpoint(self, path: str) -> bool:
        """Save module state (no learned parameters for fuzzy logic)."""
        import json
        try:
            state = {
                'module_id': self.module_id,
                'performance_history': self.performance_history,
                'step_size': self.step_size,
                'smooth_factor': self.smooth_factor
            }
            with open(path, 'w') as f:
                json.dump(state, f)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    async def load_checkpoint(self, path: str) -> bool:
        """Load module state."""
        import json
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            self.performance_history = state.get('performance_history', [])
            self.step_size = state.get('step_size', 0.1)
            self.smooth_factor = state.get('smooth_factor', 0.3)
            return True
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return False

