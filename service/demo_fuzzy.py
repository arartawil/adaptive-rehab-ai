"""
Simple demo to test Fuzzy Logic Module
"""

import asyncio
from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import FuzzyLogicModule, StateVector


async def main():
    print("🧠 Testing Fuzzy Logic Adaptation Module\n")
    print("="*60)
    
    # Initialize engine
    config = ConfigManager()
    engine = AdaptationEngine(config.to_dict())
    engine.register_module('fuzzy_logic', FuzzyLogicModule)
    
    # Start session
    success = await engine.initialize_session(
        session_id="fuzzy_test",
        module_type="fuzzy_logic",
        patient_profile={'patient_id': 'test_user'},
        task_config={'task_type': 'demo'}
    )
    
    if not success:
        print("❌ Failed to initialize session")
        return
        
    print("✅ Fuzzy Logic Module initialized\n")
    
    # Test with different performance levels
    test_cases = [
        (0.2, "Low Performance"),
        (0.5, "Medium Performance"),
        (0.8, "High Performance"),
        (0.3, "Below Average"),
        (0.7, "Above Average")
    ]
    
    difficulty = 0.5
    
    for performance, label in test_cases:
        print(f"\n📊 {label} (Accuracy: {performance*100:.0f}%)")
        print("-" * 60)
        
        # Create state
        state = StateVector(
            performance_metrics={
                'accuracy': performance,
                'success_rate': performance,
                'reaction_time': 1.0 - performance
            },
            sensor_data={},
            task_state={'difficulty': difficulty},
            timestamp=asyncio.get_event_loop().time(),
            session_id="fuzzy_test"
        )
        
        # Get adaptation
        decision = await engine.compute_adaptation("fuzzy_test", state)
        
        # Update difficulty
        difficulty = decision.parameters['difficulty']
        
        # Print results
        print(f"Action: {decision.action.value.upper()}")
        print(f"New Difficulty: {difficulty:.3f}")
        print(f"Confidence: {decision.confidence*100:.0f}%")
        print(f"Explanation: {decision.explanation}")
    
    print("\n" + "="*60)
    print("✅ Fuzzy Logic Module Test Complete!")
    
    print("\n✅ Fuzzy Logic Module implemented successfully!")


if __name__ == "__main__":
    asyncio.run(main())
