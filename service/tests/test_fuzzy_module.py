"""
Tests for Fuzzy Logic Adaptation Module
"""

import pytest
import asyncio
from adaptrehab.modules.fuzzy_logic import FuzzyLogicModule
from adaptrehab.modules.base_module import StateVector, AdaptationAction


@pytest.fixture
def fuzzy_module():
    """Create fuzzy logic module for testing."""
    return FuzzyLogicModule("test_session_fuzzy")


@pytest.mark.asyncio
async def test_fuzzy_initialization(fuzzy_module):
    """Test module initializes correctly."""
    assert fuzzy_module.session_id == "test_session_fuzzy"
    assert fuzzy_module.step_size == 0.1
    assert len(fuzzy_module.performance_history) == 0


@pytest.mark.asyncio
async def test_fuzzy_low_performance():
    """Test fuzzy logic with low performance."""
    module = FuzzyLogicModule("test_low")
    
    # Low performance (20%)
    state = StateVector(
        performance_metrics={
            'accuracy': 0.2,
            'success_rate': 0.2,
            'error_rate': 0.8,
            'reaction_time': 1.5
        },
        task_state={'difficulty': 0.5},
        session_id="test_low"
    )
    
    decision = await module.compute_adaptation(state)
    
    # Should decrease difficulty for low performance
    assert decision.action == AdaptationAction.DECREASE
    assert decision.parameters['difficulty'] < 0.5
    assert decision.confidence > 0.5
    assert 'below target' in decision.explanation.lower()


@pytest.mark.asyncio
async def test_fuzzy_medium_performance():
    """Test fuzzy logic with medium performance."""
    module = FuzzyLogicModule("test_medium")
    
    # Medium performance (50%)
    state = StateVector(
        performance_metrics={
            'accuracy': 0.5,
            'success_rate': 0.5,
            'error_rate': 0.5,
            'reaction_time': 0.8
        },
        task_state={'difficulty': 0.5},
        session_id="test_medium"
    )
    
    decision = await module.compute_adaptation(state)
    
    # Should maintain difficulty for medium performance
    assert decision.action == AdaptationAction.MAINTAIN
    assert abs(decision.parameters['difficulty'] - 0.5) < 0.05
    assert 'on target' in decision.explanation.lower()


@pytest.mark.asyncio
async def test_fuzzy_high_performance():
    """Test fuzzy logic with high performance."""
    module = FuzzyLogicModule("test_high")
    
    # High performance (85%)
    state = StateVector(
        performance_metrics={
            'accuracy': 0.85,
            'success_rate': 0.85,
            'error_rate': 0.15,
            'reaction_time': 0.3
        },
        task_state={'difficulty': 0.5},
        session_id="test_high"
    )
    
    decision = await module.compute_adaptation(state)
    
    # Should increase difficulty for high performance
    assert decision.action == AdaptationAction.INCREASE
    assert decision.parameters['difficulty'] > 0.5
    assert decision.confidence > 0.5
    assert 'above target' in decision.explanation.lower()


@pytest.mark.asyncio
async def test_fuzzy_membership_functions():
    """Test membership function calculations."""
    module = FuzzyLogicModule("test_membership")
    
    # Test low performance membership
    assert module._trapezoid_membership(0.1, module.perf_low_params) > 0.8
    assert module._trapezoid_membership(0.8, module.perf_low_params) < 0.2
    
    # Test medium performance membership
    assert module._trapezoid_membership(0.5, module.perf_medium_params) > 0.8
    
    # Test high performance membership
    assert module._trapezoid_membership(0.8, module.perf_high_params) > 0.8
    assert module._trapezoid_membership(0.2, module.perf_high_params) < 0.2


@pytest.mark.asyncio
async def test_fuzzy_fuzzification():
    """Test fuzzification process."""
    module = FuzzyLogicModule("test_fuzz")
    
    # Test low performance
    fuzzy_low = module._fuzzify_performance(0.2)
    assert fuzzy_low['low'] > fuzzy_low['medium']
    assert fuzzy_low['low'] > fuzzy_low['high']
    
    # Test medium performance
    fuzzy_med = module._fuzzify_performance(0.5)
    assert fuzzy_med['medium'] >= fuzzy_med['low']
    assert fuzzy_med['medium'] >= fuzzy_med['high']
    
    # Test high performance
    fuzzy_high = module._fuzzify_performance(0.8)
    assert fuzzy_high['high'] > fuzzy_high['medium']
    assert fuzzy_high['high'] > fuzzy_high['low']


