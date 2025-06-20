"""Game implementations for multi-agent interactions."""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..agents.base_agent import BaseGameAgent

from ..agents.types import AgentAction, GameDecision
from .payoff import PayoffCalculator, RewardMatrix
from ..utils.logger import get_logger


class GameType(Enum):
    """Types of games available."""
    PRISONERS_DILEMMA = "prisoners_dilemma"
    PUBLIC_GOODS = "public_goods"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    COORDINATION = "coordination"


@dataclass
class GameResult:
    """Result of a game round or full game."""
    game_type: GameType
    participants: List[str]
    rounds: int
    actions_history: List[Tuple[str, AgentAction]]
    payoffs: Dict[str, float]
    cooperation_rates: Dict[str, float]
    winner: Optional[str] = None
    additional_metrics: Dict[str, Any] = None


class BaseGame(ABC):
    """Base class for all games."""
    
    def __init__(self, name: str, game_type: GameType):
        self.name = name
        self.game_type = game_type
        self.logger = get_logger(f"game.{name}")
        self.round_number = 0
        self.results_history: List[GameResult] = []
    
    @abstractmethod
    async def play_round(
        self,
        agents: List["BaseGameAgent"],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Play a single round of the game."""
        pass
    
    @abstractmethod
    async def play_full_game(
        self,
        agents: List["BaseGameAgent"],
        num_rounds: int,
        context: Optional[Dict[str, Any]] = None
    ) -> GameResult:
        """Play a complete game with multiple rounds."""
        pass
    
    def reset(self) -> None:
        """Reset game state."""
        self.round_number = 0
        self.results_history.clear()


class PrisonersDilemma(BaseGame):
    """Implementation of the classic Prisoner's Dilemma game."""
    
    def __init__(self, reward_matrix: Optional[RewardMatrix] = None):
        super().__init__("Prisoner's Dilemma", GameType.PRISONERS_DILEMMA)
        self.reward_matrix = reward_matrix or RewardMatrix.prisoner_dilemma()
        self.payoff_calculator = PayoffCalculator(self.reward_matrix)
        self.game_history: List[Tuple[AgentAction, AgentAction]] = []
    
    async def play_round(
        self,
        agents: List["BaseGameAgent"],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Play a single round of Prisoner's Dilemma between two agents."""
        if len(agents) != 2:
            raise ValueError("Prisoner's Dilemma requires exactly 2 agents")
        
        agent1, agent2 = agents
        self.round_number += 1
        
        # Check if conversation tracking is enabled
        session_id = context.get("session_id") if context else None
        enable_tracking = context.get("enable_conversation_tracking", False) if context else False
        
        # Prepare context for each agent
        context1 = {
            "game_type": self.game_type.value,
            "round_number": self.round_number,
            "opponent_id": agent2.name,
            "reward_matrix": self.reward_matrix,
            **(context or {})
        }
        
        context2 = {
            "game_type": self.game_type.value,
            "round_number": self.round_number,
            "opponent_id": agent1.name,
            "reward_matrix": self.reward_matrix,
            **(context or {})
        }
        
        # Get opponent histories for decision making
        agent1_history = [action for action, _ in self.game_history]
        agent2_history = [action for _, action in self.game_history]
        
        # Get decisions from both agents simultaneously
        try:
            if enable_tracking and session_id:
                # Use tracked decision making
                decision1_task = agent1.make_decision_with_tracking(
                    context1, agent2_history, session_id, self.round_number
                )
                decision2_task = agent2.make_decision_with_tracking(
                    context2, agent1_history, session_id, self.round_number
                )
                
                (decision1, time1, reasoning1), (decision2, time2, reasoning2) = await asyncio.gather(
                    decision1_task, decision2_task
                )
                
                tracking_info = {
                    "detailed_reasoning": {
                        agent1.name: reasoning1,
                        agent2.name: reasoning2
                    },
                    "response_times_ms": {
                        agent1.name: time1,
                        agent2.name: time2
                    }
                }
            else:
                # Standard decision making
                decision1_task = agent1.make_decision(context1, agent2_history)
                decision2_task = agent2.make_decision(context2, agent1_history)
                
                decision1, decision2 = await asyncio.gather(decision1_task, decision2_task)
                tracking_info = {}
            
        except Exception as e:
            self.logger.error(f"Error getting agent decisions: {e}")
            # Default to defection if there's an error
            decision1 = GameDecision(action=AgentAction.DEFECT, reasoning="Error fallback", confidence=0.0)
            decision2 = GameDecision(action=AgentAction.DEFECT, reasoning="Error fallback", confidence=0.0)
            tracking_info = {}
        
        action1, action2 = decision1.action, decision2.action
        
        # Calculate payoffs
        payoff1, payoff2 = self.payoff_calculator.calculate_round_payoffs(action1, action2)
        
        # Update agent states
        agent1.update_state(agent2.name, action2, payoff1, action1)
        agent2.update_state(agent1.name, action1, payoff2, action2)
        
        # Handle knowledge sharing
        if decision1.knowledge_to_share:
            agent2.share_knowledge(decision1.knowledge_to_share)
        if decision2.knowledge_to_share:
            agent1.share_knowledge(decision2.knowledge_to_share)
        
        # Record history
        self.game_history.append((action1, action2))
        
        round_result = {
            "round": self.round_number,
            "actions": {agent1.name: action1, agent2.name: action2},
            "decisions": {agent1.name: decision1, agent2.name: decision2},
            "payoffs": {agent1.name: payoff1, agent2.name: payoff2},
            "knowledge_shared": {
                agent1.name: decision1.knowledge_to_share or [],
                agent2.name: decision2.knowledge_to_share or []
            },
            **tracking_info
        }
        
        self.logger.info(
            f"Round {self.round_number}: {agent1.name}={action1.value} ({payoff1}), "
            f"{agent2.name}={action2.value} ({payoff2})"
        )
        
        return round_result
    
    async def play_full_game(
        self,
        agents: List["BaseGameAgent"],
        num_rounds: int,
        context: Optional[Dict[str, Any]] = None
    ) -> GameResult:
        """Play a complete Prisoner's Dilemma game."""
        if len(agents) != 2:
            raise ValueError("Prisoner's Dilemma requires exactly 2 agents")
        
        self.reset()
        agent1, agent2 = agents
        round_results = []
        
        self.logger.info(f"Starting Prisoner's Dilemma: {agent1.name} vs {agent2.name} ({num_rounds} rounds)")
        
        # Play all rounds
        for _ in range(num_rounds):
            round_result = await self.play_round(agents, context)
            round_results.append(round_result)
        
        # Calculate final statistics
        total_payoffs = {agent1.name: 0.0, agent2.name: 0.0}
        actions_history = []
        
        for round_result in round_results:
            for agent_name, payoff in round_result["payoffs"].items():
                total_payoffs[agent_name] += payoff
            
            for agent_name, action in round_result["actions"].items():
                actions_history.append((agent_name, action))
        
        # Calculate cooperation rates
        cooperation_rates = {}
        for agent in agents:
            agent_actions = [
                action for name, action in actions_history
                if name == agent.name
            ]
            cooperation_rates[agent.name] = self.payoff_calculator.calculate_cooperation_rate(agent_actions)
        
        # Determine winner
        winner = max(total_payoffs.keys(), key=lambda k: total_payoffs[k])
        if total_payoffs[agent1.name] == total_payoffs[agent2.name]:
            winner = None
        
        # Additional metrics
        game_analysis = self.payoff_calculator.analyze_game_outcomes(
            self.game_history, agent1.name, agent2.name
        )
        
        result = GameResult(
            game_type=self.game_type,
            participants=[agent.name for agent in agents],
            rounds=num_rounds,
            actions_history=actions_history,
            payoffs=total_payoffs,
            cooperation_rates=cooperation_rates,
            winner=winner,
            additional_metrics=game_analysis
        )
        
        self.results_history.append(result)
        
        self.logger.info(
            f"Game finished. Winner: {winner or 'Tie'}. "
            f"Payoffs: {total_payoffs}. "
            f"Cooperation rates: {cooperation_rates}"
        )
        
        return result


class PublicGoodsGame(BaseGame):
    """Implementation of the Public Goods Game."""
    
    def __init__(self, multiplier: float = 2.0, endowment: float = 10.0):
        super().__init__("Public Goods Game", GameType.PUBLIC_GOODS)
        self.multiplier = multiplier
        self.endowment = endowment
        self.contribution_history: List[Dict[str, float]] = []
    
    async def play_round(
        self,
        agents: List["BaseGameAgent"],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Play a single round of Public Goods Game."""
        self.round_number += 1
        contributions = {}
        decisions = {}
        
        # Get contribution decisions from all agents
        for agent in agents:
            game_context = {
                "game_type": self.game_type.value,
                "round_number": self.round_number,
                "endowment": self.endowment,
                "multiplier": self.multiplier,
                "num_players": len(agents),
                "other_agents": [a.name for a in agents if a != agent],
                **(context or {})
            }
            
            try:
                decision = await agent.make_decision(game_context)
                # In public goods, cooperation means contributing to public pool
                contribution = self.endowment * 0.8 if decision.action == AgentAction.COOPERATE else self.endowment * 0.2
                contributions[agent.name] = contribution
                decisions[agent.name] = decision
            except Exception as e:
                self.logger.error(f"Error getting decision from {agent.name}: {e}")
                contributions[agent.name] = 0.0
                decisions[agent.name] = GameDecision(
                    action=AgentAction.DEFECT,
                    reasoning="Error fallback",
                    confidence=0.0
                )
        
        # Calculate payoffs
        total_contributions = sum(contributions.values())
        public_pool = total_contributions * self.multiplier
        equal_share = public_pool / len(agents)
        
        payoffs = {}
        for agent_name, contribution in contributions.items():
            payoffs[agent_name] = (self.endowment - contribution) + equal_share
        
        # Update agent states
        for agent in agents:
            # For public goods, we update based on average cooperation of others
            other_agents_cooperation = sum(
                1 for name, contrib in contributions.items()
                if name != agent.name and contrib > self.endowment * 0.5
            )
            avg_cooperation = other_agents_cooperation / max(1, len(agents) - 1)
            
            # Simulate updating trust with "average other"
            agent.update_state("public", 
                             AgentAction.COOPERATE if avg_cooperation > 0.5 else AgentAction.DEFECT,
                             payoffs[agent.name],
                             decisions[agent.name].action)
        
        self.contribution_history.append(contributions.copy())
        
        round_result = {
            "round": self.round_number,
            "contributions": contributions,
            "total_contributions": total_contributions,
            "public_pool": public_pool,
            "payoffs": payoffs,
            "decisions": decisions
        }
        
        self.logger.info(
            f"Round {self.round_number}: Total contributions={total_contributions:.2f}, "
            f"Average payoff={sum(payoffs.values()) / len(payoffs):.2f}"
        )
        
        return round_result
    
    async def play_full_game(
        self,
        agents: List["BaseGameAgent"],
        num_rounds: int,
        context: Optional[Dict[str, Any]] = None
    ) -> GameResult:
        """Play a complete Public Goods Game."""
        self.reset()
        round_results = []
        
        self.logger.info(f"Starting Public Goods Game with {len(agents)} agents ({num_rounds} rounds)")
        
        for _ in range(num_rounds):
            round_result = await self.play_round(agents, context)
            round_results.append(round_result)
        
        # Calculate final statistics
        total_payoffs = {agent.name: 0.0 for agent in agents}
        actions_history = []
        
        for round_result in round_results:
            for agent_name, payoff in round_result["payoffs"].items():
                total_payoffs[agent_name] += payoff
            
            for agent_name, decision in round_result["decisions"].items():
                actions_history.append((agent_name, decision.action))
        
        # Calculate cooperation rates (contribution rates)
        cooperation_rates = {}
        for agent in agents:
            agent_contributions = []
            for round_result in round_results:
                contrib_rate = round_result["contributions"][agent.name] / self.endowment
                cooperation_rates[agent.name] = cooperation_rates.get(agent.name, 0) + contrib_rate
            cooperation_rates[agent.name] /= num_rounds
        
        winner = max(total_payoffs.keys(), key=lambda k: total_payoffs[k])
        
        result = GameResult(
            game_type=self.game_type,
            participants=[agent.name for agent in agents],
            rounds=num_rounds,
            actions_history=actions_history,
            payoffs=total_payoffs,
            cooperation_rates=cooperation_rates,
            winner=winner,
            additional_metrics={
                "total_welfare": sum(total_payoffs.values()),
                "average_contribution_rate": sum(cooperation_rates.values()) / len(cooperation_rates),
                "contribution_history": self.contribution_history
            }
        )
        
        self.results_history.append(result)
        return result


class KnowledgeSharingGame(BaseGame):
    """Game focused on knowledge sharing and trust building."""
    
    def __init__(self, knowledge_value: float = 2.0, sharing_cost: float = 0.5):
        super().__init__("Knowledge Sharing Game", GameType.KNOWLEDGE_SHARING)
        self.knowledge_value = knowledge_value
        self.sharing_cost = sharing_cost
        self.knowledge_pool = [
            "Advanced algorithm optimization",
            "Market trend analysis",
            "Resource allocation strategy",
            "Communication protocol",
            "Problem-solving framework",
            "Collaboration technique",
            "Decision-making model",
            "Trust evaluation method"
        ]
    
    async def play_round(
        self,
        agents: List["BaseGameAgent"],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Play a round of knowledge sharing."""
        self.round_number += 1
        decisions = {}
        knowledge_shared = {}
        
        # Each agent gets a piece of knowledge to potentially share
        for i, agent in enumerate(agents):
            if len(agent.state.knowledge_base) < 3:  # Give knowledge if they have little
                new_knowledge = f"Knowledge_{self.round_number}_{i}: {random.choice(self.knowledge_pool)}"
                agent.share_knowledge([new_knowledge])
        
        # Get sharing decisions
        for agent in agents:
            game_context = {
                "game_type": self.game_type.value,
                "round_number": self.round_number,
                "knowledge_value": self.knowledge_value,
                "sharing_cost": self.sharing_cost,
                "other_agents": [a.name for a in agents if a != agent],
                **(context or {})
            }
            
            try:
                decision = await agent.make_decision(game_context)
                decisions[agent.name] = decision
                knowledge_shared[agent.name] = decision.knowledge_to_share or []
            except Exception as e:
                self.logger.error(f"Error getting decision from {agent.name}: {e}")
                decisions[agent.name] = GameDecision(
                    action=AgentAction.WITHHOLD_KNOWLEDGE,
                    reasoning="Error fallback",
                    confidence=0.0
                )
                knowledge_shared[agent.name] = []
        
        # Calculate payoffs and distribute knowledge
        payoffs = {}
        knowledge_received = {agent.name: [] for agent in agents}
        
        for agent in agents:
            payoff = 0.0
            
            # Cost for sharing knowledge
            if knowledge_shared[agent.name]:
                payoff -= self.sharing_cost * len(knowledge_shared[agent.name])
            
            # Benefit from receiving knowledge
            for other_agent in agents:
                if other_agent.name != agent.name and knowledge_shared[other_agent.name]:
                    # Check trust level to determine if knowledge is actually shared
                    if other_agent.get_trust_score(agent.name) > 0.3:
                        shared_knowledge = knowledge_shared[other_agent.name]
                        knowledge_received[agent.name].extend(shared_knowledge)
                        payoff += self.knowledge_value * len(shared_knowledge)
            
            payoffs[agent.name] = payoff
        
        # Actually transfer knowledge between agents
        for agent in agents:
            if knowledge_received[agent.name]:
                agent.share_knowledge(knowledge_received[agent.name])
        
        # Update agent states
        for agent in agents:
            for other_agent in agents:
                if other_agent.name != agent.name:
                    other_shared = len(knowledge_shared[other_agent.name]) > 0
                    action = AgentAction.SHARE_KNOWLEDGE if other_shared else AgentAction.WITHHOLD_KNOWLEDGE
                    agent.update_state(other_agent.name, action, payoffs[agent.name], decisions[agent.name].action)
        
        round_result = {
            "round": self.round_number,
            "decisions": decisions,
            "knowledge_shared": knowledge_shared,
            "knowledge_received": knowledge_received,
            "payoffs": payoffs
        }
        
        self.logger.info(
            f"Round {self.round_number}: Knowledge pieces shared={sum(len(k) for k in knowledge_shared.values())}"
        )
        
        return round_result
    
    async def play_full_game(
        self,
        agents: List["BaseGameAgent"],
        num_rounds: int,
        context: Optional[Dict[str, Any]] = None
    ) -> GameResult:
        """Play a complete Knowledge Sharing Game."""
        self.reset()
        round_results = []
        
        self.logger.info(f"Starting Knowledge Sharing Game with {len(agents)} agents ({num_rounds} rounds)")
        
        for _ in range(num_rounds):
            round_result = await self.play_round(agents, context)
            round_results.append(round_result)
        
        # Calculate final statistics
        total_payoffs = {agent.name: 0.0 for agent in agents}
        actions_history = []
        
        for round_result in round_results:
            for agent_name, payoff in round_result["payoffs"].items():
                total_payoffs[agent_name] += payoff
            
            for agent_name, decision in round_result["decisions"].items():
                actions_history.append((agent_name, decision.action))
        
        # Calculate sharing rates
        cooperation_rates = {}
        for agent in agents:
            sharing_count = 0
            total_rounds = 0
            for round_result in round_results:
                if agent.name in round_result["knowledge_shared"]:
                    total_rounds += 1
                    if round_result["knowledge_shared"][agent.name]:
                        sharing_count += 1
            cooperation_rates[agent.name] = sharing_count / max(1, total_rounds)
        
        winner = max(total_payoffs.keys(), key=lambda k: total_payoffs[k])
        
        # Additional metrics
        total_knowledge_shared = sum(
            len(knowledge) 
            for round_result in round_results
            for knowledge in round_result["knowledge_shared"].values()
        )
        
        final_knowledge_counts = {
            agent.name: len(agent.state.knowledge_base)
            for agent in agents
        }
        
        result = GameResult(
            game_type=self.game_type,
            participants=[agent.name for agent in agents],
            rounds=num_rounds,
            actions_history=actions_history,
            payoffs=total_payoffs,
            cooperation_rates=cooperation_rates,
            winner=winner,
            additional_metrics={
                "total_knowledge_shared": total_knowledge_shared,
                "final_knowledge_counts": final_knowledge_counts,
                "average_sharing_rate": sum(cooperation_rates.values()) / len(cooperation_rates)
            }
        )
        
        self.results_history.append(result)
        return result