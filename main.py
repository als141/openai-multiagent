"""Main application for the game theory multi-agent system."""

import asyncio
import os
import sys
import argparse
from typing import Optional
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.coordinator import GameCoordinator, ExperimentConfig
from src.game_theory.games import GameType
from src.game_theory.payoff import RewardMatrix
from src.utils.logger import setup_logger
from src.utils.visualizer import GameVisualizer


async def run_demo() -> None:
    """Run a quick demonstration of the system."""
    print("🎮 Starting Game Theory Multi-Agent System Demo")
    
    # Create coordinator
    coordinator = GameCoordinator()
    
    # Create standard agents
    coordinator.create_standard_agent_set()
    
    print(f"✅ Created agents: {list(coordinator.agents.keys())}")
    
    # Run quick demo
    results = await coordinator.quick_demo()
    
    print("📊 Demo Results:")
    print(f"Experiment ID: {results['experiment_id']}")
    
    # Show agent statistics
    stats = coordinator.get_agent_statistics()
    print("\n📈 Agent Statistics:")
    for agent_name, agent_stats in stats.items():
        print(f"  {agent_name}:")
        print(f"    Strategy: {agent_stats['strategy']}")
        print(f"    Avg Payoff: {agent_stats['average_payoff']:.2f}")
        print(f"    Cooperation Rate: {agent_stats['cooperation_rate']:.2f}")
        print(f"    Reputation: {agent_stats['reputation']:.2f}")
    
    print(f"\n💾 Results saved in: results/experiment_{results['experiment_id']}.json")
    
    # Create visualizations
    try:
        visualizer = GameVisualizer()
        visualizer.create_experiment_report(results)
        print(f"📈 Visualizations created in: results/plots/experiment_{results['experiment_id']}/")
    except Exception as e:
        print(f"⚠️  Visualization creation failed: {e}")


async def run_custom_experiment(
    game_types: list[str],
    agents: list[str],
    rounds: int,
    repetitions: int
) -> None:
    """Run a custom experiment with specified parameters."""
    print("🔬 Starting Custom Experiment")
    
    coordinator = GameCoordinator()
    
    # Create specified agents
    for agent_spec in agents:
        if '_' in agent_spec:
            name, agent_type = agent_spec.rsplit('_', 1)
        else:
            name, agent_type = agent_spec, "adaptive"
        
        try:
            coordinator.create_agent(agent_type, name)
            print(f"✅ Created agent: {name} ({agent_type})")
        except ValueError as e:
            print(f"❌ Failed to create agent {name}: {e}")
    
    # Convert game type strings to enums
    game_type_map = {
        "prisoners_dilemma": GameType.PRISONERS_DILEMMA,
        "public_goods": GameType.PUBLIC_GOODS,
        "knowledge_sharing": GameType.KNOWLEDGE_SHARING,
    }
    
    valid_games = []
    for game_str in game_types:
        if game_str in game_type_map:
            valid_games.append(game_type_map[game_str])
        else:
            print(f"⚠️  Unknown game type: {game_str}")
    
    if not valid_games:
        print("❌ No valid games specified")
        return
    
    # Create experiment config
    config = ExperimentConfig(
        game_types=valid_games,
        agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
        num_rounds=rounds,
        num_repetitions=repetitions,
        save_results=True
    )
    
    # Run experiment
    results = await coordinator.run_experiment(config)
    
    print("✅ Experiment completed!")
    print(f"Experiment ID: {results['experiment_id']}")
    
    # Create visualizations
    try:
        visualizer = GameVisualizer()
        visualizer.create_experiment_report(results)
        print(f"📈 Visualizations created in: results/plots/experiment_{results['experiment_id']}/")
    except Exception as e:
        print(f"⚠️  Visualization creation failed: {e}")


async def run_single_game(
    game_type: str,
    agent1: str,
    agent2: str,
    rounds: int
) -> None:
    """Run a single game between two agents."""
    print(f"🎯 Starting Single Game: {game_type}")
    
    coordinator = GameCoordinator()
    
    # Create agents
    agent_specs = [agent1, agent2]
    for agent_spec in agent_specs:
        if '_' in agent_spec:
            name, agent_type = agent_spec.rsplit('_', 1)
        else:
            name, agent_type = agent_spec, "adaptive"
        
        try:
            coordinator.create_agent(agent_type, name)
            print(f"✅ Created agent: {name} ({agent_type})")
        except ValueError as e:
            print(f"❌ Failed to create agent {name}: {e}")
            return
    
    # Get game type
    game_type_map = {
        "prisoners_dilemma": GameType.PRISONERS_DILEMMA,
        "public_goods": GameType.PUBLIC_GOODS,
        "knowledge_sharing": GameType.KNOWLEDGE_SHARING,
    }
    
    if game_type not in game_type_map:
        print(f"❌ Unknown game type: {game_type}")
        return
    
    # Run single game
    result = await coordinator.run_single_game(
        game_type_map[game_type],
        [list(coordinator.agents.keys())[0], list(coordinator.agents.keys())[1]],
        rounds
    )
    
    print("🏁 Game Results:")
    print(f"Winner: {result.winner or 'Tie'}")
    print(f"Payoffs: {result.payoffs}")
    print(f"Cooperation Rates: {result.cooperation_rates}")


def main() -> None:
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        return
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Game Theory Multi-Agent System")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run quick demonstration')
    
    # Experiment command
    exp_parser = subparsers.add_parser('experiment', help='Run custom experiment')
    exp_parser.add_argument('--games', nargs='+', 
                           choices=['prisoners_dilemma', 'public_goods', 'knowledge_sharing'],
                           default=['prisoners_dilemma'],
                           help='Game types to run')
    exp_parser.add_argument('--agents', nargs='+',
                           default=['Alice_cooperative', 'Bob_competitive', 'Charlie_tit_for_tat'],
                           help='Agents in format Name_Type')
    exp_parser.add_argument('--rounds', type=int, default=10,
                           help='Number of rounds per game')
    exp_parser.add_argument('--repetitions', type=int, default=1,
                           help='Number of repetitions per match')
    
    # Single game command
    game_parser = subparsers.add_parser('game', help='Run single game')
    game_parser.add_argument('game_type', 
                            choices=['prisoners_dilemma', 'public_goods', 'knowledge_sharing'],
                            help='Type of game to play')
    game_parser.add_argument('agent1', help='First agent (Name_Type)')
    game_parser.add_argument('agent2', help='Second agent (Name_Type)')
    game_parser.add_argument('--rounds', type=int, default=10,
                            help='Number of rounds')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logger("main", level="INFO")
    
    try:
        if args.command == 'demo' or args.command is None:
            asyncio.run(run_demo())
        elif args.command == 'experiment':
            asyncio.run(run_custom_experiment(
                args.games, args.agents, args.rounds, args.repetitions
            ))
        elif args.command == 'game':
            asyncio.run(run_single_game(
                args.game_type, args.agent1, args.agent2, args.rounds
            ))
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
