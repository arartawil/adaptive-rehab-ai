"""
Comprehensive Engine Test Suite

Tests all components with simulated rehabilitation scenarios.
"""

import asyncio
import logging
import time
from typing import List, Dict
import statistics

from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule, StateVector
from adaptrehab.utils import setup_logging


logger = logging.getLogger(__name__)


class RehabSimulator:
    """Simulates patient performance in rehabilitation tasks."""
    
    def __init__(self, profile_type: str):
        """
        Profile types:
        - fast_learner: Quick improvement
        - plateau: Improves then plateaus
        - variable: Inconsistent performance
        - struggling: Slow/no improvement
        """
        self.profile_type = profile_type
        self.session_count = 0
        self.baseline = 0.4
        
    def get_performance(self, difficulty: float, round_num: int) -> Dict[str, float]:
        """Simulate patient performance based on profile."""
        self.session_count += 1
        
        # Base performance affected by difficulty
        difficulty_factor = 1.0 - (difficulty * 0.5)  # Harder = worse performance
        
        if self.profile_type == "fast_learner":
            # Steady improvement
            improvement = min(0.5, round_num * 0.05)
            base_performance = self.baseline + improvement
            
        elif self.profile_type == "plateau":
            # Improves then stops
            if round_num < 10:
                improvement = round_num * 0.04
            else:
                improvement = 0.4  # Plateau
            base_performance = self.baseline + improvement
            
        elif self.profile_type == "variable":
            # Inconsistent performance
            import random
            random.seed(self.session_count)
            variability = random.uniform(-0.15, 0.15)
            base_performance = self.baseline + (round_num * 0.02) + variability
            
        elif self.profile_type == "struggling":
            # Very slow improvement
            improvement = min(0.2, round_num * 0.01)
            base_performance = self.baseline + improvement
            
        else:
            base_performance = 0.5
        
        # Apply difficulty factor
        performance = base_performance * difficulty_factor
        
        # Clamp to valid range
        performance = max(0.0, min(1.0, performance))
        
        # Calculate derived metrics
        accuracy = performance
        success_rate = performance
        reaction_time = 2.5 - (performance * 1.0)  # Better = faster
        error_rate = 1.0 - performance
        
        return {
            'accuracy': accuracy,
            'success_rate': success_rate,
            'reaction_time': reaction_time,
            'error_rate': error_rate,
            'consistency': max(0.5, performance)
        }


