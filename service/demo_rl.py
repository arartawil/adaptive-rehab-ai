"""
Reinforcement Learning Module Demo

Demonstrates Q-learning adaptation in action:
1. Low performance → learns to decrease difficulty
2. High performance → learns to increase difficulty
3. Medium performance → learns to maintain
4. Shows Q-table evolution and learning progress
"""

import asyncio
import time
import numpy as np
from adaptrehab.modules.reinforcement_learning import ReinforcementLearningModule
from adaptrehab.modules.base_module import StateVector, AdaptationAction


def print_separator():
    print("=" * 80)


def print_header(text):
    print_separator()
    print(f"  {text}")
    print_separator()


def print_q_table(rl_module, state):
    """Print Q-values for a state."""
    q_vals = {
        a: rl_module._get_q_value(state, a)
        for a in AdaptationAction
    }
    
    print(f"  Q-values for state {state}:")
    print(f"    INCREASE:  {q_vals[AdaptationAction.INCREASE]:+.3f}")
    print(f"    MAINTAIN:  {q_vals[AdaptationAction.MAINTAIN]:+.3f}")
    print(f"    DECREASE:  {q_vals[AdaptationAction.DECREASE]:+.3f}")
    
    best = max(q_vals, key=q_vals.get)
    print(f"    Best action: {best.value}")


async def scenario_low_performance(rl_module):
    """Scenario: Patient struggling, low performance."""
    print_header("SCENARIO 1: Low Performance (Patient Struggling)")
    print("Patient consistently scores 20-30% accuracy")
    print("Expected: RL should learn to DECREASE difficulty\n")
    
    performances = [0.25, 0.22, 0.28, 0.20, 0.26]
    difficulty = 0.7
    
    for round_num, perf in enumerate(performances, 1):
        state = StateVector(
            performance_metrics={'accuracy': perf},
            sensor_data={},
            task_state={'difficulty': difficulty, 'round': round_num},
            timestamp=time.time(),
            session_id="low_perf_demo"
        )
        
        decision = await rl_module.compute_adaptation(state)
        
        # Apply decision
        if decision.action == AdaptationAction.DECREASE:
            difficulty = max(0.0, difficulty - 0.1)
        elif decision.action == AdaptationAction.INCREASE:
            difficulty = min(1.0, difficulty + 0.1)
        
        print(f"Round {round_num}:")
        print(f"  Performance: {perf:.2f} | Difficulty: {difficulty:.2f}")
        print(f"  Action: {decision.action.value} (confidence: {decision.confidence:.2f})")
        print(f"  Exploration: ε={decision.parameters['epsilon']:.3f}")
        print()
    
    # Show learned Q-values
    print("\nLearned Q-values after low performance episodes:")
    discrete_state = rl_module._discretize_state(state)
    print_q_table(rl_module, discrete_state)
    print()


async def scenario_high_performance(rl_module):
    """Scenario: Patient excelling, high performance."""
    print_header("SCENARIO 2: High Performance (Patient Excelling)")
    print("Patient consistently scores 80-90% accuracy")
    print("Expected: RL should learn to INCREASE difficulty\n")
    
    performances = [0.85, 0.88, 0.82, 0.87, 0.90]
    difficulty = 0.3
    
    for round_num, perf in enumerate(performances, 1):
        state = StateVector(
            performance_metrics={'accuracy': perf},
            sensor_data={},
            task_state={'difficulty': difficulty, 'round': round_num},
            timestamp=time.time(),
            session_id="high_perf_demo"
        )
        
        decision = await rl_module.compute_adaptation(state)
        
        # Apply decision
        if decision.action == AdaptationAction.DECREASE:
            difficulty = max(0.0, difficulty - 0.1)
        elif decision.action == AdaptationAction.INCREASE:
            difficulty = min(1.0, difficulty + 0.1)
        
        print(f"Round {round_num}:")
        print(f"  Performance: {perf:.2f} | Difficulty: {difficulty:.2f}")
        print(f"  Action: {decision.action.value} (confidence: {decision.confidence:.2f})")
        print(f"  Exploration: ε={decision.parameters['epsilon']:.3f}")
        print()
    
    # Show learned Q-values
    print("\nLearned Q-values after high performance episodes:")
    discrete_state = rl_module._discretize_state(state)
    print_q_table(rl_module, discrete_state)
    print()


