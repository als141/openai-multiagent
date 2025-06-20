"""Payoff calculation and reward matrix management."""

import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

import numpy as np

from ..agents.types import AgentAction


@dataclass
class RewardMatrix:
    """Reward matrix for two-player games."""
    cooperate_cooperate: Tuple[float, float]
    cooperate_defect: Tuple[float, float]
    defect_cooperate: Tuple[float, float]
    defect_defect: Tuple[float, float]
    
    @classmethod
    def prisoner_dilemma(cls) -> 'RewardMatrix':
        """Create a standard prisoner's dilemma reward matrix."""
        return cls(
            cooperate_cooperate=(3, 3),  # Mutual cooperation
            cooperate_defect=(0, 5),     # Sucker's payoff / Temptation
            defect_cooperate=(5, 0),     # Temptation / Sucker's payoff
            defect_defect=(1, 1)         # Mutual defection
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, List[float]]) -> 'RewardMatrix':
        """Create reward matrix from dictionary."""
        return cls(
            cooperate_cooperate=tuple(data["cooperate_cooperate"]),
            cooperate_defect=tuple(data["cooperate_defect"]),
            defect_cooperate=tuple(data["defect_cooperate"]),
            defect_defect=tuple(data["defect_defect"])
        )
    
    @classmethod
    def from_json_string(cls, json_str: str) -> 'RewardMatrix':
        """Create reward matrix from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_payoffs(self, action1: AgentAction, action2: AgentAction) -> Tuple[float, float]:
        """Get payoffs for both players given their actions."""
        coop1 = action1 in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
        coop2 = action2 in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
        
        if coop1 and coop2:
            return self.cooperate_cooperate
        elif coop1 and not coop2:
            return self.cooperate_defect
        elif not coop1 and coop2:
            return self.defect_cooperate
        else:
            return self.defect_defect
    
    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array format [player1_payoffs, player2_payoffs]."""
        # Rows: Player 1 actions (Cooperate, Defect)
        # Cols: Player 2 actions (Cooperate, Defect)
        player1_payoffs = np.array([
            [self.cooperate_cooperate[0], self.cooperate_defect[0]],
            [self.defect_cooperate[0], self.defect_defect[0]]
        ])
        
        player2_payoffs = np.array([
            [self.cooperate_cooperate[1], self.defect_cooperate[1]],
            [self.cooperate_defect[1], self.defect_defect[1]]
        ])
        
        return np.array([player1_payoffs, player2_payoffs])


class PayoffCalculator:
    """Calculator for various game theory payoffs and metrics."""
    
    def __init__(self, reward_matrix: RewardMatrix):
        self.reward_matrix = reward_matrix
        
    def calculate_round_payoffs(
        self,
        agent1_action: AgentAction,
        agent2_action: AgentAction
    ) -> Tuple[float, float]:
        """Calculate payoffs for a single round."""
        return self.reward_matrix.get_payoffs(agent1_action, agent2_action)
    
    def calculate_cumulative_payoffs(
        self,
        history: List[Tuple[AgentAction, AgentAction]]
    ) -> Tuple[float, float]:
        """Calculate cumulative payoffs over multiple rounds."""
        total1, total2 = 0.0, 0.0
        
        for action1, action2 in history:
            payoff1, payoff2 = self.calculate_round_payoffs(action1, action2)
            total1 += payoff1
            total2 += payoff2
        
        return total1, total2
    
    def calculate_average_payoffs(
        self,
        history: List[Tuple[AgentAction, AgentAction]]
    ) -> Tuple[float, float]:
        """Calculate average payoffs over multiple rounds."""
        if not history:
            return 0.0, 0.0
        
        total1, total2 = self.calculate_cumulative_payoffs(history)
        return total1 / len(history), total2 / len(history)
    
    def calculate_cooperation_rate(
        self,
        actions: List[AgentAction]
    ) -> float:
        """Calculate cooperation rate for an agent."""
        if not actions:
            return 0.0
        
        cooperative_actions = sum(
            1 for action in actions
            if action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
        )
        
        return cooperative_actions / len(actions)
    
    def calculate_mutual_cooperation_rate(
        self,
        history: List[Tuple[AgentAction, AgentAction]]
    ) -> float:
        """Calculate rate of mutual cooperation."""
        if not history:
            return 0.0
        
        mutual_cooperation = sum(
            1 for action1, action2 in history
            if (action1 in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE] and
                action2 in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE])
        )
        
        return mutual_cooperation / len(history)
    
    def calculate_exploitation_rate(
        self,
        history: List[Tuple[AgentAction, AgentAction]],
        player: int = 1
    ) -> float:
        """Calculate how often a player exploits the other (defects when other cooperates)."""
        if not history:
            return 0.0
        
        exploitation_count = 0
        for action1, action2 in history:
            if player == 1:
                my_action, other_action = action1, action2
            else:
                my_action, other_action = action2, action1
            
            my_defects = my_action in [AgentAction.DEFECT, AgentAction.WITHHOLD_KNOWLEDGE]
            other_cooperates = other_action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
            
            if my_defects and other_cooperates:
                exploitation_count += 1
        
        return exploitation_count / len(history)
    
    def calculate_pareto_efficiency(
        self,
        history: List[Tuple[AgentAction, AgentAction]]
    ) -> float:
        """Calculate Pareto efficiency of the outcomes."""
        if not history:
            return 0.0
        
        # Count outcomes that are Pareto optimal (mutual cooperation in prisoner's dilemma)
        pareto_optimal_count = sum(
            1 for action1, action2 in history
            if (action1 in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE] and
                action2 in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE])
        )
        
        return pareto_optimal_count / len(history)
    
    def analyze_game_outcomes(
        self,
        history: List[Tuple[AgentAction, AgentAction]],
        agent1_name: str = "Agent1",
        agent2_name: str = "Agent2"
    ) -> Dict[str, Any]:
        """Comprehensive analysis of game outcomes."""
        if not history:
            return {"error": "No game history provided"}
        
        # Calculate payoffs
        total1, total2 = self.calculate_cumulative_payoffs(history)
        avg1, avg2 = self.calculate_average_payoffs(history)
        
        # Extract individual action histories
        actions1 = [action1 for action1, _ in history]
        actions2 = [action2 for _, action2 in history]
        
        # Calculate cooperation rates
        coop_rate1 = self.calculate_cooperation_rate(actions1)
        coop_rate2 = self.calculate_cooperation_rate(actions2)
        mutual_coop_rate = self.calculate_mutual_cooperation_rate(history)
        
        # Calculate exploitation rates
        exploit_rate1 = self.calculate_exploitation_rate(history, player=1)
        exploit_rate2 = self.calculate_exploitation_rate(history, player=2)
        
        # Calculate efficiency
        pareto_efficiency = self.calculate_pareto_efficiency(history)
        
        return {
            "game_summary": {
                "total_rounds": len(history),
                "mutual_cooperation_rate": mutual_coop_rate,
                "pareto_efficiency": pareto_efficiency
            },
            agent1_name: {
                "total_payoff": total1,
                "average_payoff": avg1,
                "cooperation_rate": coop_rate1,
                "exploitation_rate": exploit_rate1
            },
            agent2_name: {
                "total_payoff": total2,
                "average_payoff": avg2,
                "cooperation_rate": coop_rate2,
                "exploitation_rate": exploit_rate2
            },
            "comparative_analysis": {
                "payoff_difference": total1 - total2,
                "cooperation_difference": coop_rate1 - coop_rate2,
                "winner": agent1_name if total1 > total2 else agent2_name if total2 > total1 else "Tie"
            }
        }