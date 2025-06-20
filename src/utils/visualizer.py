"""Visualization utilities for game results and agent behavior."""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from ..game_theory.games import GameResult, GameType
from ..utils.logger import get_logger


class GameVisualizer:
    """Visualizer for game theory experiment results."""
    
    def __init__(self, results_dir: str = "results", output_dir: str = "results/plots"):
        self.results_dir = results_dir
        self.output_dir = output_dir
        self.logger = get_logger("visualizer")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def plot_payoff_comparison(
        self,
        results: List[Dict[str, Any]],
        title: str = "Agent Payoff Comparison",
        save_path: Optional[str] = None
    ) -> None:
        """Plot payoff comparison across agents."""
        # Prepare data
        data = []
        for result in results:
            for agent, payoff in result["payoffs"].items():
                data.append({
                    "Agent": agent,
                    "Payoff": payoff,
                    "Game": result["game_type"],
                    "Match": result.get("additional_metrics", {}).get("tournament_match", "Unknown")
                })
        
        df = pd.DataFrame(data)
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        if len(df["Game"].unique()) > 1:
            # Multiple games - use subplot
            games = df["Game"].unique()
            n_games = len(games)
            
            fig, axes = plt.subplots(1, n_games, figsize=(6 * n_games, 6), sharey=True)
            if n_games == 1:
                axes = [axes]
            
            for i, game in enumerate(games):
                game_data = df[df["Game"] == game]
                sns.boxplot(data=game_data, x="Agent", y="Payoff", ax=axes[i])
                axes[i].set_title(f"{game}")
                axes[i].tick_params(axis='x', rotation=45)
        else:
            # Single game
            sns.boxplot(data=df, x="Agent", y="Payoff")
            plt.xticks(rotation=45)
        
        plt.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Payoff comparison saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_cooperation_rates(
        self,
        results: List[Dict[str, Any]],
        title: str = "Cooperation Rates by Agent",
        save_path: Optional[str] = None
    ) -> None:
        """Plot cooperation rates for each agent."""
        # Prepare data
        data = []
        for result in results:
            for agent, coop_rate in result["cooperation_rates"].items():
                data.append({
                    "Agent": agent,
                    "Cooperation_Rate": coop_rate,
                    "Game": result["game_type"]
                })
        
        df = pd.DataFrame(data)
        
        # Create plot
        plt.figure(figsize=(10, 6))
        
        if len(df["Game"].unique()) > 1:
            sns.barplot(data=df, x="Agent", y="Cooperation_Rate", hue="Game")
        else:
            sns.barplot(data=df, x="Agent", y="Cooperation_Rate")
        
        plt.title(title)
        plt.ylabel("Cooperation Rate")
        plt.ylim(0, 1)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Cooperation rates saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_strategy_performance(
        self,
        results: List[Dict[str, Any]],
        title: str = "Strategy Performance Analysis",
        save_path: Optional[str] = None
    ) -> None:
        """Plot performance analysis by strategy type."""
        # Extract strategy from agent names (assuming format: Name_Strategy)
        data = []
        for result in results:
            for agent, payoff in result["payoffs"].items():
                strategy = agent.split('_')[-1] if '_' in agent else agent
                cooperation_rate = result["cooperation_rates"].get(agent, 0)
                
                data.append({
                    "Strategy": strategy,
                    "Payoff": payoff,
                    "Cooperation_Rate": cooperation_rate,
                    "Game": result["game_type"]
                })
        
        df = pd.DataFrame(data)
        
        # Create subplot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Average payoff by strategy
        strategy_payoffs = df.groupby("Strategy")["Payoff"].mean().sort_values(ascending=False)
        strategy_payoffs.plot(kind="bar", ax=ax1)
        ax1.set_title("Average Payoff by Strategy")
        ax1.set_ylabel("Average Payoff")
        ax1.tick_params(axis='x', rotation=45)
        
        # Cooperation rate vs payoff scatter
        strategy_summary = df.groupby("Strategy").agg({
            "Payoff": "mean",
            "Cooperation_Rate": "mean"
        }).reset_index()
        
        scatter = ax2.scatter(
            strategy_summary["Cooperation_Rate"],
            strategy_summary["Payoff"],
            s=100,
            alpha=0.7
        )
        
        # Add strategy labels
        for i, row in strategy_summary.iterrows():
            ax2.annotate(
                row["Strategy"],
                (row["Cooperation_Rate"], row["Payoff"]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9
            )
        
        ax2.set_xlabel("Average Cooperation Rate")
        ax2.set_ylabel("Average Payoff")
        ax2.set_title("Cooperation vs Performance")
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Strategy performance saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_game_evolution(
        self,
        result: Dict[str, Any],
        title: str = "Game Evolution Over Time",
        save_path: Optional[str] = None
    ) -> None:
        """Plot how cooperation and payoffs evolve during a game."""
        actions_history = result["actions_history"]
        
        if not actions_history:
            self.logger.warning("No action history to plot")
            return
        
        # Parse actions by round
        rounds_data = {}
        current_round = 0
        round_actions = {}
        
        for i, (agent, action_str) in enumerate(actions_history):
            # Group actions by pairs (assuming 2-player games)
            if agent not in round_actions:
                round_actions[agent] = action_str
            else:
                # Complete round
                rounds_data[current_round] = round_actions.copy()
                current_round += 1
                round_actions = {agent: action_str}
        
        # Add final round if incomplete
        if round_actions:
            rounds_data[current_round] = round_actions
        
        if not rounds_data:
            self.logger.warning("Could not parse rounds data")
            return
        
        # Calculate cooperation rate by round
        rounds = sorted(rounds_data.keys())
        cooperation_by_agent = {}
        
        agents = list(rounds_data[rounds[0]].keys())
        for agent in agents:
            cooperation_by_agent[agent] = []
        
        for round_num in rounds:
            round_data = rounds_data[round_num]
            for agent in agents:
                action = round_data.get(agent, "defect")
                cooperated = action in ["cooperate", "share_knowledge"]
                cooperation_by_agent[agent].append(1 if cooperated else 0)
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Plot cooperation evolution
        plt.subplot(2, 1, 1)
        for agent, cooperation_history in cooperation_by_agent.items():
            # Calculate moving average
            window_size = min(5, len(cooperation_history))
            if window_size > 1:
                cooperation_ma = pd.Series(cooperation_history).rolling(window=window_size).mean()
            else:
                cooperation_ma = cooperation_history
            
            plt.plot(rounds[:len(cooperation_ma)], cooperation_ma, label=agent, marker='o', alpha=0.7)
        
        plt.title("Cooperation Rate Evolution")
        plt.xlabel("Round")
        plt.ylabel("Cooperation Rate (Moving Average)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot cumulative payoffs if available
        plt.subplot(2, 1, 2)
        if "additional_metrics" in result and isinstance(result["additional_metrics"], dict):
            # Try to extract round-by-round payoffs
            plt.text(0.5, 0.5, "Round-by-round payoff data not available", 
                    ha='center', va='center', transform=plt.gca().transAxes)
        else:
            # Show final payoffs as bar chart
            agents = list(result["payoffs"].keys())
            payoffs = list(result["payoffs"].values())
            plt.bar(agents, payoffs)
            plt.title("Final Payoffs")
            plt.ylabel("Total Payoff")
        
        plt.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Game evolution saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def create_experiment_report(
        self,
        experiment_data: Dict[str, Any],
        save_dir: Optional[str] = None
    ) -> None:
        """Create a comprehensive visual report for an experiment."""
        if save_dir is None:
            save_dir = os.path.join(self.output_dir, f"experiment_{experiment_data['experiment_id']}")
        
        os.makedirs(save_dir, exist_ok=True)
        
        self.logger.info(f"Creating experiment report in {save_dir}")
        
        # Process results by game type
        for game_type, game_results in experiment_data["results"].items():
            game_save_dir = os.path.join(save_dir, game_type)
            os.makedirs(game_save_dir, exist_ok=True)
            
            # Payoff comparison
            self.plot_payoff_comparison(
                game_results,
                title=f"{game_type} - Payoff Comparison",
                save_path=os.path.join(game_save_dir, "payoff_comparison.png")
            )
            
            # Cooperation rates
            self.plot_cooperation_rates(
                game_results,
                title=f"{game_type} - Cooperation Rates",
                save_path=os.path.join(game_save_dir, "cooperation_rates.png")
            )
            
            # Strategy performance
            self.plot_strategy_performance(
                game_results,
                title=f"{game_type} - Strategy Performance",
                save_path=os.path.join(game_save_dir, "strategy_performance.png")
            )
            
            # Individual game evolution (first match only)
            if game_results:
                self.plot_game_evolution(
                    game_results[0],
                    title=f"{game_type} - Game Evolution (Sample)",
                    save_path=os.path.join(game_save_dir, "game_evolution.png")
                )
        
        # Create summary statistics
        self._create_summary_statistics(experiment_data, save_dir)
        
        self.logger.info(f"Experiment report completed: {save_dir}")
    
    def _create_summary_statistics(
        self,
        experiment_data: Dict[str, Any],
        save_dir: str
    ) -> None:
        """Create summary statistics file."""
        summary = {
            "experiment_id": experiment_data["experiment_id"],
            "timestamp": datetime.now().isoformat(),
            "config": experiment_data["config"],
            "agents": experiment_data["agents"],
            "summary_by_game": {}
        }
        
        for game_type, game_results in experiment_data["results"].items():
            if not game_results:
                continue
            
            # Aggregate statistics
            all_payoffs = {}
            all_cooperation_rates = {}
            winners = []
            
            for result in game_results:
                for agent, payoff in result["payoffs"].items():
                    if agent not in all_payoffs:
                        all_payoffs[agent] = []
                    all_payoffs[agent].append(payoff)
                
                for agent, coop_rate in result["cooperation_rates"].items():
                    if agent not in all_cooperation_rates:
                        all_cooperation_rates[agent] = []
                    all_cooperation_rates[agent].append(coop_rate)
                
                if result["winner"]:
                    winners.append(result["winner"])
            
            # Calculate summary statistics
            summary["summary_by_game"][game_type] = {
                "total_matches": len(game_results),
                "average_payoffs": {
                    agent: np.mean(payoffs) for agent, payoffs in all_payoffs.items()
                },
                "average_cooperation_rates": {
                    agent: np.mean(coop_rates) for agent, coop_rates in all_cooperation_rates.items()
                },
                "win_counts": {agent: winners.count(agent) for agent in set(winners)},
                "most_successful_agent": max(
                    all_payoffs.keys(),
                    key=lambda agent: np.mean(all_payoffs[agent])
                ) if all_payoffs else None
            }
        
        # Save summary
        summary_path = os.path.join(save_dir, "summary_statistics.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Summary statistics saved to {summary_path}")


class ResultsPlotter:
    """Simple plotter for quick visualizations."""
    
    @staticmethod
    def quick_payoff_plot(payoffs: Dict[str, float], title: str = "Agent Payoffs") -> None:
        """Quick payoff visualization."""
        agents = list(payoffs.keys())
        values = list(payoffs.values())
        
        plt.figure(figsize=(8, 6))
        bars = plt.bar(agents, values)
        
        # Color bars based on performance
        max_payoff = max(values)
        for bar, value in zip(bars, values):
            if value == max_payoff:
                bar.set_color('gold')
            elif value > np.mean(values):
                bar.set_color('lightgreen')
            else:
                bar.set_color('lightcoral')
        
        plt.title(title)
        plt.ylabel("Payoff")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def quick_cooperation_plot(coop_rates: Dict[str, float], title: str = "Cooperation Rates") -> None:
        """Quick cooperation rate visualization."""
        agents = list(coop_rates.keys())
        values = list(coop_rates.values())
        
        plt.figure(figsize=(8, 6))
        bars = plt.bar(agents, values)
        
        # Color bars based on cooperation level
        for bar, value in zip(bars, values):
            if value > 0.7:
                bar.set_color('darkgreen')
            elif value > 0.3:
                bar.set_color('orange')
            else:
                bar.set_color('darkred')
        
        plt.title(title)
        plt.ylabel("Cooperation Rate")
        plt.ylim(0, 1)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()