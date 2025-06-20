#!/usr/bin/env python3
"""
Conversation Analysis Tool for Research

This script provides detailed analysis of agent conversations from experiments.
It can analyze individual sessions, compare agents across sessions, and generate
research-appropriate visualizations and reports.

Usage:
    python examples/conversation_analysis.py [session_id]
"""

import asyncio
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.conversation_tracker import conversation_tracker
from agents.types import AgentAction


class ConversationAnalyzer:
    """Advanced conversation analysis for research purposes."""
    
    def __init__(self, results_dir: str = "research_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def analyze_all_sessions(self) -> Dict[str, Any]:
        """Analyze all conversation sessions comprehensively."""
        
        sessions = conversation_tracker.get_session_history()
        if not sessions:
            print("No conversation sessions found.")
            return {}
        
        print(f"📊 Analyzing {len(sessions)} conversation sessions...")
        
        # Aggregate analysis
        analysis = {
            "total_sessions": len(sessions),
            "game_type_distribution": {},
            "agent_performance": {},
            "cooperation_trends": {},
            "reasoning_analysis": {},
            "response_time_analysis": {},
            "session_summaries": []
        }
        
        # Game type distribution
        for session in sessions:
            game_type = session['game_type']
            analysis["game_type_distribution"][game_type] = analysis["game_type_distribution"].get(game_type, 0) + 1
        
        # Per-session analysis
        all_agent_data = {}
        
        for session in sessions:
            session_analysis = conversation_tracker.analyze_session(session['session_id'])
            analysis["session_summaries"].append(session_analysis)
            
            # Aggregate agent data
            for agent in session['participants']:
                if agent not in all_agent_data:
                    all_agent_data[agent] = {
                        "sessions": 0,
                        "total_cooperation": 0,
                        "total_confidence": 0,
                        "total_response_time": 0,
                        "games_won": 0,
                        "reasoning_patterns": []
                    }
                
                stats = session_analysis['agent_statistics']
                if agent in stats['cooperation_rates']:
                    all_agent_data[agent]["sessions"] += 1
                    all_agent_data[agent]["total_cooperation"] += stats['cooperation_rates'][agent]
                    all_agent_data[agent]["total_confidence"] += stats['average_confidence'][agent]
                    all_agent_data[agent]["total_response_time"] += stats['average_response_time_ms'][agent]
                    
                    # Check if won
                    if session['final_outcomes'].get('winner') == agent:
                        all_agent_data[agent]["games_won"] += 1
                    
                    # Reasoning patterns
                    if agent in session_analysis['reasoning_patterns']:
                        all_agent_data[agent]["reasoning_patterns"].append(
                            session_analysis['reasoning_patterns'][agent]
                        )
        
        # Calculate averages
        for agent, data in all_agent_data.items():
            if data["sessions"] > 0:
                analysis["agent_performance"][agent] = {
                    "sessions_played": data["sessions"],
                    "average_cooperation_rate": data["total_cooperation"] / data["sessions"],
                    "average_confidence": data["total_confidence"] / data["sessions"],
                    "average_response_time_ms": data["total_response_time"] / data["sessions"],
                    "win_rate": data["games_won"] / data["sessions"],
                    "reasoning_complexity": self._analyze_reasoning_complexity(data["reasoning_patterns"])
                }
        
        return analysis
    
    def _analyze_reasoning_complexity(self, reasoning_patterns: List[Dict]) -> Dict[str, float]:
        """Analyze complexity of reasoning patterns."""
        if not reasoning_patterns:
            return {"average_length": 0, "cooperation_focus": 0, "uncertainty": 0}
        
        total_length = sum(p["average_reasoning_length"] for p in reasoning_patterns)
        total_coop_focus = sum(p["cooperation_focus_rate"] for p in reasoning_patterns)
        total_uncertainty = sum(p["uncertainty_rate"] for p in reasoning_patterns)
        
        return {
            "average_reasoning_length": total_length / len(reasoning_patterns),
            "cooperation_focus_rate": total_coop_focus / len(reasoning_patterns),
            "uncertainty_rate": total_uncertainty / len(reasoning_patterns)
        }
    
    def generate_cooperation_heatmap(self, analysis: Dict[str, Any]) -> None:
        """Generate a heatmap of cooperation rates between agents."""
        
        print("📈 Generating cooperation rate heatmap...")
        
        agents = list(analysis["agent_performance"].keys())
        if len(agents) < 2:
            print("Need at least 2 agents for heatmap.")
            return
        
        # Create cooperation matrix
        cooperation_matrix = []
        agent_names = []
        
        for agent in agents:
            cooperation_rate = analysis["agent_performance"][agent]["average_cooperation_rate"]
            cooperation_matrix.append([cooperation_rate] * len(agents))
            agent_names.append(agent)
        
        # Create heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cooperation_matrix,
            xticklabels=agent_names,
            yticklabels=agent_names,
            annot=True,
            cmap="RdYlGn",
            center=0.5,
            vmin=0,
            vmax=1,
            fmt=".3f"
        )
        plt.title("Agent Cooperation Rates Across All Games")
        plt.xlabel("Agents")
        plt.ylabel("Agents")
        plt.tight_layout()
        
        output_file = self.results_dir / "cooperation_heatmap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"💾 Cooperation heatmap saved to: {output_file}")
    
    def generate_performance_charts(self, analysis: Dict[str, Any]) -> None:
        """Generate performance comparison charts."""
        
        print("📊 Generating performance charts...")
        
        agent_data = analysis["agent_performance"]
        if not agent_data:
            print("No agent performance data available.")
            return
        
        agents = list(agent_data.keys())
        
        # Extract metrics
        cooperation_rates = [agent_data[agent]["average_cooperation_rate"] for agent in agents]
        win_rates = [agent_data[agent]["win_rate"] for agent in agents]
        confidence_levels = [agent_data[agent]["average_confidence"] for agent in agents]
        response_times = [agent_data[agent]["average_response_time_ms"] for agent in agents]
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Cooperation rates
        bars1 = ax1.bar(agents, cooperation_rates, color='green', alpha=0.7)
        ax1.set_title("Average Cooperation Rates")
        ax1.set_ylabel("Cooperation Rate")
        ax1.set_ylim(0, 1)
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars1, cooperation_rates):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{value:.3f}', ha='center', va='bottom')
        
        # Win rates
        bars2 = ax2.bar(agents, win_rates, color='blue', alpha=0.7)
        ax2.set_title("Win Rates")
        ax2.set_ylabel("Win Rate")
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='x', rotation=45)
        
        for bar, value in zip(bars2, win_rates):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{value:.3f}', ha='center', va='bottom')
        
        # Confidence levels
        bars3 = ax3.bar(agents, confidence_levels, color='orange', alpha=0.7)
        ax3.set_title("Average Confidence Levels")
        ax3.set_ylabel("Confidence")
        ax3.set_ylim(0, 1)
        ax3.tick_params(axis='x', rotation=45)
        
        for bar, value in zip(bars3, confidence_levels):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{value:.3f}', ha='center', va='bottom')
        
        # Response times
        bars4 = ax4.bar(agents, response_times, color='red', alpha=0.7)
        ax4.set_title("Average Response Times")
        ax4.set_ylabel("Response Time (ms)")
        ax4.tick_params(axis='x', rotation=45)
        
        for bar, value in zip(bars4, response_times):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{value:.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        output_file = self.results_dir / "agent_performance_charts.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"💾 Performance charts saved to: {output_file}")
    
    def export_detailed_csv(self, analysis: Dict[str, Any]) -> None:
        """Export detailed analysis to CSV for further research."""
        
        print("📝 Exporting detailed analysis to CSV...")
        
        # Agent performance data
        agent_data = []
        for agent, stats in analysis["agent_performance"].items():
            row = {
                "agent_name": agent,
                "sessions_played": stats["sessions_played"],
                "average_cooperation_rate": stats["average_cooperation_rate"],
                "average_confidence": stats["average_confidence"],
                "average_response_time_ms": stats["average_response_time_ms"],
                "win_rate": stats["win_rate"],
                **stats["reasoning_complexity"]
            }
            agent_data.append(row)
        
        # Save agent performance
        df_agents = pd.DataFrame(agent_data)
        agent_file = self.results_dir / "agent_performance_analysis.csv"
        df_agents.to_csv(agent_file, index=False)
        print(f"💾 Agent performance data saved to: {agent_file}")
        
        # Session summary data
        session_data = []
        for session_summary in analysis["session_summaries"]:
            session_info = session_summary["session_summary"]
            row = {
                "session_id": session_info["session_id"],
                "game_type": session_info["game_type"],
                "participants": ";".join(session_info["participants"]),
                "total_rounds": session_info["total_rounds"],
                "total_turns": session_info["total_turns"],
                "duration_seconds": session_info["duration"],
                "winner": session_info["final_outcomes"].get("winner", "tie")
            }
            
            # Add agent-specific data for this session
            for participant in session_info["participants"]:
                if participant in session_summary["agent_statistics"]["cooperation_rates"]:
                    row[f"{participant}_cooperation"] = session_summary["agent_statistics"]["cooperation_rates"][participant]
                    row[f"{participant}_confidence"] = session_summary["agent_statistics"]["average_confidence"][participant]
                    row[f"{participant}_response_time"] = session_summary["agent_statistics"]["average_response_time_ms"][participant]
            
            session_data.append(row)
        
        # Save session data
        df_sessions = pd.DataFrame(session_data)
        session_file = self.results_dir / "session_analysis.csv"
        df_sessions.to_csv(session_file, index=False)
        print(f"💾 Session analysis data saved to: {session_file}")
    
    def generate_research_report(self, analysis: Dict[str, Any]) -> None:
        """Generate a comprehensive research report."""
        
        print("📋 Generating research report...")
        
        report = []
        report.append("# Multi-Agent Game Theory Conversation Analysis Report")
        report.append(f"Generated on: {pd.Timestamp.now()}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append(f"- Total conversation sessions analyzed: {analysis['total_sessions']}")
        report.append(f"- Number of unique agents: {len(analysis['agent_performance'])}")
        report.append(f"- Game types covered: {', '.join(analysis['game_type_distribution'].keys())}")
        report.append("")
        
        # Game Type Distribution
        report.append("## Game Type Distribution")
        for game_type, count in analysis['game_type_distribution'].items():
            percentage = (count / analysis['total_sessions']) * 100
            report.append(f"- {game_type}: {count} sessions ({percentage:.1f}%)")
        report.append("")
        
        # Agent Performance Rankings
        report.append("## Agent Performance Rankings")
        
        # Sort by cooperation rate
        sorted_by_cooperation = sorted(
            analysis['agent_performance'].items(),
            key=lambda x: x[1]['average_cooperation_rate'],
            reverse=True
        )
        
        report.append("### By Cooperation Rate:")
        for i, (agent, stats) in enumerate(sorted_by_cooperation):
            report.append(f"{i+1}. {agent}: {stats['average_cooperation_rate']:.3f} "
                         f"(Win rate: {stats['win_rate']:.3f})")
        report.append("")
        
        # Sort by win rate
        sorted_by_wins = sorted(
            analysis['agent_performance'].items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )
        
        report.append("### By Win Rate:")
        for i, (agent, stats) in enumerate(sorted_by_wins):
            report.append(f"{i+1}. {agent}: {stats['win_rate']:.3f} win rate "
                         f"(Cooperation: {stats['average_cooperation_rate']:.3f})")
        report.append("")
        
        # Reasoning Analysis
        report.append("## Reasoning Pattern Analysis")
        for agent, stats in analysis['agent_performance'].items():
            complexity = stats['reasoning_complexity']
            report.append(f"### {agent}:")
            report.append(f"- Average reasoning length: {complexity['average_reasoning_length']:.1f} characters")
            report.append(f"- Cooperation focus rate: {complexity['cooperation_focus_rate']:.3f}")
            report.append(f"- Uncertainty rate: {complexity['uncertainty_rate']:.3f}")
            report.append("")
        
        # Performance Insights
        report.append("## Key Insights")
        
        # Find most cooperative vs most competitive
        most_cooperative = max(analysis['agent_performance'].items(), 
                             key=lambda x: x[1]['average_cooperation_rate'])
        most_competitive = min(analysis['agent_performance'].items(), 
                             key=lambda x: x[1]['average_cooperation_rate'])
        
        report.append(f"- Most cooperative agent: {most_cooperative[0]} "
                     f"({most_cooperative[1]['average_cooperation_rate']:.3f} cooperation rate)")
        report.append(f"- Most competitive agent: {most_competitive[0]} "
                     f"({most_competitive[1]['average_cooperation_rate']:.3f} cooperation rate)")
        
        # Find fastest vs slowest responder
        fastest = min(analysis['agent_performance'].items(), 
                     key=lambda x: x[1]['average_response_time_ms'])
        slowest = max(analysis['agent_performance'].items(), 
                     key=lambda x: x[1]['average_response_time_ms'])
        
        report.append(f"- Fastest responder: {fastest[0]} "
                     f"({fastest[1]['average_response_time_ms']:.0f}ms average)")
        report.append(f"- Slowest responder: {slowest[0]} "
                     f"({slowest[1]['average_response_time_ms']:.0f}ms average)")
        
        # Correlation analysis
        cooperation_rates = [stats['average_cooperation_rate'] for stats in analysis['agent_performance'].values()]
        win_rates = [stats['win_rate'] for stats in analysis['agent_performance'].values()]
        
        if len(cooperation_rates) > 1:
            correlation = pd.Series(cooperation_rates).corr(pd.Series(win_rates))
            report.append(f"- Cooperation-Win Rate Correlation: {correlation:.3f}")
        
        report.append("")
        
        # Recommendations
        report.append("## Research Recommendations")
        report.append("- Investigate the relationship between cooperation and success across different game types")
        report.append("- Analyze longer-term strategy evolution within individual agents")
        report.append("- Study the impact of opponent strategy on agent behavior adaptation")
        report.append("- Examine reasoning pattern complexity as a predictor of performance")
        
        # Save report
        report_content = "\n".join(report)
        report_file = self.results_dir / "conversation_analysis_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"💾 Research report saved to: {report_file}")


async def main():
    """Main analysis function."""
    
    print("🔍 Multi-Agent Conversation Analysis Tool")
    print("=" * 45)
    
    analyzer = ConversationAnalyzer()
    
    # Check if specific session ID provided
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        print(f"📝 Analyzing specific session: {session_id}")
        
        try:
            analysis = conversation_tracker.analyze_session(session_id)
            print(json.dumps(analysis, indent=2))
        except ValueError as e:
            print(f"❌ Error: {e}")
            return
    else:
        print("📊 Analyzing all conversation sessions...")
        
        # Comprehensive analysis
        analysis = analyzer.analyze_all_sessions()
        
        if analysis:
            # Generate visualizations
            analyzer.generate_cooperation_heatmap(analysis)
            analyzer.generate_performance_charts(analysis)
            
            # Export data
            analyzer.export_detailed_csv(analysis)
            
            # Generate report
            analyzer.generate_research_report(analysis)
            
            # Print summary
            print(f"\n✅ Analysis Complete!")
            print(f"📊 Analyzed {analysis['total_sessions']} sessions")
            print(f"👥 {len(analysis['agent_performance'])} unique agents")
            print(f"📁 Results saved to: {analyzer.results_dir}")
            
            # Show top performers
            print(f"\n🏆 Top Performing Agents:")
            sorted_agents = sorted(
                analysis['agent_performance'].items(),
                key=lambda x: (x[1]['win_rate'] + x[1]['average_cooperation_rate']) / 2,
                reverse=True
            )
            
            for i, (agent, stats) in enumerate(sorted_agents[:5]):
                combined_score = (stats['win_rate'] + stats['average_cooperation_rate']) / 2
                print(f"  {i+1}. {agent}: {combined_score:.3f} combined score "
                      f"(Win: {stats['win_rate']:.3f}, Coop: {stats['average_cooperation_rate']:.3f})")
        else:
            print("No conversation data found. Run some experiments first!")


if __name__ == "__main__":
    asyncio.run(main())