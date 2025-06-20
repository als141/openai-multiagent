"""Prisoner's Dilemma experiment script."""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.coordinator import GameCoordinator, ExperimentConfig
from src.game_theory.games import GameType
from src.game_theory.payoff import RewardMatrix
from src.utils.visualizer import GameVisualizer


async def run_prisoner_dilemma_tournament():
    """Run a comprehensive Prisoner's Dilemma tournament."""
    print("🎮 Prisoner's Dilemma Tournament")
    
    # Create coordinator
    coordinator = GameCoordinator()
    
    # Create diverse set of agents
    agents_config = [
        ("Alice_Cooperative", "cooperative"),
        ("Bob_Competitive", "competitive"),
        ("Charlie_TitForTat", "tit_for_tat"),
        ("Diana_Adaptive", "adaptive"),
        ("Eve_Random", "random"),
        ("Frank_Cooperative2", "cooperative"),  # Another cooperative for comparison
        ("Grace_Adaptive2", "adaptive")         # Another adaptive for comparison
    ]
    
    for name, agent_type in agents_config:
        coordinator.create_agent(agent_type, name)
    
    print(f"✅ Created {len(agents_config)} agents")
    
    # Test different reward matrices
    reward_matrices = {
        "standard": RewardMatrix.prisoner_dilemma(),
        "high_temptation": RewardMatrix(
            cooperate_cooperate=(3, 3),
            cooperate_defect=(0, 7),
            defect_cooperate=(7, 0),
            defect_defect=(1, 1)
        ),
        "low_punishment": RewardMatrix(
            cooperate_cooperate=(3, 3),
            cooperate_defect=(0, 5),
            defect_cooperate=(5, 0),
            defect_defect=(2, 2)
        )
    }
    
    all_results = {}
    
    for matrix_name, reward_matrix in reward_matrices.items():
        print(f"\n🎯 Testing {matrix_name} reward matrix")
        
        # Create experiment config
        config = ExperimentConfig(
            game_types=[GameType.PRISONERS_DILEMMA],
            agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
            num_rounds=20,
            num_repetitions=3,
            save_results=True,
            reward_matrix=reward_matrix
        )
        
        # Run experiment
        results = await coordinator.run_experiment(config)
        all_results[matrix_name] = results
        
        print(f"✅ Completed {matrix_name} experiment")
        
        # Reset agents for next experiment
        coordinator.reset_all_agents()
    
    # Create comprehensive visualizations
    print("\n📊 Creating visualizations...")
    
    visualizer = GameVisualizer()
    
    for matrix_name, results in all_results.items():
        print(f"Creating plots for {matrix_name}...")
        visualizer.create_experiment_report(
            results,
            save_dir=f"results/plots/prisoner_dilemma_{matrix_name}_{results['experiment_id']}"
        )
    
    # Compare results across matrices
    print("\n📈 Experiment Summary:")
    for matrix_name, results in all_results.items():
        print(f"\n{matrix_name.upper()} MATRIX:")
        
        # Get results for prisoners dilemma
        pd_results = results["results"]["prisoners_dilemma"]
        
        # Calculate average statistics
        avg_payoffs = {}
        avg_cooperation = {}
        
        for result in pd_results:
            for agent, payoff in result["payoffs"].items():
                if agent not in avg_payoffs:
                    avg_payoffs[agent] = []
                avg_payoffs[agent].append(payoff)
            
            for agent, coop_rate in result["cooperation_rates"].items():
                if agent not in avg_cooperation:
                    avg_cooperation[agent] = []
                avg_cooperation[agent].append(coop_rate)
        
        # Print summary
        for agent in avg_payoffs:
            avg_pay = sum(avg_payoffs[agent]) / len(avg_payoffs[agent])
            avg_coop = sum(avg_cooperation[agent]) / len(avg_cooperation[agent])
            print(f"  {agent}: Avg Payoff={avg_pay:.2f}, Avg Cooperation={avg_coop:.2f}")
    
    print("\n🎉 Tournament completed!")
    return all_results


async def run_strategy_evolution():
    """Test how strategies perform over many iterations."""
    print("🧬 Strategy Evolution Experiment")
    
    coordinator = GameCoordinator()
    
    # Create agents
    agents = [
        ("Coop", "cooperative"),
        ("Comp", "competitive"),
        ("TFT", "tit_for_tat"),
        ("Adaptive", "adaptive")
    ]
    
    for name, agent_type in agents:
        coordinator.create_agent(agent_type, name)
    
    # Run many short tournaments to see adaptation
    evolution_results = []
    
    for iteration in range(5):
        print(f"\n🔄 Evolution iteration {iteration + 1}")
        
        config = ExperimentConfig(
            game_types=[GameType.PRISONERS_DILEMMA],
            agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
            num_rounds=15,
            num_repetitions=2,
            save_results=False
        )
        
        results = await coordinator.run_experiment(config)
        evolution_results.append(results)
        
        # Show current agent states
        stats = coordinator.get_agent_statistics()
        print("Current agent statistics:")
        for agent_name, agent_stats in stats.items():
            print(f"  {agent_name}: Rep={agent_stats['reputation']:.2f}, "
                  f"Coop={agent_stats['cooperation_rate']:.2f}")
    
    print("\n🎯 Evolution Summary:")
    
    # Track how cooperation rates changed over time
    for agent_name in coordinator.agents.keys():
        cooperation_over_time = []
        
        for iteration_result in evolution_results:
            pd_results = iteration_result["results"]["prisoners_dilemma"]
            
            # Calculate average cooperation for this agent in this iteration
            agent_cooperation = []
            for result in pd_results:
                if agent_name in result["cooperation_rates"]:
                    agent_cooperation.append(result["cooperation_rates"][agent_name])
            
            if agent_cooperation:
                avg_coop = sum(agent_cooperation) / len(agent_cooperation)
                cooperation_over_time.append(avg_coop)
        
        print(f"{agent_name}: {cooperation_over_time}")
    
    return evolution_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prisoner's Dilemma Experiments")
    parser.add_argument("--experiment", choices=["tournament", "evolution", "both"],
                       default="both", help="Type of experiment to run")
    
    args = parser.parse_args()
    
    async def main():
        if args.experiment in ["tournament", "both"]:
            await run_prisoner_dilemma_tournament()
        
        if args.experiment in ["evolution", "both"]:
            await run_strategy_evolution()
    
    asyncio.run(main())