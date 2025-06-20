#!/usr/bin/env python3
"""
Research-Grade Experiment Runner with Full Conversation Tracking

This script demonstrates how to run research-appropriate experiments with:
- Complete conversation history tracking
- Detailed experiment logging
- Research-grade data analysis
- Automatic report generation

Usage:
    python examples/research_experiment.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.coordinator import GameCoordinator, ExperimentConfig
from game_theory.games import GameType
from utils.conversation_tracker import conversation_tracker
from utils.experiment_logger import ExperimentLogger


async def run_research_experiment():
    """Run a comprehensive research experiment with full tracking."""
    
    print("🔬 Starting Research-Grade Multi-Agent Game Theory Experiment")
    print("=" * 60)
    
    # Initialize coordinator
    coordinator = GameCoordinator(
        logger_name="research_experiment",
        log_level="INFO",
        results_dir="research_results"
    )
    
    # Create diverse agent population for research
    coordinator.create_standard_agent_set()
    
    # Add additional research agents
    coordinator.create_agent("adaptive", "Dr_Adaptive_Researcher", 
                           cooperation_threshold=0.6, trust_threshold=0.4)
    coordinator.create_agent("tit_for_tat", "Prof_TitForTat_Scholar", 
                           cooperation_threshold=0.7, trust_threshold=0.6)
    coordinator.create_agent("cooperative", "Dr_Altruist_Cooper", 
                           cooperation_threshold=0.9, trust_threshold=0.8)
    
    print(f"📊 Research Population: {len(coordinator.agents)} agents")
    for name, agent in coordinator.agents.items():
        print(f"  - {name}: {agent.strategy}")
    
    # Configure comprehensive research experiment
    research_config = ExperimentConfig(
        game_types=[
            GameType.PRISONERS_DILEMMA,
            GameType.PUBLIC_GOODS,
            GameType.KNOWLEDGE_SHARING
        ],
        agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
        num_rounds=25,  # Longer games for research insights
        num_repetitions=3,  # Multiple repetitions for statistical significance
        save_results=True,
        results_dir="research_results",
        enable_conversation_tracking=True,  # Track all conversations
        enable_detailed_logging=True,       # Full research logging
        experiment_description="Comprehensive multi-agent game theory research experiment: "
                              "Analyzing cooperative vs competitive strategies across multiple game types "
                              "with full conversation tracking for behavioral analysis"
    )
    
    print(f"🎯 Experiment Configuration:")
    print(f"  - Game Types: {[gt.value for gt in research_config.game_types]}")
    print(f"  - Rounds per Game: {research_config.num_rounds}")
    print(f"  - Repetitions: {research_config.num_repetitions}")
    print(f"  - Conversation Tracking: {research_config.enable_conversation_tracking}")
    print(f"  - Detailed Logging: {research_config.enable_detailed_logging}")
    
    estimated_games = (len(coordinator.agents) * (len(coordinator.agents) - 1) // 2 * 
                      len(research_config.game_types) * research_config.num_repetitions)
    print(f"  - Estimated Total Games: {estimated_games}")
    
    print("\n🚀 Starting Experiment...")
    start_time = datetime.now()
    
    try:
        # Run the comprehensive experiment
        results = await coordinator.run_experiment(research_config)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✅ Experiment Completed Successfully!")
        print(f"⏱️  Total Duration: {duration}")
        print(f"📈 Experiment ID: {results['experiment_id']}")
        
        # Print summary statistics
        print(f"\n📊 Results Summary:")
        total_games = sum(len(game_results) for game_results in results['results'].values())
        print(f"  - Total Games Played: {total_games}")
        
        for game_type, game_results in results['results'].items():
            print(f"  - {game_type}: {len(game_results)} games")
            
            # Calculate aggregate statistics
            if game_results:
                total_payoffs = {}
                total_cooperation = {}
                
                for result in game_results:
                    for agent, payoff in result['payoffs'].items():
                        total_payoffs[agent] = total_payoffs.get(agent, 0) + payoff
                    
                    for agent, coop_rate in result['cooperation_rates'].items():
                        if agent not in total_cooperation:
                            total_cooperation[agent] = []
                        total_cooperation[agent].append(coop_rate)
                
                print(f"    Top performers:")
                sorted_agents = sorted(total_payoffs.items(), key=lambda x: x[1], reverse=True)
                for i, (agent, total_payoff) in enumerate(sorted_agents[:3]):
                    avg_payoff = total_payoff / len(game_results)
                    avg_coop = sum(total_cooperation[agent]) / len(total_cooperation[agent])
                    print(f"      {i+1}. {agent}: {avg_payoff:.2f} avg payoff, {avg_coop:.3f} cooperation rate")
        
        # Conversation analysis if tracking was enabled
        if research_config.enable_conversation_tracking:
            print(f"\n💬 Conversation Analysis:")
            sessions = conversation_tracker.get_session_history()
            print(f"  - Total Conversation Sessions: {len(sessions)}")
            
            if sessions:
                total_turns = sum(session['total_turns'] for session in sessions)
                print(f"  - Total Conversation Turns: {total_turns}")
                print(f"  - Average Turns per Session: {total_turns / len(sessions):.1f}")
                
                # Analyze a sample session
                sample_session = sessions[-1]  # Last session
                analysis = conversation_tracker.analyze_session(sample_session['session_id'])
                print(f"  - Sample Session Analysis ({sample_session['session_id']}):")
                
                for agent, stats in analysis['agent_statistics']['cooperation_rates'].items():
                    confidence = analysis['agent_statistics']['average_confidence'][agent]
                    response_time = analysis['agent_statistics']['average_response_time_ms'][agent]
                    print(f"    * {agent}: {stats:.3f} cooperation, {confidence:.3f} confidence, {response_time:.1f}ms response")
        
        # File outputs
        print(f"\n📁 Generated Files:")
        results_dir = Path("research_results")
        experiment_dir = results_dir / f"experiment_{results['experiment_id']}"
        
        if experiment_dir.exists():
            print(f"  - Experiment Directory: {experiment_dir}")
            print(f"  - Detailed Results: {experiment_dir}/detailed_results.json")
            print(f"  - Experiment Summary: {experiment_dir}/experiment_summary.json")
            print(f"  - Performance Metrics: {experiment_dir}/performance_metrics.csv")
            print(f"  - Error Logs: {experiment_dir}/logs/errors.log")
            print(f"  - Debug Logs: {experiment_dir}/logs/debug.log")
            
        conversation_file = results_dir / f"conversations_{results['experiment_id']}.csv"
        if conversation_file.exists():
            print(f"  - Conversation Data: {conversation_file}")
            
        print(f"\n🎉 Research experiment complete! Check the results directory for detailed analysis.")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Experiment failed: {e}")
        raise


async def analyze_conversation_patterns():
    """Analyze conversation patterns from recent sessions."""
    
    print("\n🔍 Analyzing Conversation Patterns...")
    
    sessions = conversation_tracker.get_session_history(limit=5)
    if not sessions:
        print("No conversation sessions found.")
        return
    
    print(f"Analyzing {len(sessions)} recent sessions:")
    
    for session in sessions:
        print(f"\n📝 Session: {session['session_id']}")
        print(f"  - Game: {session['game_type']}")
        print(f"  - Participants: {', '.join(session['participants'])}")
        print(f"  - Rounds: {session['total_rounds']}")
        print(f"  - Turns: {session['total_turns']}")
        
        # Get detailed analysis
        analysis = conversation_tracker.analyze_session(session['session_id'])
        
        print(f"  - Agent Performance:")
        for agent in session['participants']:
            if agent in analysis['agent_statistics']['cooperation_rates']:
                coop = analysis['agent_statistics']['cooperation_rates'][agent]
                conf = analysis['agent_statistics']['average_confidence'][agent]
                time_ms = analysis['agent_statistics']['average_response_time_ms'][agent]
                
                print(f"    * {agent}: {coop:.2f} cooperation, {conf:.2f} confidence, {time_ms:.0f}ms response")
        
        # Reasoning patterns
        print(f"  - Reasoning Patterns:")
        for agent, patterns in analysis['reasoning_patterns'].items():
            coop_focus = patterns['cooperation_focus_rate']
            comp_focus = patterns['competition_focus_rate']
            uncertainty = patterns['uncertainty_rate']
            complexity = patterns['reasoning_complexity']
            
            print(f"    * {agent}: {coop_focus:.2f} cooperation focus, {comp_focus:.2f} competition focus, "
                  f"{uncertainty:.2f} uncertainty, {complexity} complexity")


if __name__ == "__main__":
    print("🧪 Research-Grade Multi-Agent Game Theory Experiment")
    print("=" * 50)
    
    # Run the main research experiment
    results = asyncio.run(run_research_experiment())
    
    # Analyze conversation patterns
    asyncio.run(analyze_conversation_patterns())
    
    print("\n🏁 Research session complete!")