async def scenario_optimal_flow(rl_module):
    """Scenario: Patient in flow state, optimal challenge."""
    print_header("SCENARIO 3: Flow State (Optimal Challenge)")
    print("Patient consistently scores 60-70% accuracy (flow state)")
    print("Expected: RL should learn to MAINTAIN difficulty\n")
    
    performances = [0.65, 0.62, 0.68, 0.64, 0.66]
    difficulty = 0.5
    
    for round_num, perf in enumerate(performances, 1):
        state = StateVector(
            performance_metrics={'accuracy': perf},
            sensor_data={},
            task_state={'difficulty': difficulty, 'round': round_num},
            timestamp=time.time(),
            session_id="flow_demo"
        )
        
        decision = await rl_module.compute_adaptation(state)
        
        # Apply decision
        if decision.action == AdaptationAction.DECREASE:
            difficulty = max(0.0, difficulty - 0.1)
        elif decision.action == AdaptationAction.INCREASE:
            difficulty = min(1.0, difficulty + 0.1)
        
        print(f"Round {round_num}:")
        print(f"  Performance: {perf:.2f} | Difficulty: {difficulty:.2f}")
        print(f"  Action: {decision.action.value} (confidence: {decision.confidence:.2f})")
        print(f"  Flow state bonus: Active ✓")
        print()
    
    # Show learned Q-values
    print("\nLearned Q-values after flow state episodes:")
    discrete_state = rl_module._discretize_state(state)
    print_q_table(rl_module, discrete_state)
    print()


async def scenario_learning_progression(rl_module):
    """Show Q-table evolution over many episodes."""
    print_header("SCENARIO 4: Learning Progression")
    print("Training on 50 episodes with varying performance")
    print("Watch Q-values converge and exploration decay\n")
    
    np.random.seed(42)
    
    # Record metrics
    epsilons = []
    q_table_sizes = []
    actions_taken = {action: 0 for action in AdaptationAction}
    
    for episode in range(50):
        # Simulate realistic performance variation
        base_perf = 0.5 + 0.2 * np.sin(episode / 5)  # Oscillating performance
        noise = np.random.normal(0, 0.1)
        perf = np.clip(base_perf + noise, 0.0, 1.0)
        
        state = StateVector(
            performance_metrics={'accuracy': perf},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': episode},
            timestamp=time.time(),
            session_id="progression_demo"
        )
        
        decision = await rl_module.compute_adaptation(state)
        
        # Track metrics
        epsilons.append(decision.parameters['epsilon'])
        q_table_sizes.append(len(rl_module.q_table))
        actions_taken[decision.action] += 1
        
        # Print every 10 episodes
        if (episode + 1) % 10 == 0:
            print(f"Episode {episode + 1}/50:")
            print(f"  Exploration rate: ε={decision.parameters['epsilon']:.3f}")
            print(f"  Q-table size: {len(rl_module.q_table)} states")
            print(f"  Actions: INC={actions_taken[AdaptationAction.INCREASE]}, "
                  f"DEC={actions_taken[AdaptationAction.DECREASE]}, "
                  f"MNT={actions_taken[AdaptationAction.MAINTAIN]}")
            print()
    
    print("\nFinal learning statistics:")
    print(f"  Initial ε: {epsilons[0]:.3f} → Final ε: {epsilons[-1]:.3f}")
    print(f"  Q-table states explored: {q_table_sizes[-1]}")
    print(f"  Total actions taken:")
    for action, count in actions_taken.items():
        pct = (count / 50) * 100
        print(f"    {action.value}: {count} ({pct:.1f}%)")
    print()