@pytest.mark.asyncio
async def test_fuzzy_smoothing():
    """Test performance smoothing over time."""
    module = FuzzyLogicModule("test_smooth", config={'smooth_factor': 0.5})
    
    # Submit multiple states
    for perf in [0.3, 0.4, 0.5, 0.6, 0.7]:
        state = StateVector(
            performance_metrics={'accuracy': perf, 'success_rate': perf},
            task_state={'difficulty': 0.5},
            session_id="test_smooth"
        )
        await module.compute_adaptation(state)
    
    # Check history is being maintained
    assert len(module.performance_history) <= module.max_history
    assert len(module.performance_history) > 0


@pytest.mark.asyncio
async def test_fuzzy_boundary_conditions():
    """Test fuzzy logic at difficulty boundaries."""
    module = FuzzyLogicModule("test_boundary")
    
    # Test at minimum difficulty
    state_low = StateVector(
        performance_metrics={'accuracy': 0.1, 'success_rate': 0.1},
        task_state={'difficulty': 0.0},
        session_id="test_boundary"
    )
    decision_low = await module.compute_adaptation(state_low)
    assert decision_low.parameters['difficulty'] >= 0.0
    
    # Test at maximum difficulty
    state_high = StateVector(
        performance_metrics={'accuracy': 0.9, 'success_rate': 0.9},
        task_state={'difficulty': 1.0},
        session_id="test_boundary"
    )
    decision_high = await module.compute_adaptation(state_high)
    assert decision_high.parameters['difficulty'] <= 1.0


@pytest.mark.asyncio
async def test_fuzzy_confidence_levels():
    """Test confidence calculation."""
    module = FuzzyLogicModule("test_conf")
    
    # Very clear low performance (high confidence)
    state_clear = StateVector(
        performance_metrics={'accuracy': 0.1, 'success_rate': 0.1},
        task_state={'difficulty': 0.5},
        session_id="test_conf"
    )
    decision_clear = await module.compute_adaptation(state_clear)
    
    # Ambiguous performance (lower confidence)
    state_ambig = StateVector(
        performance_metrics={'accuracy': 0.45, 'success_rate': 0.5},
        task_state={'difficulty': 0.5},
        session_id="test_conf"
    )
    decision_ambig = await module.compute_adaptation(state_ambig)
    
    # Clear decision should have higher confidence
    assert decision_clear.confidence > 0.7


@pytest.mark.asyncio
async def test_fuzzy_reset():
    """Test module reset."""
    module = FuzzyLogicModule("test_reset")
    
    # Add some history
    state = StateVector(
        performance_metrics={'accuracy': 0.5, 'success_rate': 0.5},
        task_state={'difficulty': 0.5},
        session_id="test_reset"
    )
    await module.compute_adaptation(state)
    
    assert len(module.performance_history) > 0
    
    # Reset
    module.reset()
    assert len(module.performance_history) == 0


@pytest.mark.asyncio
async def test_fuzzy_vs_rule_based():
    """Compare fuzzy logic to rule-based for same inputs."""
    from adaptrehab.modules.rule_based import RuleBasedModule
    
    fuzzy = FuzzyLogicModule("test_compare")
    rule = RuleBasedModule("test_compare")
    
    # Test with various performance levels
    for perf in [0.2, 0.5, 0.8]:
        state = StateVector(
            performance_metrics={'accuracy': perf, 'success_rate': perf},
            task_state={'difficulty': 0.5},
            session_id="test_compare"
        )
        
        fuzzy_decision = await fuzzy.compute_adaptation(state)
        rule_decision = await rule.compute_adaptation(state)
        
        # Both should make similar decisions at extremes
        if perf < 0.3 or perf > 0.7:
            assert fuzzy_decision.action == rule_decision.action


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
