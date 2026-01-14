"""
Reinforcement Learning Adaptation Module

Uses Q-learning to learn optimal adaptation policies through trial and error.
The agent learns which difficulty adjustments maximize patient progress.

Key Features:
- State discretization for tractable learning
- Q-table for state-action values
- Epsilon-greedy exploration
- Reward based on performance trajectory
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time
import logging
import json
import os

from .base_module import AdaptationModule, StateVector, AdaptationDecision, AdaptationAction


@dataclass
class Experience:
    """Single experience tuple for learning"""
    state: Tuple[int, ...]
    action: AdaptationAction
    reward: float
    next_state: Tuple[int, ...]
    done: bool


class ReinforcementLearningModule(AdaptationModule):
    """
    Q-learning based adaptation module.
    
    Learns optimal difficulty adjustment policy by:
    1. Discretizing continuous state space
    2. Maintaining Q-table of state-action values
    3. Exploring actions with epsilon-greedy policy
    4. Learning from rewards based on performance improvement
    
    Reward function:
    - Positive reward for improved performance
    - Negative reward for decreased performance
    - Small penalty for excessive changes
    - Bonus for maintaining flow state (0.5-0.7 performance)
    """
    
    def __init__(self, module_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(module_id)
        
        self.logger = logging.getLogger(__name__)
        
        # Q-learning hyperparameters
        config = config or {}
        self.alpha = config.get('learning_rate', 0.1)  # Learning rate
        self.gamma = config.get('discount_factor', 0.9)  # Discount factor
        self.epsilon = config.get('exploration_rate', 0.2)  # Exploration rate
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.epsilon_min = config.get('epsilon_min', 0.01)
        
        # State discretization
        self.perf_bins = config.get('perf_bins', 10)  # Performance buckets
        self.diff_bins = config.get('diff_bins', 5)   # Difficulty buckets
        self.trend_bins = config.get('trend_bins', 3)  # Trend buckets (-1, 0, 1)
        
        # Q-table: dict[(state) -> dict[action -> Q-value]]
        self.q_table: Dict[Tuple, Dict[AdaptationAction, float]] = {}
        
        # Experience tracking
        self.last_state: Optional[Tuple] = None
        self.last_action: Optional[AdaptationAction] = None
        self.performance_history = []
        self.max_history = 10
        
        # Persistence
        self.save_path = config.get('save_path', None)
        if self.save_path:
            self._load_q_table()
        
        self.logger.info(f"ReinforcementLearningModule {module_id} initialized")
        self.logger.info(f"Hyperparameters: α={self.alpha}, γ={self.gamma}, ε={self.epsilon}")
        
    async def initialize(self, config: Dict[str, Any], patient_profile: Dict[str, Any]) -> bool:
        """Initialize the RL module."""
        self.is_initialized = True
        self.logger.info(f"RL module {self.module_id} initialized for patient")
        return True
        
    def _discretize_state(self, state: StateVector) -> Tuple[int, ...]:
        """
        Convert continuous state to discrete state representation.
        
        State tuple: (performance_bin, difficulty_bin, trend_bin)
        """
        # Extract key metrics
        performance = state.performance_metrics.get('accuracy', 0.5)
        difficulty = state.task_state.get('difficulty', 0.5)
        
        # Bin performance (0-1 into n bins)
        perf_bin = min(int(performance * self.perf_bins), self.perf_bins - 1)
        
        # Bin difficulty (0-1 into n bins)
        diff_bin = min(int(difficulty * self.diff_bins), self.diff_bins - 1)
        
        # Calculate performance trend
        trend_bin = self._calculate_trend_bin()
        
        return (perf_bin, diff_bin, trend_bin)
    
    def _calculate_trend_bin(self) -> int:
        """
        Calculate performance trend from history.
        
        Returns:
            0: declining
            1: stable
            2: improving
        """
        if len(self.performance_history) < 2:
            return 1  # Stable by default
        
        recent = self.performance_history[-3:]
        avg_recent = sum(recent) / len(recent)
        
        older = self.performance_history[:-3] if len(self.performance_history) > 3 else [0.5]
        avg_older = sum(older) / len(older)
        
        if avg_recent > avg_older + 0.05:
            return 2  # Improving
        elif avg_recent < avg_older - 0.05:
            return 0  # Declining
        else:
            return 1  # Stable
    
    def _get_q_value(self, state: Tuple, action: AdaptationAction) -> float:
        """Get Q-value for state-action pair, initializing if needed."""
        if state not in self.q_table:
            # Initialize all actions for new state
            self.q_table[state] = {
                AdaptationAction.DECREASE: 0.0,
                AdaptationAction.MAINTAIN: 0.0,
                AdaptationAction.INCREASE: 0.0
            }
        return self.q_table[state][action]
    
    def _set_q_value(self, state: Tuple, action: AdaptationAction, value: float):
        """Set Q-value for state-action pair."""
        if state not in self.q_table:
            self.q_table[state] = {
                AdaptationAction.DECREASE: 0.0,
                AdaptationAction.MAINTAIN: 0.0,
                AdaptationAction.INCREASE: 0.0
            }
        self.q_table[state][action] = value
    
    def _select_action(self, state: Tuple) -> AdaptationAction:
        """
        Select action using epsilon-greedy policy.
        
        With probability epsilon: explore (random action)
        With probability 1-epsilon: exploit (best known action)
        """
        if np.random.random() < self.epsilon:
            # Explore: random action
            return np.random.choice(list(AdaptationAction))
        else:
            # Exploit: best action according to Q-table
            if state not in self.q_table:
                return AdaptationAction.MAINTAIN  # Safe default
            
            q_values = self.q_table[state]
            best_action = max(q_values, key=q_values.get)
            return best_action
    
    def _calculate_reward(self, state: StateVector, action: AdaptationAction) -> float:
        """
        Calculate reward based on performance and action appropriateness.
        
        Reward components:
        1. Performance improvement: +/-0.5
        2. Flow state bonus: +0.2 if in 0.5-0.7 range
        3. Stability bonus: +0.1 for not changing when performing well
        4. Excessive change penalty: -0.2 for changing too much
        """
        performance = state.performance_metrics.get('accuracy', 0.5)
        
        # Track performance history
        self.performance_history.append(performance)
        if len(self.performance_history) > self.max_history:
            self.performance_history.pop(0)
        
        reward = 0.0
        
        # 1. Performance improvement reward
        if len(self.performance_history) >= 2:
            improvement = performance - self.performance_history[-2]
            reward += improvement * 0.5
        
        # 2. Flow state bonus (optimal challenge)
        if 0.5 <= performance <= 0.7:
            reward += 0.2
        
        # 3. Stability bonus (don't change if performing well)
        if 0.6 <= performance <= 0.8 and action == AdaptationAction.MAINTAIN:
            reward += 0.1
        
        # 4. Appropriate action bonus
        if performance < 0.4 and action == AdaptationAction.DECREASE:
            reward += 0.15  # Good decision to make it easier
        elif performance > 0.8 and action == AdaptationAction.INCREASE:
            reward += 0.15  # Good decision to make it harder
        
        # 5. Penalty for performance extremes
        if performance < 0.3 or performance > 0.9:
            reward -= 0.1
        
        return reward
    
    def _update_q_value(self, state: Tuple, action: AdaptationAction, 
                       reward: float, next_state: Tuple):
        """
        Update Q-value using Q-learning update rule.
        
        Q(s,a) = Q(s,a) + α * [r + γ * max(Q(s',a')) - Q(s,a)]
        """
        current_q = self._get_q_value(state, action)
        
        # Get max Q-value for next state
        max_next_q = max(self._get_q_value(next_state, a) 
                        for a in AdaptationAction)
        
        # Q-learning update
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        
        self._set_q_value(state, action, new_q)
        
        # Decay exploration rate
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    async def compute_adaptation(self, state: StateVector) -> AdaptationDecision:
        """
        Compute adaptation decision using Q-learning policy.
        
        Steps:
        1. Discretize current state
        2. Learn from previous experience (if any)
        3. Select action using epsilon-greedy
        4. Return adaptation decision
        """
        start_time = time.time()
        
        # Discretize state
        discrete_state = self._discretize_state(state)
        
        # Learn from previous experience
        if self.last_state is not None and self.last_action is not None:
            reward = self._calculate_reward(state, self.last_action)
            self._update_q_value(self.last_state, self.last_action, 
                               reward, discrete_state)
            
            self.logger.debug(f"Learning: s={self.last_state}, a={self.last_action}, "
                            f"r={reward:.3f}, s'={discrete_state}")
        
        # Select action
        action = self._select_action(discrete_state)
        
        # Convert action to magnitude and parameters
        magnitude = 0.1  # Standard step size
        if action == AdaptationAction.INCREASE:
            magnitude = 0.15
        elif action == AdaptationAction.DECREASE:
            magnitude = 0.15
        else:  # MAINTAIN
            magnitude = 0.0
        
        # Build decision
        decision = AdaptationDecision(
            action=action,
            magnitude=magnitude,
            parameters={
                'difficulty_change': magnitude if action == AdaptationAction.INCREASE 
                                   else -magnitude if action == AdaptationAction.DECREASE 
                                   else 0.0,
                'q_values': {a.value: self._get_q_value(discrete_state, a) 
                           for a in AdaptationAction},
                'epsilon': self.epsilon,
                'state': discrete_state
            },
            confidence=1.0 - self.epsilon,  # Higher confidence when exploiting
            explanation=self._generate_explanation(state, action, discrete_state)
        )
        
        # Store for next update
        self.last_state = discrete_state
        self.last_action = action
        self._last_decision = decision
        
        elapsed = time.time() - start_time
        self.logger.debug(f"RL decision: {action.value} (ε={self.epsilon:.3f}, "
                         f"t={elapsed*1000:.2f}ms)")
        
        return decision
    
    def _generate_explanation(self, state: StateVector, action: AdaptationAction,
                            discrete_state: Tuple) -> str:
        """Generate human-readable explanation for decision."""
        performance = state.performance_metrics.get('accuracy', 0.5)
        mode = "exploring" if np.random.random() < self.epsilon else "exploiting"
        
        q_vals = {a: self._get_q_value(discrete_state, a) for a in AdaptationAction}
        best_action = max(q_vals, key=q_vals.get)
        
        explanation = f"RL ({mode}): performance={performance:.2f}, "
        explanation += f"Q-values: "
        explanation += f"INC={q_vals[AdaptationAction.INCREASE]:.2f}, "
        explanation += f"DEC={q_vals[AdaptationAction.DECREASE]:.2f}, "
        explanation += f"MNT={q_vals[AdaptationAction.MAINTAIN]:.2f}"
        
        if action != best_action:
            explanation += f" [exploring, best={best_action.value}]"
        
        return explanation
    
    async def update_from_feedback(self, feedback: Dict[str, Any]) -> bool:
        """
        Update learning from explicit feedback.
        
        Can be used to inject external rewards or corrections.
        """
        if 'reward' in feedback and self.last_state and self.last_action:
            reward = feedback['reward']
            current_q = self._get_q_value(self.last_state, self.last_action)
            new_q = current_q + self.alpha * reward
            self._set_q_value(self.last_state, self.last_action, new_q)
            
            self.logger.info(f"Updated from feedback: reward={reward}, "
                           f"Q: {current_q:.3f} -> {new_q:.3f}")
            return True
        return False
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current module state."""
        return {
            'module_id': self.module_id,
            'q_table_size': len(self.q_table),
            'epsilon': self.epsilon,
            'alpha': self.alpha,
            'gamma': self.gamma,
            'last_decision': {
                'action': self._last_decision.action.value if self._last_decision else None,
                'confidence': self._last_decision.confidence if self._last_decision else None
            } if self._last_decision else None
        }
    
    def _save_q_table(self):
        """Save Q-table to disk."""
        if not self.save_path:
            return
        
        # Convert Q-table to serializable format
        serializable = {}
        for state, actions in self.q_table.items():
            state_key = str(state)
            serializable[state_key] = {a.value: v for a, v in actions.items()}
        
        data = {
            'q_table': serializable,
            'epsilon': self.epsilon,
            'performance_history': self.performance_history
        }
        
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        with open(self.save_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved Q-table with {len(self.q_table)} states to {self.save_path}")
    
    def _load_q_table(self):
        """Load Q-table from disk."""
        if not self.save_path or not os.path.exists(self.save_path):
            return
        
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
            
            # Deserialize Q-table
            for state_key, actions in data.get('q_table', {}).items():
                state = eval(state_key)  # Convert string back to tuple
                self.q_table[state] = {
                    AdaptationAction(k): v for k, v in actions.items()
                }
            
            self.epsilon = data.get('epsilon', self.epsilon)
            self.performance_history = data.get('performance_history', [])
            
            self.logger.info(f"Loaded Q-table with {len(self.q_table)} states from {self.save_path}")
        except Exception as e:
            self.logger.warning(f"Could not load Q-table: {e}")
    
    def save_model(self):
        """Public method to save the learned model."""
        self._save_q_table()
    
    async def reset(self) -> None:
        """Reset the module state."""
        self.last_state = None
        self.last_action = None
        self.performance_history = []
    
    async def update(self, reward_signal: float) -> None:
        """Update RL model with external reward signal."""
        if self.last_state and self.last_action:
            # Direct reward injection
            current_q = self._get_q_value(self.last_state, self.last_action)
            new_q = current_q + self.alpha * reward_signal
            self._set_q_value(self.last_state, self.last_action, new_q)
            self.logger.debug(f"Updated Q from external reward: {reward_signal:.3f}")
    
    def explain(self) -> Dict[str, Any]:
        """
        Return explanation of the last decision.
        
        Returns Q-values, exploration status, and reasoning.
        """
        if not self._last_decision:
            return {'error': 'No decision made yet'}
        
        explanation = {
            'decision': self._last_decision.action.value,
            'confidence': self._last_decision.confidence,
            'epsilon': self.epsilon,
            'mode': 'exploring' if np.random.random() < self.epsilon else 'exploiting',
            'q_values': self._last_decision.parameters.get('q_values', {}),
            'state': self._last_decision.parameters.get('state'),
            'explanation_text': self._last_decision.explanation,
            'q_table_size': len(self.q_table)
        }
        return explanation
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return RL module metadata."""
        return {
            'name': 'Reinforcement Learning (Q-Learning)',
            'version': '1.0.0',
            'type': 'rl',
            'requires_training': True,
            'supports_explanation': True,
            'latency_estimate_ms': 0.5,
            'hyperparameters': {
                'learning_rate': self.alpha,
                'discount_factor': self.gamma,
                'exploration_rate': self.epsilon,
                'epsilon_min': self.epsilon_min
            }
        }
    
    async def save_checkpoint(self, path: str) -> bool:
        """Save Q-table and state to checkpoint file."""
        try:
            self.save_path = path
            self._save_q_table()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    async def load_checkpoint(self, path: str) -> bool:
        """Load Q-table and state from checkpoint file."""
        try:
            self.save_path = path
            self._load_q_table()
            return True
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return False