async def scenario_performance_comparison():
    """Compare RL to other methods."""
    print_header("SCENARIO 5: Multi-Module Comparison")
    print("Comparing RL to Rule-based and Fuzzy Logic\n")
    
    # Create modules
    from adaptrehab.modules.fuzzy_logic import FuzzyLogicModule
    
    rl_mod = ReinforcementLearningModule("rl_comp", {
        'exploration_rate': 0.1  # Low exploration for fair comparison
    })
    fuzzy_mod = FuzzyLogicModule("fuzzy_comp")
    
    await rl_mod.initialize({}, {})
    await fuzzy_mod.initialize({}, {})
    
    # Test on various performance levels
    test_cases = [
        (0.3, "Low"),
        (0.5, "Medium-Low"),
        (0.65, "Flow"),
        (0.8, "High")
    ]
    
    print(f"{'Performance':<15} {'RL Action':<15} {'Fuzzy Action':<15}")
    print("-" * 45)
    
    for perf, label in test_cases:
        state = StateVector(
            performance_metrics={'accuracy': perf},
            sensor_data={},
            task_state={'difficulty': 0.5, 'round': 0},
            timestamp=time.time(),
            session_id="comparison"
        )
        
        rl_decision = await rl_mod.compute_adaptation(state)
        fuzzy_decision = await fuzzy_mod.compute_adaptation(state)
        
        print(f"{label} ({perf:.2f})   {rl_decision.action.value:<15} "
              f"{fuzzy_decision.action.value:<15}")
    
    print()


async def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "REINFORCEMENT LEARNING MODULE DEMO" + " " * 24 + "║")
    print("║" + " " * 78 + "║")
    print("║" + " " * 15 + "Q-Learning Adaptation for Rehabilitation" + " " * 22 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Create RL module
    config = {
        'learning_rate': 0.2,      # α: How much to update Q-values
        'discount_factor': 0.9,    # γ: Weight future rewards
        'exploration_rate': 0.3,   # ε: Initial exploration
        'epsilon_decay': 0.98,     # Decay rate
        'epsilon_min': 0.01,       # Minimum exploration
        'perf_bins': 10,           # State discretization
        'diff_bins': 5
    }
    
    rl_module = ReinforcementLearningModule("demo_rl", config)
    await rl_module.initialize({}, {})
    
    print("Configuration:")
    print(f"  Learning rate (α): {config['learning_rate']}")
    print(f"  Discount factor (γ): {config['discount_factor']}")
    print(f"  Exploration rate (ε): {config['exploration_rate']}")
    print(f"  State space: {config['perf_bins']} × {config['diff_bins']} × 3 = "
          f"{config['perf_bins'] * config['diff_bins'] * 3} states")
    print()
    
    # Run scenarios
    await scenario_low_performance(rl_module)
    await asyncio.sleep(0.5)
    
    await scenario_high_performance(rl_module)
    await asyncio.sleep(0.5)
    
    await scenario_optimal_flow(rl_module)
    await asyncio.sleep(0.5)
    
    await scenario_learning_progression(rl_module)
    await asyncio.sleep(0.5)
    
    await scenario_performance_comparison()
    
    # Final summary
    print_separator()
    print("  DEMO COMPLETE")
    print_separator()
    print("\nKey Takeaways:")
    print("  ✓ RL learns optimal policies through trial and error")
    print("  ✓ Q-learning updates values based on observed rewards")
    print("  ✓ Epsilon-greedy balances exploration vs exploitation")
    print("  ✓ Works well for flow state maintenance (60-70% performance)")
    print("  ✓ Can save/load learned Q-tables for persistence")
    print("\nRL vs Other Methods:")
    print("  • Rule-based: Fast but rigid")
    print("  • Fuzzy Logic: Smooth but predefined")
    print("  • RL: Adaptive and learns from experience ✨")
    print()


if __name__ == '__main__':
    asyncio.run(main())
