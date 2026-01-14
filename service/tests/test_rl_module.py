"""
Tests for Reinforcement Learning Adaptation Module
"""

import pytest
import asyncio
import numpy as np
from adaptrehab.modules.reinforcement_learning import ReinforcementLearningModule
from adaptrehab.modules.base_module import StateVector, AdaptationAction


@pytest.fixture
def rl_module():
    """Create RL module for testing."""
    config = {
        'learning_rate': 0.2,
        'discount_factor': 0.9,
        'exploration_rate': 0.3,
        'perf_bins': 5,
        'diff_bins': 3
    }
    return ReinforcementLearningModule("test_rl", config)


@pytest.fixture
def sample_state():
    """Create sample state."""
    return StateVector(
        performance_metrics={'accuracy': 0.65, 'speed': 1.0},
        sensor_data={'hand_velocity': 0.5},
        task_state={'difficulty': 0.5, 'round': 3},
        timestamp=0.0,
        session_id="test_session"
    )


@pytest.mark.asyncio
async def test_initialization(rl_module):
    """Test RL module initialization."""
    assert rl_module.module_id == "test_rl"
    assert rl_module.alpha == 0.2
    assert rl_module.gamma == 0.9
    assert rl_module.epsilon == 0.3
    assert len(rl_module.q_table) == 0
    
    # Initialize
    result = await rl_module.initialize({}, {})
    assert result is True
    assert rl_module.is_initialized


@pytest.mark.asyncio
async def test_state_discretization(rl_module, sample_state):
    """Test continuous to discrete state conversion."""
    discrete_state = rl_module._discretize_state(sample_state)
    
    assert isinstance(discrete_state, tuple)
    assert len(discrete_state) == 3  # (perf_bin, diff_bin, trend_bin)
    
    # Check bins are in valid range
    perf_bin, diff_bin, trend_bin = discrete_state
    assert 0 <= perf_bin < rl_module.perf_bins
    assert 0 <= diff_bin < rl_module.diff_bins
    assert 0 <= trend_bin < rl_module.trend_bins


@pytest.mark.asyncio
async def test_q_table_operations(rl_module):
    """Test Q-table get/set operations."""
    state = (2, 1, 1)
    action = AdaptationAction.INCREASE
    
    # Get default Q-value
    q_value = rl_module._get_q_value(state, action)
    assert q_value == 0.0
    
    # Set Q-value
    rl_module._set_q_value(state, action, 1.5)
    assert rl_module._get_q_value(state, action) == 1.5
    
    # Check all actions initialized
    assert len(rl_module.q_table[state]) == 3


@pytest.mark.asyncio
async def test_action_selection(rl_module):
    """Test epsilon-greedy action selection."""
    state = (2, 1, 1)
    
    # Set different Q-values
    rl_module._set_q_value(state, AdaptationAction.INCREASE, 2.0)
    rl_module._set_q_value(state, AdaptationAction.DECREASE, 0.5)
    rl_module._set_q_value(state, AdaptationAction.MAINTAIN, 1.0)
    
    # With low epsilon, should mostly exploit (choose INCREASE)
    rl_module.epsilon = 0.1
    actions = [rl_module._select_action(state) for _ in range(100)]
    increase_count = sum(1 for a in actions if a == AdaptationAction.INCREASE)
    assert increase_count >= 70  # At least 70% should be best action
    
    # With high epsilon, should explore more
    rl_module.epsilon = 0.9
    actions = [rl_module._select_action(state) for _ in range(100)]
    increase_count = sum(1 for a in actions if a == AdaptationAction.INCREASE)
    assert increase_count < 50  # Less than 50% should be best action


@pytest.mark.asyncio
async def test_reward_calculation(rl_module, sample_state):
    """Test reward function."""
    # Test performance improvement reward
    rl_module.performance_history = [0.5]
    sample_state.performance_metrics['accuracy'] = 0.7
    
    reward = rl_module._calculate_reward(sample_state, AdaptationAction.MAINTAIN)
    assert reward > 0  # Should get positive reward for improvement
    
    # Test flow state bonus
    sample_state.performance_metrics['accuracy'] = 0.6
    reward = rl_module._calculate_reward(sample_state, AdaptationAction.MAINTAIN)
    assert reward > 0  # In flow state


@pytest.mark.asyncio
async def test_q_learning_update(rl_module):
    """Test Q-value update rule."""
    state = (2, 1, 1)
    next_state = (2, 1, 2)
    action = AdaptationAction.INCREASE
    reward = 1.0
    
    # Set initial Q-values
    rl_module._set_q_value(state, action, 0.5)
    rl_module._set_q_value(next_state, AdaptationAction.INCREASE, 2.0)
    
    # Update
    old_q = rl_module._get_q_value(state, action)
    rl_module._update_q_value(state, action, reward, next_state)
    new_q = rl_module._get_q_value(state, action)
    
    # Q-value should increase (positive reward + high next state value)
    assert new_q > old_q


