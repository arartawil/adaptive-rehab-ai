"""
Rule-Based Adaptation Module - Simple baseline algorithm.

Uses threshold-based rules to make adaptation decisions.
"""

import logging
from typing import Dict, Any

from adaptrehab.modules.base_module import (
    AdaptationModule,
    AdaptationAction,
    StateVector,
    AdaptationDecision
)


logger = logging.getLogger(__name__)


class RuleBasedModule(AdaptationModule):
    """
    Simple rule-based adaptation using performance thresholds.
    
    Rules:
    - If performance > success_threshold → increase difficulty
    - If performance < failure_threshold → decrease difficulty
    - Otherwise → maintain difficulty
    
    This serves as a baseline for comparing more complex algorithms.
    """
    
    def __init__(self, module_id: str):
        super().__init__(module_id)
        
        # Configuration
        self.success_threshold = 0.8
        self.failure_threshold = 0.4
        self.increase_step = 0.1
        self.decrease_step = 0.15
        
        # State
        self.performance_history: list = []
        self.history_window = 5  # Consider last N adaptations
        
        logger.info(f"RuleBasedModule {module_id} created")
    
    async def initialize(
        self,
        config: Dict[str, Any],
        patient_profile: Dict[str, Any]
    ) -> bool:
        """Initialize with configuration."""
        try:
            # Load config
            self.success_threshold = config.get('success_threshold', 0.8)
            self.failure_threshold = config.get('failure_threshold', 0.4)
            self.increase_step = config.get('increase_step', 0.1)
            self.decrease_step = config.get('decrease_step', 0.15)
            
            # Adjust thresholds based on patient baseline if available
            baseline = patient_profile.get('baseline_performance', None)
            if baseline is not None:
                self.success_threshold = min(0.9, baseline + 0.2)
                self.failure_threshold = max(0.3, baseline - 0.2)
                logger.info(f"Adjusted thresholds for baseline {baseline:.2f}")
            
            self.is_initialized = True
            logger.info(f"RuleBasedModule initialized: success={self.success_threshold}, "
                       f"failure={self.failure_threshold}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RuleBasedModule: {e}", exc_info=True)
            return False
    
    async def compute_adaptation(self, state: StateVector) -> AdaptationDecision:
        """Compute adaptation based on performance rules."""
        
        # Extract performance metrics
        accuracy = state.performance_metrics.get('accuracy', 0.5)
        success_rate = state.performance_metrics.get('success_rate', accuracy)
        
        # Use average of recent performance
        self.performance_history.append(success_rate)
        if len(self.performance_history) > self.history_window:
            self.performance_history.pop(0)
        
        avg_performance = sum(self.performance_history) / len(self.performance_history)
        
        # Apply rules
        if avg_performance >= self.success_threshold:
            action = AdaptationAction.INCREASE
            magnitude = self.increase_step
            explanation = (
                f"Performance {avg_performance:.2f} exceeds threshold {self.success_threshold:.2f}. "
                f"Increasing difficulty by {magnitude:.2f}"
            )
            confidence = min(1.0, (avg_performance - self.success_threshold) / (1.0 - self.success_threshold))
            
        elif avg_performance <= self.failure_threshold:
            action = AdaptationAction.DECREASE
            magnitude = self.decrease_step
            explanation = (
                f"Performance {avg_performance:.2f} below threshold {self.failure_threshold:.2f}. "
                f"Decreasing difficulty by {magnitude:.2f}"
            )
            confidence = min(1.0, (self.failure_threshold - avg_performance) / self.failure_threshold)
            
        else:
            action = AdaptationAction.MAINTAIN
            magnitude = 0.0
            explanation = (
                f"Performance {avg_performance:.2f} in acceptable range "
                f"[{self.failure_threshold:.2f}, {self.success_threshold:.2f}]. "
                "Maintaining difficulty"
            )
            confidence = 0.9  # High confidence in maintaining
        
        # Get current difficulty from state
        current_difficulty = state.task_state.get('difficulty', 0.5)
        
        # Calculate new difficulty
        if action == AdaptationAction.INCREASE:
            new_difficulty = min(1.0, current_difficulty + magnitude)
        elif action == AdaptationAction.DECREASE:
            new_difficulty = max(0.0, current_difficulty - magnitude)
        else:
            new_difficulty = current_difficulty
        
        decision = AdaptationDecision(
            action=action,
            magnitude=magnitude,
            parameters={
                'difficulty': new_difficulty,
                'current_performance': avg_performance
            },
            confidence=confidence,
            explanation=explanation
        )
        
        self._last_decision = decision
        
        logger.debug(f"Rule decision: {action.value}, difficulty: {current_difficulty:.2f} → {new_difficulty:.2f}")
        
        return decision
    
    async def update(self, reward_signal: float) -> None:
        """
        Update based on reward (no-op for rule-based).
        
        Rule-based doesn't learn, but we could adjust thresholds
        based on long-term success patterns in future versions.
        """
        pass  # Rule-based doesn't learn
    
    def explain(self) -> Dict[str, Any]:
        """Explain last decision."""
        if self._last_decision is None:
            return {'explanation': 'No decision made yet'}
        
        return {
            'module_type': 'rule_based',
            'decision': self._last_decision.action.value,
            'reasoning': self._last_decision.explanation,
            'thresholds': {
                'success': self.success_threshold,
                'failure': self.failure_threshold
            },
            'performance_history': self.performance_history[-5:],  # Last 5
            'confidence': self._last_decision.confidence
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return module metadata."""
        return {
            'name': 'Rule-Based Adaptation',
            'version': '1.0.0',
            'type': 'rule-based',
            'requires_training': False,
            'supports_explanation': True,
            'latency_estimate_ms': 0.5,  # Very fast
            'parameters': {
                'success_threshold': self.success_threshold,
                'failure_threshold': self.failure_threshold,
                'increase_step': self.increase_step,
                'decrease_step': self.decrease_step
            }
        }
    
    async def reset(self) -> None:
        """Reset module state."""
        self.performance_history.clear()
        self._last_decision = None
        logger.info(f"RuleBasedModule {self.module_id} reset")
    
    async def save_checkpoint(self, path: str) -> bool:
        """
        Save checkpoint (minimal state for rule-based).
        
        Rule-based has no learned parameters, but we save
        performance history for continuity.
        """
        try:
            import json
            from pathlib import Path
            
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            checkpoint = {
                'module_id': self.module_id,
                'module_type': 'rule_based',
                'performance_history': self.performance_history,
                'config': {
                    'success_threshold': self.success_threshold,
                    'failure_threshold': self.failure_threshold,
                    'increase_step': self.increase_step,
                    'decrease_step': self.decrease_step
                }
            }
            
            with open(path, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            logger.info(f"Checkpoint saved: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}", exc_info=True)
            return False
    
    async def load_checkpoint(self, path: str) -> bool:
        """Load checkpoint."""
        try:
            import json
            
            with open(path, 'r') as f:
                checkpoint = json.load(f)
            
            self.performance_history = checkpoint.get('performance_history', [])
            
            config = checkpoint.get('config', {})
            self.success_threshold = config.get('success_threshold', self.success_threshold)
            self.failure_threshold = config.get('failure_threshold', self.failure_threshold)
            self.increase_step = config.get('increase_step', self.increase_step)
            self.decrease_step = config.get('decrease_step', self.decrease_step)
            
            logger.info(f"Checkpoint loaded: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}", exc_info=True)
            return False
