#!/usr/bin/env python3
"""
Batch Research Experiments Runner

This script runs multiple experiments with different configurations for comprehensive research.
It's designed for systematic parameter sweeps and comparative studies.

Usage:
    python examples/batch_experiments.py
"""

import asyncio
import itertools
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.coordinator import GameCoordinator, ExperimentConfig
from game_theory.games import GameType
from game_theory.payoff import RewardMatrix
from utils.conversation_tracker import conversation_tracker


class BatchExperimentRunner:
    """Runs systematic batch experiments for research."""
    
    def __init__(self, base_results_dir: str = "batch_research_results"):
        self.base_results_dir = Path(base_results_dir)
        self.base_results_dir.mkdir(exist_ok=True)
        self.all_results = []
        
    async def run_parameter_sweep(self):
        """Run a parameter sweep across different experimental conditions."""
        
        print("🔬 Starting Batch Parameter Sweep Experiments")
        print("=" * 50)
        
        # Define parameter space for systematic exploration
        parameter_space = {
            "num_rounds": [10, 20, 50],  # Different game lengths
            "num_repetitions": [2, 3],   # Statistical robustness
            "cooperation_thresholds": [0.3, 0.5, 0.7],  # Agent personality variants
            "game_combinations": [
                [GameType.PRISONERS_DILEMMA],
                [GameType.PUBLIC_GOODS],
                [GameType.KNOWLEDGE_SHARING],
                [GameType.PRISONERS_DILEMMA, GameType.PUBLIC_GOODS],
                [GameType.PRISONERS_DILEMMA, GameType.KNOWLEDGE_SHARING],
                [GameType.PUBLIC_GOODS, GameType.KNOWLEDGE_SHARING],
                [GameType.PRISONERS_DILEMMA, GameType.PUBLIC_GOODS, GameType.KNOWLEDGE_SHARING]
            ]
        }
        
        # Calculate total experiments
        total_experiments = (len(parameter_space["num_rounds"]) * 
                           len(parameter_space["num_repetitions"]) * 
                           len(parameter_space["cooperation_thresholds"]) * 
                           len(parameter_space["game_combinations"]))
        
        print(f"📊 Parameter Space:")
        print(f"  - Rounds: {parameter_space['num_rounds']}")
        print(f"  - Repetitions: {parameter_space['num_repetitions']}")
        print(f"  - Cooperation Thresholds: {parameter_space['cooperation_thresholds']}")
        print(f"  - Game Combinations: {len(parameter_space['game_combinations'])} different sets")
        print(f"  - Total Experiments: {total_experiments}")
        
        experiment_count = 0
        
        # Systematic parameter sweep
        for rounds in parameter_space["num_rounds"]:
            for repetitions in parameter_space["num_repetitions"]:
                for coop_threshold in parameter_space["cooperation_thresholds"]:
                    for game_combo in parameter_space["game_combinations"]:
                        
                        experiment_count += 1
                        print(f"\n🧪 Experiment {experiment_count}/{total_experiments}")
                        print(f"   Parameters: {rounds} rounds, {repetitions} reps, "
                              f"{coop_threshold} coop_threshold")
                        print(f"   Games: {[g.value for g in game_combo]}")
                        
                        # Create coordinator with fresh agents for each experiment
                        coordinator = GameCoordinator(
                            logger_name=f"batch_exp_{experiment_count}",
                            results_dir=str(self.base_results_dir / f"experiment_{experiment_count:03d}")
                        )
                        
                        # Create agents with specific cooperation threshold
                        self._create_research_agents(coordinator, coop_threshold)
                        
                        # Configure experiment
                        config = ExperimentConfig(
                            game_types=game_combo,
                            agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
                            num_rounds=rounds,
                            num_repetitions=repetitions,
                            save_results=True,
                            results_dir=str(self.base_results_dir / f"experiment_{experiment_count:03d}"),
                            enable_conversation_tracking=True,
                            enable_detailed_logging=True,
                            experiment_description=f"Parameter sweep experiment {experiment_count}: "
                                                 f"rounds={rounds}, reps={repetitions}, "
                                                 f"coop_threshold={coop_threshold}, "
                                                 f"games={[g.value for g in game_combo]}"
                        )
                        
                        try:
                            # Run experiment
                            start_time = datetime.now()
                            result = await coordinator.run_experiment(config)
                            end_time = datetime.now()
                            
                            # Add metadata
                            result["batch_metadata"] = {
                                "experiment_number": experiment_count,
                                "total_experiments": total_experiments,
                                "parameters": {
                                    "rounds": rounds,
                                    "repetitions": repetitions,
                                    "cooperation_threshold": coop_threshold,
                                    "game_types": [g.value for g in game_combo]
                                },
                                "duration_seconds": (end_time - start_time).total_seconds()
                            }
                            
                            self.all_results.append(result)
                            
                            print(f"   ✅ Completed in {(end_time - start_time).total_seconds():.1f}s")
                            
                        except Exception as e:
                            print(f"   ❌ Failed: {e}")
                            continue
        
        print(f"\n🎉 Batch experiments completed! {len(self.all_results)}/{total_experiments} successful")
        
        # Generate comparative analysis
        await self._generate_batch_analysis()
    
    def _create_research_agents(self, coordinator: GameCoordinator, cooperation_threshold: float):
        """Create a standardized set of research agents with specific cooperation threshold."""
        
        # Clear any existing agents
        coordinator.agents.clear()
        
        # Standard research agent set with parameter variation
        agent_configs = [
            ("Coop_Agent", "cooperative", cooperation_threshold + 0.1),
            ("Comp_Agent", "competitive", max(0.1, cooperation_threshold - 0.2)),
            ("TFT_Agent", "tit_for_tat", cooperation_threshold),
            ("Adapt_Agent", "adaptive", cooperation_threshold),
            ("Random_Agent", "random", 0.5)  # Random agents don't use cooperation threshold
        ]
        
        for name, strategy, threshold in agent_configs:
            coordinator.create_agent(
                strategy, 
                name, 
                cooperation_threshold=min(0.9, max(0.1, threshold)),
                trust_threshold=cooperation_threshold
            )
    
    async def run_comparative_study(self):
        """Run comparative study between different agent populations."""
        
        print("\n🔍 Starting Comparative Agent Population Study")
        print("=" * 50)
        
        # Define different population compositions
        population_configs = [
            {
                "name": "cooperative_majority",
                "description": "Majority cooperative agents (75%)",
                "agents": [
                    ("Coop1", "cooperative"), ("Coop2", "cooperative"), ("Coop3", "cooperative"),
                    ("Comp1", "competitive")
                ]
            },
            {
                "name": "competitive_majority", 
                "description": "Majority competitive agents (75%)",
                "agents": [
                    ("Comp1", "competitive"), ("Comp2", "competitive"), ("Comp3", "competitive"),
                    ("Coop1", "cooperative")
                ]
            },
            {
                "name": "balanced_population",
                "description": "Balanced population",
                "agents": [
                    ("Coop1", "cooperative"), ("Comp1", "competitive"),
                    ("TFT1", "tit_for_tat"), ("Adapt1", "adaptive")
                ]
            },
            {
                "name": "adaptive_majority",
                "description": "Majority adaptive agents (75%)",
                "agents": [
                    ("Adapt1", "adaptive"), ("Adapt2", "adaptive"), ("Adapt3", "adaptive"),
                    ("Random1", "random")
                ]
            },
            {
                "name": "mixed_strategies",
                "description": "All strategy types",
                "agents": [
                    ("Coop1", "cooperative"), ("Comp1", "competitive"),
                    ("TFT1", "tit_for_tat"), ("Adapt1", "adaptive"), ("Random1", "random")
                ]
            }
        ]
        
        comparative_results = []
        
        for i, pop_config in enumerate(population_configs):
            print(f"\n🧬 Population {i+1}/{len(population_configs)}: {pop_config['name']}")
            print(f"   Description: {pop_config['description']}")
            print(f"   Agents: {[f'{name}({strategy})' for name, strategy in pop_config['agents']]}")
            
            # Create coordinator
            coordinator = GameCoordinator(
                logger_name=f"comparative_{pop_config['name']}",
                results_dir=str(self.base_results_dir / f"comparative_{pop_config['name']}")
            )
            
            # Create specific population
            for name, strategy in pop_config["agents"]:
                coordinator.create_agent(strategy, name)
            
            # Run comprehensive experiment
            config = ExperimentConfig(
                game_types=[GameType.PRISONERS_DILEMMA, GameType.PUBLIC_GOODS, GameType.KNOWLEDGE_SHARING],
                agent_types=list(set(strategy for _, strategy in pop_config["agents"])),
                num_rounds=25,
                num_repetitions=3,
                save_results=True,
                results_dir=str(self.base_results_dir / f"comparative_{pop_config['name']}"),
                enable_conversation_tracking=True,
                enable_detailed_logging=True,
                experiment_description=f"Comparative study: {pop_config['description']}"
            )
            
            try:
                result = await coordinator.run_experiment(config)
                result["population_config"] = pop_config
                comparative_results.append(result)
                
                print(f"   ✅ Completed successfully")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                continue
        
        # Analyze comparative results
        print(f"\n📊 Comparative Analysis Results:")
        
        for result in comparative_results:
            pop_name = result["population_config"]["name"]
            print(f"\n🧬 {pop_name}:")
            
            # Calculate aggregate cooperation rates
            total_cooperation = 0
            total_games = 0
            total_welfare = 0
            
            for game_type, games in result["results"].items():
                for game in games:
                    coop_rates = game.get("cooperation_rates", {})
                    if coop_rates:
                        total_cooperation += sum(coop_rates.values())
                        total_games += len(coop_rates)
                    
                    payoffs = game.get("payoffs", {})
                    if payoffs:
                        total_welfare += sum(payoffs.values())
            
            avg_cooperation = total_cooperation / total_games if total_games > 0 else 0
            print(f"   - Average cooperation rate: {avg_cooperation:.3f}")
            print(f"   - Total welfare generated: {total_welfare:.1f}")
            print(f"   - Games analyzed: {total_games}")
        
        return comparative_results
    
    async def _generate_batch_analysis(self):
        """Generate comprehensive analysis of all batch experiments."""
        
        print(f"\n📈 Generating Batch Analysis...")
        
        if not self.all_results:
            print("No results to analyze.")
            return
        
        # Aggregate analysis
        analysis = {
            "total_experiments": len(self.all_results),
            "parameter_effects": {},
            "game_type_effects": {},
            "cooperation_trends": {},
            "performance_patterns": {}
        }
        
        # Analyze parameter effects
        for result in self.all_results:
            metadata = result.get("batch_metadata", {})
            params = metadata.get("parameters", {})
            
            # Group by parameters
            rounds = params.get("rounds")
            coop_threshold = params.get("cooperation_threshold")
            
            # Calculate aggregate metrics for this experiment
            total_cooperation = 0
            total_welfare = 0
            game_count = 0
            
            for game_type, games in result["results"].items():
                for game in games:
                    coop_rates = game.get("cooperation_rates", {})
                    payoffs = game.get("payoffs", {})
                    
                    if coop_rates:
                        total_cooperation += sum(coop_rates.values()) / len(coop_rates)
                        game_count += 1
                    
                    if payoffs:
                        total_welfare += sum(payoffs.values())
            
            avg_cooperation = total_cooperation / game_count if game_count > 0 else 0
            
            # Store in analysis
            if rounds not in analysis["parameter_effects"]:
                analysis["parameter_effects"][rounds] = {"cooperation": [], "welfare": []}
            
            analysis["parameter_effects"][rounds]["cooperation"].append(avg_cooperation)
            analysis["parameter_effects"][rounds]["welfare"].append(total_welfare)
        
        # Generate summary report
        report_lines = []
        report_lines.append("# Batch Experiment Analysis Report")
        report_lines.append(f"Generated: {datetime.now()}")
        report_lines.append(f"Total experiments: {analysis['total_experiments']}")
        report_lines.append("")
        
        report_lines.append("## Parameter Effects")
        for rounds, effects in analysis["parameter_effects"].items():
            avg_coop = sum(effects["cooperation"]) / len(effects["cooperation"])
            avg_welfare = sum(effects["welfare"]) / len(effects["welfare"])
            
            report_lines.append(f"### {rounds} Rounds:")
            report_lines.append(f"- Average cooperation: {avg_coop:.3f}")
            report_lines.append(f"- Average welfare: {avg_welfare:.1f}")
            report_lines.append(f"- Sample size: {len(effects['cooperation'])}")
            report_lines.append("")
        
        # Save report
        report_file = self.base_results_dir / "batch_analysis_report.md"
        with open(report_file, 'w') as f:
            f.write("\n".join(report_lines))
        
        print(f"💾 Batch analysis report saved to: {report_file}")


async def main():
    """Main batch experiment function."""
    
    print("🚀 Multi-Agent Batch Research Experiments")
    print("=" * 45)
    
    runner = BatchExperimentRunner()
    
    # Run parameter sweep
    await runner.run_parameter_sweep()
    
    # Run comparative study
    await runner.run_comparative_study()
    
    print(f"\n🏁 All batch experiments completed!")
    print(f"📁 Results saved to: {runner.base_results_dir}")
    
    # Show conversation tracking summary
    sessions = conversation_tracker.get_session_history()
    print(f"💬 Total conversation sessions recorded: {len(sessions)}")


if __name__ == "__main__":
    asyncio.run(main())