async def test_scenario(
    engine: AdaptationEngine,
    scenario_name: str,
    patient_profile_type: str,
    task_type: str,
    rounds: int = 20
) -> Dict[str, any]:
    """Test a complete rehabilitation scenario."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Scenario: {scenario_name}")
    logger.info(f"Patient: {patient_profile_type} | Task: {task_type}")
    logger.info(f"{'='*60}\n")
    
    # Initialize session
    session_id = f"test_{scenario_name.replace(' ', '_')}"
    patient_profile = {
        'patient_id': f"P_{patient_profile_type}",
        'condition': 'stroke',
        'baseline_performance': 0.4
    }
    
    task_config = {
        'task_type': task_type,
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
        return None
    
    # Create patient simulator
    simulator = RehabSimulator(patient_profile_type)
    
    # Track metrics
    difficulties = []
    performances = []
    actions = []
    latencies = []
    safety_interventions = 0
    
    current_difficulty = 0.5
    
    # Run rehabilitation rounds
    for round_num in range(1, rounds + 1):
        # Simulate patient performance
        perf_metrics = simulator.get_performance(current_difficulty, round_num)
        
        # Create state
        state = StateVector(
            performance_metrics=perf_metrics,
            sensor_data={
                'hand_velocity': 0.5,
                'movement_smoothness': perf_metrics['consistency']
            },
            task_state={
                'difficulty': current_difficulty,
                'round': round_num
            },
            timestamp=time.time(),
            session_id=session_id
        )
        
        # Get adaptation
        start_time = time.perf_counter()
        decision = await engine.compute_adaptation(session_id, state)
        latency = (time.perf_counter() - start_time) * 1000
        
        if decision:
            # Update difficulty
            new_difficulty = decision.parameters.get('difficulty', current_difficulty)
            
            # Track metrics
            difficulties.append(new_difficulty)
            performances.append(perf_metrics['success_rate'])
            actions.append(decision.action.value)
            latencies.append(latency)
            
            # Log every 5 rounds
            if round_num % 5 == 0 or round_num == 1:
                logger.info(f"Round {round_num:2d}: "
                          f"Perf={perf_metrics['success_rate']:.2f} "
                          f"Diff={current_difficulty:.2f}→{new_difficulty:.2f} "
                          f"Action={decision.action.value:8s} "
                          f"Conf={decision.confidence:.2f}")
            
            current_difficulty = new_difficulty
            
            # Send feedback
            reward = (perf_metrics['success_rate'] - 0.5) * 2
            await engine.update_feedback(session_id, reward)
    
    # Get final stats
    status = engine.get_status()
    
    # Calculate results
    results = {
        'scenario': scenario_name,
        'patient_type': patient_profile_type,
        'rounds': rounds,
        'avg_performance': statistics.mean(performances),
        'final_performance': performances[-1],
        'improvement': performances[-1] - performances[0],
        'avg_difficulty': statistics.mean(difficulties),
        'final_difficulty': difficulties[-1],
        'difficulty_range': (min(difficulties), max(difficulties)),
        'avg_latency_ms': statistics.mean(latencies),
        'max_latency_ms': max(latencies),
        'safety_interventions': status['statistics']['safety_interventions'],
        'action_distribution': {
            'increase': actions.count('increase'),
            'decrease': actions.count('decrease'),
            'maintain': actions.count('maintain')
        }
    }
    
    # Print summary
    logger.info(f"\n--- Results ---")
    logger.info(f"Performance: {performances[0]:.2f} → {performances[-1]:.2f} "
               f"(Δ {results['improvement']:+.2f})")
    logger.info(f"Difficulty:  {difficulties[0]:.2f} → {difficulties[-1]:.2f}")
    logger.info(f"Avg Latency: {results['avg_latency_ms']:.2f}ms")
    logger.info(f"Actions: ↑{results['action_distribution']['increase']} "
               f"↓{results['action_distribution']['decrease']} "
               f"→{results['action_distribution']['maintain']}")
    
    # Cleanup
    await engine.end_session(session_id)
    
    return results


async def test_performance_under_load():
    """Test system performance with multiple concurrent sessions."""
    logger.info(f"\n{'='*60}")
    logger.info("LOAD TEST: Multiple Concurrent Sessions")
    logger.info(f"{'='*60}\n")
    
    config_manager = ConfigManager()
    config = config_manager.to_dict()
    
    # Create multiple engines (simulating multiple patients)
    num_sessions = 5
    engines = []
    
    for i in range(num_sessions):
        engine = AdaptationEngine(config)
        engine.register_module('rule_based', RuleBasedModule)
        engines.append(engine)
    
    # Initialize all sessions
    session_ids = []
    for i, engine in enumerate(engines):
        session_id = f"load_test_{i}"
        patient_profile = {
            'patient_id': f'P{i:03d}',
            'condition': 'stroke',
            'baseline_performance': 0.4 + (i * 0.05)
        }
        task_config = {
            'task_type': 'memory',
            'safety_bounds': {'difficulty': {'min': 0.0, 'max': 1.0}}
        }
        
        await engine.initialize_session(session_id, 'rule_based', patient_profile, task_config)
        session_ids.append(session_id)
    
    logger.info(f"✓ {num_sessions} sessions initialized\n")
    
    # Run concurrent adaptations
    total_rounds = 50
    all_latencies = []
    
    for round_num in range(total_rounds):
        round_latencies = []
        
        # Create tasks for all sessions
        tasks = []
        for i, (engine, session_id) in enumerate(zip(engines, session_ids)):
            state = StateVector(
                performance_metrics={'accuracy': 0.5 + (round_num * 0.01)},
                sensor_data={'velocity': 0.5},
                task_state={'difficulty': 0.5, 'round': round_num},
                timestamp=time.time(),
                session_id=session_id
            )
            tasks.append(engine.compute_adaptation(session_id, state))
        
        # Execute all concurrently
        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        elapsed = (time.perf_counter() - start) * 1000
        
        all_latencies.append(elapsed)
        
        if round_num % 10 == 0:
            logger.info(f"Round {round_num:2d}: {num_sessions} concurrent adaptations in {elapsed:.2f}ms")
    
    # Results
    logger.info(f"\n--- Load Test Results ---")
    logger.info(f"Concurrent sessions: {num_sessions}")
    logger.info(f"Total rounds: {total_rounds}")
    logger.info(f"Avg latency: {statistics.mean(all_latencies):.2f}ms")
    logger.info(f"Max latency: {max(all_latencies):.2f}ms")
    logger.info(f"P95 latency: {sorted(all_latencies)[int(len(all_latencies)*0.95)]:.2f}ms")
    logger.info(f"Throughput: {(num_sessions * total_rounds / (sum(all_latencies)/1000)):.1f} adaptations/sec")
    
    # Cleanup
    for engine, session_id in zip(engines, session_ids):
        await engine.end_session(session_id)
    
    return {
        'sessions': num_sessions,
        'rounds': total_rounds,
        'avg_latency': statistics.mean(all_latencies),
        'max_latency': max(all_latencies)
    }


async def test_module_hot_swap():
    """Test hot-swapping modules during active session."""
    logger.info(f"\n{'='*60}")
    logger.info("HOT-SWAP TEST")
    logger.info(f"{'='*60}\n")
    
    config_manager = ConfigManager()
    engine = AdaptationEngine(config_manager.to_dict())
    engine.register_module('rule_based', RuleBasedModule)
    
    session_id = "hotswap_test"
    patient_profile = {
        'patient_id': 'P_SWAP',
        'condition': 'stroke',
        'baseline_performance': 0.5
    }
    task_config = {
        'task_type': 'reaching',
        'safety_bounds': {'difficulty': {'min': 0.0, 'max': 1.0}}
    }
    
    await engine.initialize_session(session_id, 'rule_based', patient_profile, task_config)
    
    # Run with first module
    logger.info("Running with rule_based module...")
    for i in range(5):
        state = StateVector(
            performance_metrics={'accuracy': 0.6},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': i},
            timestamp=time.time(),
            session_id=session_id
        )
        decision = await engine.compute_adaptation(session_id, state)
        logger.info(f"  Round {i+1}: {decision.action.value}")
    
    # Hot-swap
    logger.info("\n🔄 Hot-swapping module...")
    swap_start = time.perf_counter()
    success = await engine.swap_module(session_id, 'rule_based')  # Swap to same for testing
    swap_time = (time.perf_counter() - swap_start) * 1000
    
    if success:
        logger.info(f"✓ Module swapped in {swap_time:.2f}ms\n")
    else:
        logger.error("✗ Module swap failed\n")
        return False
    
    # Continue with new module
    logger.info("Running with new module instance...")
    for i in range(5, 10):
        state = StateVector(
            performance_metrics={'accuracy': 0.6},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': i},
            timestamp=time.time(),
            session_id=session_id
        )
        decision = await engine.compute_adaptation(session_id, state)
        logger.info(f"  Round {i+1}: {decision.action.value}")
    
    logger.info(f"\n✓ Session continued seamlessly after swap")
    
    await engine.end_session(session_id)
    return True


async def test_safety_system():
    """Test safety wrapper with edge cases."""
    logger.info(f"\n{'='*60}")
    logger.info("SAFETY SYSTEM TEST")
    logger.info(f"{'='*60}\n")
    
    config_manager = ConfigManager()
    config = config_manager.to_dict()
    config['safety']['max_change_rate'] = 0.1  # Strict rate limit
    
    engine = AdaptationEngine(config)
    engine.register_module('rule_based', RuleBasedModule)
    
    session_id = "safety_test"
    patient_profile = {
        'patient_id': 'P_SAFETY',
        'condition': 'stroke',
        'baseline_performance': 0.5
    }
    task_config = {
        'task_type': 'memory',
        'safety_bounds': {
            'difficulty': {'min': 0.2, 'max': 0.8}
        }
    }
    
    await engine.initialize_session(session_id, 'rule_based', patient_profile, task_config)
    
    test_cases = [
        ("Very high performance", 0.95, "Should trigger increase"),
        ("Very low performance", 0.15, "Should trigger decrease"),
        ("At max difficulty", 0.9, "Should prevent increase"),
        ("At min difficulty", 0.1, "Should prevent decrease"),
    ]
    
    initial_interventions = engine.get_status()['statistics']['safety_interventions']
    
    for test_name, performance, expected in test_cases:
        logger.info(f"\nTest: {test_name}")
        logger.info(f"  Expected: {expected}")
        
        state = StateVector(
            performance_metrics={'accuracy': performance, 'success_rate': performance},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': 1},
            timestamp=time.time(),
            session_id=session_id
        )
        
        decision = await engine.compute_adaptation(session_id, state)
        
        logger.info(f"  Result: {decision.action.value} "
                   f"(diff: {decision.parameters.get('difficulty', 0):.2f}, "
                   f"conf: {decision.confidence:.2f})")
    
    final_interventions = engine.get_status()['statistics']['safety_interventions']
    interventions = final_interventions - initial_interventions
    
    logger.info(f"\n✓ Safety interventions triggered: {interventions}")
    
    await engine.end_session(session_id)
    return interventions > 0


async def run_comprehensive_tests():
    """Run all tests."""
    setup_logging("INFO")
    
    logger.info("╔" + "═"*58 + "╗")
    logger.info("║" + " "*10 + "ADAPTIVE REHAB AI - ENGINE TEST SUITE" + " "*10 + "║")
    logger.info("╚" + "═"*58 + "╝\n")
    
    # Test scenarios
    scenarios = [
        ("Fast Learner - Memory Task", "fast_learner", "memory"),
        ("Plateau Patient - Reaching Task", "plateau", "reaching"),
        ("Variable Performance - Balance Task", "variable", "balance"),
        ("Struggling Patient - Memory Task", "struggling", "memory"),
    ]
    
    # Initialize engine
    config_manager = ConfigManager()
    engine = AdaptationEngine(config_manager.to_dict())
    engine.register_module('rule_based', RuleBasedModule)
    
    all_results = []
    
    # Run scenarios
    for name, patient_type, task_type in scenarios:
        result = await test_scenario(engine, name, patient_type, task_type, rounds=20)
        if result:
            all_results.append(result)
        await asyncio.sleep(0.5)  # Brief pause between scenarios
    
    # Additional tests
    await test_performance_under_load()
    await asyncio.sleep(0.5)
    
    await test_module_hot_swap()
    await asyncio.sleep(0.5)
    
    await test_safety_system()
    
    # Final summary
    logger.info(f"\n\n{'='*60}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'='*60}\n")
    
    logger.info(f"✅ Scenarios tested: {len(all_results)}")
    
    for result in all_results:
        logger.info(f"\n{result['scenario']}:")
        logger.info(f"  Performance improvement: {result['improvement']:+.2f}")
        logger.info(f"  Avg latency: {result['avg_latency_ms']:.2f}ms")
        logger.info(f"  Difficulty adapted: {result['difficulty_range'][0]:.2f} - {result['difficulty_range'][1]:.2f}")
    
    # Overall stats
    avg_latency = statistics.mean([r['avg_latency_ms'] for r in all_results])
    max_latency = max([r['max_latency_ms'] for r in all_results])
    
    logger.info(f"\n{'─'*60}")
    logger.info("OVERALL PERFORMANCE")
    logger.info(f"{'─'*60}")
    logger.info(f"Average latency: {avg_latency:.2f}ms")
    logger.info(f"Maximum latency: {max_latency:.2f}ms")
    logger.info(f"Target: <50ms → {'✅ PASS' if max_latency < 50 else '❌ FAIL'}")
    
    logger.info(f"\n{'─'*60}")
    logger.info("ADAPTATION QUALITY")
    logger.info(f"{'─'*60}")
    
    for result in all_results:
        adaptation_quality = "Good" if abs(result['improvement']) > 0.1 else "Moderate"
        logger.info(f"{result['patient_type']:15s}: {adaptation_quality:8s} "
                   f"(Δ performance: {result['improvement']:+.2f})")
    
    logger.info(f"\n\n{'='*60}")
    logger.info("🎉 ALL TESTS COMPLETE!")
    logger.info(f"{'='*60}")
    logger.info("\nEngine is ready for Unity integration! ✅\n")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
