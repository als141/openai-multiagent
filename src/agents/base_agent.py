"""Base agent class for game theory multi-agent system."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

try:
    from openai_agents import Agent
except ImportError:
    # Fallback if OpenAI agents not available
    class Agent:
        def __init__(self, name: str, instructions: str = "", **kwargs):
            self.name = name
            self.instructions = instructions

from .types import AgentAction, GameDecision
from ..utils.logger import get_logger


@dataclass
class AgentState:
    """State information for an agent."""
    trust_scores: Dict[str, float] = field(default_factory=dict)
    knowledge_base: List[str] = field(default_factory=list)
    cooperation_history: List[Tuple[str, AgentAction]] = field(default_factory=list)
    payoff_history: List[float] = field(default_factory=list)
    reputation: float = 0.5
    
    def update_trust(self, agent_id: str, cooperation: bool, decay_rate: float = 0.1) -> None:
        """Update trust score for another agent."""
        if agent_id not in self.trust_scores:
            self.trust_scores[agent_id] = 0.5
        
        if cooperation:
            self.trust_scores[agent_id] = min(1.0, self.trust_scores[agent_id] + 0.1)
        else:
            self.trust_scores[agent_id] = max(0.0, self.trust_scores[agent_id] - 0.2)
        
        # Apply decay to all trust scores
        for agent in self.trust_scores:
            if agent != agent_id:
                self.trust_scores[agent] *= (1.0 - decay_rate)




class BaseGameAgent(Agent, ABC):
    """Base class for game theory agents with extended capabilities."""
    
    def __init__(
        self,
        name: str,
        strategy: str,
        instructions: Optional[str] = None,
        cooperation_threshold: float = 0.5,
        trust_threshold: float = 0.5,
        **kwargs
    ):
        """Initialize a game theory agent.
        
        Args:
            name: Agent name
            strategy: Strategy type (e.g., 'tit_for_tat', 'always_cooperate')
            instructions: Custom instructions for the agent
            cooperation_threshold: Threshold for cooperation decisions
            trust_threshold: Threshold for trusting other agents
        """
        # Store attributes first
        self.name = name
        self.strategy = strategy
        self.cooperation_threshold = cooperation_threshold
        self.trust_threshold = trust_threshold
        self.state = AgentState()
        self.logger = get_logger(f"agent.{name}")
        
        # Build instructions based on strategy
        if instructions is None:
            instructions = self._build_instructions()
        
        super().__init__(
            name=name,
            instructions=instructions,
            **kwargs
        )
    
    def _build_instructions(self) -> str:
        """Build agent instructions based on strategy."""
        base_instructions = f"""
        You are a game theory agent named {self.name} with a {self.strategy} strategy.
        
        Your role is to make strategic decisions in multi-agent interactions while considering:
        1. Your past experiences with other agents
        2. Trust levels and reputation scores
        3. Long-term vs short-term benefits
        4. The potential for knowledge sharing and cooperation
        
        When making decisions, you should:
        - Analyze the current situation carefully
        - Consider your trust in other agents
        - Evaluate potential payoffs
        - Decide whether to cooperate or compete
        - Determine if knowledge sharing is beneficial
        
        Always provide clear reasoning for your decisions and express your confidence level.
        """
        
        strategy_specific = {
            "tit_for_tat": "You mirror the last action of your opponent - cooperate if they cooperated, defect if they defected. Start with cooperation.",
            "always_cooperate": "You always choose to cooperate and share knowledge, believing in the power of collaboration.",
            "always_defect": "You always choose to defect and withhold knowledge, prioritizing individual gain.",
            "adaptive": "You adapt your strategy based on the behavior patterns of other agents and the success of your past decisions.",
            "random": "You make random decisions with equal probability of cooperation and defection."
        }
        
        return base_instructions + "\n\n" + strategy_specific.get(self.strategy, "")
    
    @abstractmethod
    async def make_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """Make a decision in a game context.
        
        Args:
            game_context: Current game state and context
            opponent_history: History of opponent actions
            
        Returns:
            GameDecision with action and reasoning
        """
        pass
    
    async def make_decision_with_tracking(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None,
        session_id: Optional[str] = None,
        round_number: int = 1
    ) -> Tuple[GameDecision, float, str]:
        """Make a decision with conversation tracking.
        
        Returns:
            Tuple of (GameDecision, response_time_ms, detailed_reasoning)
        """
        start_time = time.time()
        
        # Get the basic decision
        decision = await self.make_decision(game_context, opponent_history)
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Build detailed reasoning process
        detailed_reasoning = self._build_detailed_reasoning(
            game_context, opponent_history, decision
        )
        
        # Record in conversation tracker if session provided
        if session_id:
            from ..utils.conversation_tracker import conversation_tracker
            
            opponent_last_action = opponent_history[-1] if opponent_history else None
            trust_level = 0.5
            
            if "opponent_id" in game_context:
                trust_level = self.get_trust_score(game_context["opponent_id"])
            
            conversation_tracker.record_turn(
                session_id=session_id,
                agent_name=self.name,
                round_number=round_number,
                context=game_context,
                decision=decision,
                reasoning_process=detailed_reasoning,
                response_time_ms=response_time_ms,
                opponent_last_action=opponent_last_action,
                trust_level=trust_level
            )
        
        return decision, response_time_ms, detailed_reasoning
    
    def _build_detailed_reasoning(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]],
        decision: GameDecision
    ) -> str:
        """Build detailed reasoning process for analysis."""
        reasoning_parts = []
        
        # Context analysis
        reasoning_parts.append(f"CONTEXT ANALYSIS:")
        reasoning_parts.append(f"- Game type: {game_context.get('game_type', 'unknown')}")
        reasoning_parts.append(f"- Round: {game_context.get('round_number', 'unknown')}")
        
        if "opponent_id" in game_context:
            opponent_id = game_context["opponent_id"]
            trust_score = self.get_trust_score(opponent_id)
            coop_rate = self.get_cooperation_rate(opponent_id)
            reasoning_parts.append(f"- Opponent: {opponent_id}")
            reasoning_parts.append(f"- Trust level with opponent: {trust_score:.3f}")
            reasoning_parts.append(f"- Historical cooperation rate with opponent: {coop_rate:.3f}")
        
        # Strategy analysis
        reasoning_parts.append(f"\nSTRATEGY ANALYSIS:")
        reasoning_parts.append(f"- My strategy: {self.strategy}")
        reasoning_parts.append(f"- Cooperation threshold: {self.cooperation_threshold}")
        reasoning_parts.append(f"- Trust threshold: {self.trust_threshold}")
        
        # Opponent history analysis
        if opponent_history:
            reasoning_parts.append(f"\nOPPONENT HISTORY ANALYSIS:")
            reasoning_parts.append(f"- Total interactions: {len(opponent_history)}")
            cooperative_count = sum(
                1 for action in opponent_history
                if action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
            )
            reasoning_parts.append(f"- Opponent cooperation rate: {cooperative_count / len(opponent_history):.3f}")
            if len(opponent_history) > 0:
                reasoning_parts.append(f"- Last opponent action: {opponent_history[-1].value}")
        
        # Personal state analysis
        reasoning_parts.append(f"\nPERSONAL STATE ANALYSIS:")
        reasoning_parts.append(f"- My reputation: {self.state.reputation:.3f}")
        reasoning_parts.append(f"- My overall cooperation rate: {self.get_cooperation_rate():.3f}")
        reasoning_parts.append(f"- Knowledge base size: {len(self.state.knowledge_base)}")
        
        if self.state.payoff_history:
            avg_payoff = sum(self.state.payoff_history) / len(self.state.payoff_history)
            reasoning_parts.append(f"- Average historical payoff: {avg_payoff:.3f}")
        
        # Decision reasoning
        reasoning_parts.append(f"\nDECISION REASONING:")
        reasoning_parts.append(f"- Chosen action: {decision.action.value}")
        reasoning_parts.append(f"- Confidence: {decision.confidence:.3f}")
        reasoning_parts.append(f"- Primary reasoning: {decision.reasoning}")
        
        if decision.knowledge_to_share:
            reasoning_parts.append(f"- Knowledge to share: {len(decision.knowledge_to_share)} items")
        
        return "\n".join(reasoning_parts)
    
    def update_state(
        self,
        opponent_id: str,
        opponent_action: AgentAction,
        payoff: float,
        my_action: AgentAction
    ) -> None:
        """Update agent state after a game round.
        
        Args:
            opponent_id: ID of the opponent
            opponent_action: Action taken by opponent
            payoff: Payoff received in this round
            my_action: Action taken by this agent
        """
        # Update trust based on opponent's action
        cooperation = opponent_action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
        self.state.update_trust(opponent_id, cooperation)
        
        # Update history
        self.state.cooperation_history.append((opponent_id, opponent_action))
        self.state.payoff_history.append(payoff)
        
        # Update reputation based on performance
        if len(self.state.payoff_history) > 0:
            avg_payoff = sum(self.state.payoff_history[-10:]) / min(10, len(self.state.payoff_history))
            self.state.reputation = max(0.0, min(1.0, avg_payoff / 5.0))  # Normalize to 0-1
        
        self.logger.info(
            f"Updated state: trust_scores={self.state.trust_scores}, "
            f"reputation={self.state.reputation:.3f}, "
            f"avg_payoff={sum(self.state.payoff_history[-5:]) / min(5, len(self.state.payoff_history)):.3f}"
        )
    
    def get_trust_score(self, agent_id: str) -> float:
        """Get trust score for another agent."""
        return self.state.trust_scores.get(agent_id, 0.5)
    
    def get_cooperation_rate(self, agent_id: Optional[str] = None) -> float:
        """Get cooperation rate with specific agent or overall."""
        if not self.state.cooperation_history:
            return 0.5
        
        if agent_id:
            agent_actions = [
                action for aid, action in self.state.cooperation_history
                if aid == agent_id
            ]
        else:
            agent_actions = [action for _, action in self.state.cooperation_history]
        
        if not agent_actions:
            return 0.5
        
        cooperative_actions = sum(
            1 for action in agent_actions
            if action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
        )
        
        return cooperative_actions / len(agent_actions)
    
    def share_knowledge(self, knowledge: List[str]) -> None:
        """Add knowledge to the agent's knowledge base."""
        for item in knowledge:
            if item not in self.state.knowledge_base:
                self.state.knowledge_base.append(item)
                self.logger.info(f"Added knowledge: {item}")
    
    def get_knowledge_to_share(self, requester_id: str) -> List[str]:
        """Determine what knowledge to share with another agent."""
        trust_score = self.get_trust_score(requester_id)
        
        if trust_score < self.trust_threshold:
            return []
        
        # Share knowledge based on trust level
        knowledge_to_share = []
        max_items = max(1, int(len(self.state.knowledge_base) * trust_score))
        
        for item in self.state.knowledge_base[:max_items]:
            knowledge_to_share.append(item)
        
        return knowledge_to_share
    
    def __str__(self) -> str:
        return f"{self.name} ({self.strategy})"
    
    def __repr__(self) -> str:
        return f"BaseGameAgent(name='{self.name}', strategy='{self.strategy}')"