@pytest.mark.asyncio
async def test_compute_adaptation(rl_module, sample_state):
    """Test full adaptation computation."""
    await rl_module.initialize({}, {})
    
    decision = await rl_module.compute_adaptation(sample_state)
    
    # Check decision structure
    assert decision.action in AdaptationAction
    assert 0.0 <= decision.magnitude <= 1.0
    assert 0.0 <= decision.confidence <= 1.0
    assert 'difficulty_change' in decision.parameters
    assert 'q_values' in decision.parameters
    assert 'epsilon' in decision.parameters
    assert isinstance(decision.explanation, str)


@pytest.mark.asyncio
async def test_learning_over_time(rl_module):
    """Test that Q-values improve with experience."""
    await rl_module.initialize({}, {})
    
    # Simulate consistent scenario: low performance -> decrease works
    initial_q_tables = {}
    
    for i in range(50):
        # Low performance state
        state = StateVector(
            performance_metrics={'accuracy': 0.3},
            sensor_data={},
            task_state={'difficulty': 0.7, 'round': i},
            timestamp=float(i),
            session_id="test"
        )
        
        decision = await rl_module.compute_adaptation(state)
        
        # Record Q-values at start
        if i == 0:
            discrete = rl_module._discretize_state(state)
            initial_q_tables[discrete] = {
                a: rl_module._get_q_value(discrete, a) 
                for a in AdaptationAction
            }
    
    # After learning, Q-value for DECREASE should be highest for low performance
    low_perf_state = rl_module._discretize_state(state)
    final_q_decrease = rl_module._get_q_value(low_perf_state, AdaptationAction.DECREASE)
    final_q_increase = rl_module._get_q_value(low_perf_state, AdaptationAction.INCREASE)
    
    # DECREASE should be preferred over INCREASE for low performance
    assert final_q_decrease >= final_q_increase


@pytest.mark.asyncio
async def test_exploration_decay(rl_module):
    """Test that epsilon decays over time."""
    await rl_module.initialize({}, {})
    
    initial_epsilon = rl_module.epsilon
    
    # Run many iterations
    for i in range(100):
        state = StateVector(
            performance_metrics={'accuracy': 0.5},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': i},
            timestamp=float(i),
            session_id="test"
        )
        await rl_module.compute_adaptation(state)
    
    # Epsilon should have decayed
    assert rl_module.epsilon < initial_epsilon
    assert rl_module.epsilon >= rl_module.epsilon_min


@pytest.mark.asyncio
async def test_feedback_update(rl_module, sample_state):
    """Test explicit feedback updates."""
    await rl_module.initialize({}, {})
    
    # Make a decision to set last_state and last_action
    await rl_module.compute_adaptation(sample_state)
    
    old_q = rl_module._get_q_value(rl_module.last_state, rl_module.last_action)
    
    # Provide positive feedback
    result = await rl_module.update_from_feedback({'reward': 0.5})
    assert result is True
    
    new_q = rl_module._get_q_value(rl_module.last_state, rl_module.last_action)
    assert new_q > old_q


@pytest.mark.asyncio
async def test_get_state(rl_module, sample_state):
    """Test state retrieval."""
    await rl_module.initialize({}, {})
    await rl_module.compute_adaptation(sample_state)
    
    state = await rl_module.get_state()
    
    assert state['module_id'] == "test_rl"
    assert 'q_table_size' in state
    assert 'epsilon' in state
    assert 'alpha' in state
    assert 'gamma' in state
    assert state['last_decision'] is not None


@pytest.mark.asyncio
async def test_reset(rl_module, sample_state):
    """Test module reset."""
    await rl_module.initialize({}, {})
    
    # Make some decisions
    await rl_module.compute_adaptation(sample_state)
    assert len(rl_module.performance_history) > 0
    
    # Reset
    result = await rl_module.reset()
    assert result is True
    assert len(rl_module.performance_history) == 0
    assert rl_module.last_state is None
    assert rl_module.last_action is None


@pytest.mark.asyncio
async def test_different_scenarios(rl_module):
    """Test RL adapts to different performance scenarios."""
    await rl_module.initialize({}, {})
    
    scenarios = [
        (0.2, "low"),    # Low performance
        (0.5, "medium"), # Medium performance
        (0.8, "high")    # High performance
    ]
    
    for perf, label in scenarios:
        state = StateVector(
            performance_metrics={'accuracy': perf},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': 0},
            timestamp=0.0,
            session_id="test"
        )
        
        decision = await rl_module.compute_adaptation(state)
        
        # Check that decision is valid
        assert decision.action in AdaptationAction
        assert isinstance(decision.explanation, str)
        assert label.lower() in decision.explanation.lower() or 'performance' in decision.explanation.lower()


def test_trend_calculation(rl_module):
    """Test performance trend calculation."""
    # Test improving trend
    rl_module.performance_history = [0.4, 0.5, 0.6]
    trend = rl_module._calculate_trend_bin()
    assert trend == 2  # Improving
    
    # Test declining trend
    rl_module.performance_history = [0.6, 0.5, 0.4]
    trend = rl_module._calculate_trend_bin()
    assert trend == 0  # Declining
    
    # Test stable trend
    rl_module.performance_history = [0.5, 0.51, 0.5]
    trend = rl_module._calculate_trend_bin()
    assert trend == 1  # Stable


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
