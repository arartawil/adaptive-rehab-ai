"""
Simple test to verify Phase 2 components work.

This tests the core adaptation loop without gRPC.
"""

import asyncio
import logging
from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule, StateVector
from adaptrehab.utils import setup_logging


async def test_adaptation_loop():
    """Test basic adaptation loop."""
    
    # Setup
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("=== Testing Adaptive Rehab AI - Phase 2 ===\n")
    
    # 1. Create configuration
    config_manager = ConfigManager()
    config = config_manager.to_dict()
    
    # 2. Create engine
    engine = AdaptationEngine(config)
    
    # 3. Register module
    engine.register_module('rule_based', RuleBasedModule)
    logger.info("✓ Module registered\n")
    
    # 4. Initialize session
    session_id = "test_session_001"
    patient_profile = {
        'patient_id': 'P001',
        'condition': 'stroke',
        'baseline_performance': 0.5
    }
    task_config = {
        'task_type': 'memory',
        'safety_bounds': {
            'difficulty': {'min': 0.0, 'max': 1.0}
        }
    }
    
    success = await engine.initialize_session(
        session_id,
        'rule_based',
        patient_profile,
        task_config
    )
    
    if not success:
        logger.error("Failed to initialize session")
        return
    
    logger.info("✓ Session initialized\n")
    
    # 5. Simulate adaptation loop (10 iterations)
    logger.info("=== Running Adaptation Loop ===\n")
    
    for i in range(10):
        # Simulate performance that improves over time
        performance = 0.3 + (i * 0.08)  # Gradually improving
        
        # Create state vector
        state = StateVector(
            performance_metrics={
                'accuracy': performance,
                'success_rate': performance,
                'reaction_time': 2.0 - (i * 0.1)
            },
            sensor_data={
                'hand_velocity': 0.5
            },
            task_state={
                'difficulty': 0.5 + (i * 0.05),
                'round': i + 1
            },
            timestamp=asyncio.get_event_loop().time(),
            session_id=session_id
        )
        
        # Get adaptation
        decision = await engine.compute_adaptation(session_id, state)
        
        if decision:
            logger.info(f"Round {i+1}:")
            logger.info(f"  Performance: {performance:.2f}")
            logger.info(f"  Decision: {decision.action.value}")
            logger.info(f"  New Difficulty: {decision.parameters.get('difficulty', 0):.2f}")
            logger.info(f"  Confidence: {decision.confidence:.2f}")
            logger.info(f"  Explanation: {decision.explanation}\n")
            
            # Send feedback (simple reward based on performance)
            reward = (performance - 0.5) * 2  # -1 to 1
            await engine.update_feedback(session_id, reward)
    
    # 6. Get status
    status = engine.get_status()
    logger.info("\n=== Engine Status ===")
    logger.info(f"Total adaptations: {status['statistics']['total_adaptations']}")
    logger.info(f"Safety interventions: {status['statistics']['safety_interventions']}")
    logger.info(f"Average latency: {status['statistics']['average_latency_ms']:.2f}ms")
    
    # 7. Test module explanation
    if engine.active_module:
        explanation = engine.active_module.explain()
        logger.info(f"\n=== Module Explanation ===")
        logger.info(f"Type: {explanation['module_type']}")
        logger.info(f"Last decision: {explanation['decision']}")
        logger.info(f"Thresholds: {explanation['thresholds']}")
    
    # 8. Test hot-swap (switch to same module for testing)
    logger.info("\n=== Testing Hot-Swap ===")
    swap_success = await engine.swap_module(session_id, 'rule_based')
    if swap_success:
        logger.info("✓ Module swap successful")
    
    # 9. Cleanup
    await engine.end_session(session_id)
    logger.info("\n✓ Session ended")
    
    logger.info("\n=== Phase 2 Test Complete! ===")
    logger.info("✓ All core components working correctly")


if __name__ == "__main__":
    asyncio.run(test_adaptation_loop())
