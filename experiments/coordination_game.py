"""Coordination and knowledge sharing game experiments."""

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.coordinator import GameCoordinator, ExperimentConfig
from src.game_theory.games import GameType
from src.utils.visualizer import GameVisualizer


async def run_knowledge_sharing_experiment():
    """Run knowledge sharing game experiments."""
    print("🧠 Knowledge Sharing Experiment")
    
    coordinator = GameCoordinator()
    
    # Create agents with different sharing propensities
    agents_config = [
        ("Scholar_Cooperative", "cooperative"),      # Shares freely
        ("Hoarder_Competitive", "competitive"),      # Hoards knowledge
        ("Reciprocator_TitForTat", "tit_for_tat"),  # Shares if others share
        ("Learner_Adaptive", "adaptive"),            # Adapts sharing strategy
        ("Chaotic_Random", "random")                 # Random sharing
    ]
    
    for name, agent_type in agents_config:
        coordinator.create_agent(agent_type, name)
    
    print(f"✅ Created {len(agents_config)} agents")
    
    # Run knowledge sharing tournament
    config = ExperimentConfig(
        game_types=[GameType.KNOWLEDGE_SHARING],
        agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
        num_rounds=15,
        num_repetitions=2,
        save_results=True
    )
    
    results = await coordinator.run_experiment(config)
    
    # Analyze knowledge accumulation
    print("\n📚 Knowledge Accumulation Analysis:")
    
    final_stats = coordinator.get_agent_statistics()
    for agent_name, stats in final_stats.items():
        print(f"{agent_name}:")
        print(f"  Knowledge Count: {stats['knowledge_count']}")
        print(f"  Cooperation Rate: {stats['cooperation_rate']:.2f}")
        print(f"  Average Payoff: {stats['average_payoff']:.2f}")
        print(f"  Reputation: {stats['reputation']:.2f}")
    
    # Create visualizations
    visualizer = GameVisualizer()
    visualizer.create_experiment_report(results)
    
    print(f"📊 Results saved: experiment_{results['experiment_id']}")
    return results


async def run_public_goods_experiment():
    """Run public goods game experiments."""
    print("🏛️ Public Goods Game Experiment")
    
    coordinator = GameCoordinator()
    
    # Create agents representing different social attitudes
    agents_config = [
        ("Altruist_Cooperative", "cooperative"),     # Always contributes
        ("Egoist_Competitive", "competitive"),       # Minimal contributions
        ("Conditional_TitForTat", "tit_for_tat"),    # Responds to others
        ("Strategic_Adaptive", "adaptive"),          # Optimizes contributions
        ("Erratic_Random", "random"),                # Unpredictable
        ("Follower_Adaptive2", "adaptive")           # Another adaptive agent
    ]
    
    for name, agent_type in agents_config:
        coordinator.create_agent(agent_type, name)
    
    print(f"✅ Created {len(agents_config)} agents")
    
    # Run public goods tournament
    config = ExperimentConfig(
        game_types=[GameType.PUBLIC_GOODS],
        agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
        num_rounds=12,
        num_repetitions=2,
        save_results=True
    )
    
    results = await coordinator.run_experiment(config)
    
    # Analyze contribution patterns
    print("\n💰 Contribution Analysis:")
    
    # Extract contribution data from results
    public_goods_results = results["results"]["public_goods"]
    
    for result in public_goods_results[:3]:  # Show first few matches
        print(f"\nMatch: {result.get('additional_metrics', {}).get('tournament_match', 'Unknown')}")
        
        if "additional_metrics" in result and "contribution_history" in result["additional_metrics"]:
            contrib_history = result["additional_metrics"]["contribution_history"]
            
            # Calculate average contributions per agent
            agent_contribs = {}
            for round_contribs in contrib_history:
                for agent, contrib in round_contribs.items():
                    if agent not in agent_contribs:
                        agent_contribs[agent] = []
                    agent_contribs[agent].append(contrib)
            
            for agent, contribs in agent_contribs.items():
                avg_contrib = sum(contribs) / len(contribs)
                print(f"  {agent}: Avg contribution = {avg_contrib:.2f}")
    
    # Create visualizations
    visualizer = GameVisualizer()
    visualizer.create_experiment_report(results)
    
    print(f"📊 Results saved: experiment_{results['experiment_id']}")
    return results


async def run_multi_game_comparison():
    """Compare agent performance across different game types."""
    print("🎲 Multi-Game Comparison Experiment")
    
    coordinator = GameCoordinator()
    
    # Create a balanced set of agents
    agents_config = [
        ("Alpha_Cooperative", "cooperative"),
        ("Beta_Competitive", "competitive"),
        ("Gamma_TitForTat", "tit_for_tat"),
        ("Delta_Adaptive", "adaptive")
    ]
    
    for name, agent_type in agents_config:
        coordinator.create_agent(agent_type, name)
    
    print(f"✅ Created {len(agents_config)} agents")
    
    # Run all game types
    config = ExperimentConfig(
        game_types=[
            GameType.PRISONERS_DILEMMA,
            GameType.PUBLIC_GOODS,
            GameType.KNOWLEDGE_SHARING
        ],
        agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
        num_rounds=10,
        num_repetitions=2,
        save_results=True
    )
    
    results = await coordinator.run_experiment(config)
    
    # Cross-game analysis
    print("\n🔄 Cross-Game Performance Analysis:")
    
    game_performance = {}
    
    for game_type, game_results in results["results"].items():
        print(f"\n{game_type.upper()}:")
        
        # Calculate average performance per agent
        agent_performance = {}
        
        for result in game_results:
            for agent, payoff in result["payoffs"].items():
                if agent not in agent_performance:
                    agent_performance[agent] = []
                agent_performance[agent].append(payoff)
        
        # Store average performance
        game_performance[game_type] = {}
        for agent, payoffs in agent_performance.items():
            avg_payoff = sum(payoffs) / len(payoffs)
            game_performance[game_type][agent] = avg_payoff
            print(f"  {agent}: {avg_payoff:.2f}")
    
    # Find best performing strategy per game
    print("\n🏆 Best Strategy Per Game:")
    for game_type, agent_scores in game_performance.items():
        best_agent = max(agent_scores.keys(), key=lambda a: agent_scores[a])
        best_score = agent_scores[best_agent]
        strategy = best_agent.split('_')[-1]
        print(f"{game_type}: {strategy} ({best_agent}) with {best_score:.2f}")
    
    # Create comprehensive visualizations
    visualizer = GameVisualizer()
    visualizer.create_experiment_report(results)
    
    print(f"📊 Results saved: experiment_{results['experiment_id']}")
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Coordination Game Experiments")
    parser.add_argument("--experiment", 
                       choices=["knowledge", "public_goods", "comparison", "all"],
                       default="all", 
                       help="Type of experiment to run")
    
    args = parser.parse_args()
    
    async def main():
        if args.experiment in ["knowledge", "all"]:
            await run_knowledge_sharing_experiment()
            print("\n" + "="*50 + "\n")
        
        if args.experiment in ["public_goods", "all"]:
            await run_public_goods_experiment()
            print("\n" + "="*50 + "\n")
        
        if args.experiment in ["comparison", "all"]:
            await run_multi_game_comparison()
    
    asyncio.run(main())