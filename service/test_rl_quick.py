"""
Quick integration test for RL module - No async needed
"""

from adaptrehab.modules.reinforcement_learning import ReinforcementLearningModule
from adaptrehab.modules.base_module import StateVector
import asyncio


def test_rl_basic():
    """Test basic RL functionality."""
    # Create module
    config = {
        'learning_rate': 0.2,
        'exploration_rate': 0.2
    }
    rl = ReinforcementLearningModule("test_rl", config)
    
    # Initialize
    async def run_test():
        await rl.initialize({}, {})
        
        # Create state
        state = StateVector(
            performance_metrics={'accuracy': 0.65},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': 1},
            timestamp=0.0,
            session_id="test"
        )
        
        # Get adaptation
        decision = await rl.compute_adaptation(state)
        
        print(f"✓ RL module created and initialized")
        print(f"✓ Decision: {decision.action.value}")
        print(f"✓ Confidence: {decision.confidence:.2f}")
        print(f"✓ Q-table size: {len(rl.q_table)}")
        
        # Test metadata
        metadata = rl.get_metadata()
        print(f"✓ Module type: {metadata['type']}")
        print(f"✓ Requires training: {metadata['requires_training']}")
        
        # Test explanation
        explanation = rl.explain()
        print(f"✓ Explanation available: {len(explanation) > 0}")
        
        print("\n✅ All basic tests passed!")
        
        return True
    
    result = asyncio.run(run_test())
    assert result


if __name__ == '__main__':
    test_rl_basic()
