"""Specific agent implementations for different game theory strategies."""

import random
from typing import Dict, List, Optional, Any

from agents import Runner
from pydantic import Field

from .base_agent import BaseGameAgent
from .types import GameDecision, AgentAction
from ..utils.logger import get_logger


class CooperativeAgent(BaseGameAgent):
    """Agent that always tries to cooperate and share knowledge."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(
            name=name,
            strategy="always_cooperate",
            cooperation_threshold=0.2,  # Very willing to cooperate
            trust_threshold=0.3,       # Trusts easily
            **kwargs
        )
    
    async def make_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """Always choose to cooperate."""
        self.logger.info(f"Making cooperative decision in context: {game_context.get('game_type', 'unknown')}")
        
        # Prepare knowledge to share
        knowledge_to_share = []
        if 'opponent_id' in game_context:
            knowledge_to_share = self.get_knowledge_to_share(game_context['opponent_id'])
        
        return GameDecision(
            action=AgentAction.COOPERATE,
            reasoning="I believe in cooperation for mutual benefit. Sharing knowledge helps everyone succeed.",
            confidence=0.9,
            knowledge_to_share=knowledge_to_share[:3]  # Share up to 3 items
        )


class CompetitiveAgent(BaseGameAgent):
    """Agent that prioritizes individual gain and rarely cooperates."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(
            name=name,
            strategy="always_defect",
            cooperation_threshold=0.8,  # Rarely cooperates
            trust_threshold=0.7,       # Hard to gain trust
            **kwargs
        )
    
    async def make_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """Usually choose to defect, but may cooperate if trust is very high."""
        opponent_id = game_context.get('opponent_id')
        
        # Check if we have high trust with this opponent
        if opponent_id and self.get_trust_score(opponent_id) > self.cooperation_threshold:
            action = AgentAction.COOPERATE
            reasoning = "Despite my competitive nature, I trust this agent enough to cooperate this time."
            confidence = 0.6
        else:
            action = AgentAction.DEFECT
            reasoning = "I prioritize my own success. Competition drives excellence."
            confidence = 0.85
        
        self.logger.info(f"Competitive decision: {action.value} (trust={self.get_trust_score(opponent_id or '') if opponent_id else 'N/A'})")
        
        return GameDecision(
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            knowledge_to_share=[] if action == AgentAction.DEFECT else self.get_knowledge_to_share(opponent_id or '')[:1]
        )


class TitForTatAgent(BaseGameAgent):
    """Agent that implements the tit-for-tat strategy."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(
            name=name,
            strategy="tit_for_tat",
            cooperation_threshold=0.5,
            trust_threshold=0.5,
            **kwargs
        )
    
    async def make_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """Mirror the opponent's last action, starting with cooperation."""
        opponent_id = game_context.get('opponent_id', '')
        
        # Get opponent's last action
        last_opponent_action = None
        if opponent_history and len(opponent_history) > 0:
            last_opponent_action = opponent_history[-1]
        elif opponent_id:
            # Check our history with this opponent
            opponent_actions = [
                action for aid, action in self.state.cooperation_history
                if aid == opponent_id
            ]
            if opponent_actions:
                last_opponent_action = opponent_actions[-1]
        
        # Decide action based on tit-for-tat
        if last_opponent_action is None:
            # First interaction - start with cooperation
            action = AgentAction.COOPERATE
            reasoning = "First interaction with this agent - starting with cooperation as per tit-for-tat strategy."
            confidence = 0.8
        elif last_opponent_action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]:
            action = AgentAction.COOPERATE
            reasoning = f"Opponent cooperated last time ({last_opponent_action.value}), so I will cooperate in return."
            confidence = 0.9
        else:
            action = AgentAction.DEFECT
            reasoning = f"Opponent defected last time ({last_opponent_action.value}), so I will defect in return."
            confidence = 0.9
        
        self.logger.info(f"Tit-for-tat decision: {action.value} (opponent's last: {last_opponent_action})")
        
        knowledge_to_share = []
        if action == AgentAction.COOPERATE and opponent_id:
            knowledge_to_share = self.get_knowledge_to_share(opponent_id)[:2]
        
        return GameDecision(
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            knowledge_to_share=knowledge_to_share
        )


class AdaptiveAgent(BaseGameAgent):
    """Agent that adapts its strategy based on opponent behavior and success."""
    
    def __init__(self, name: str, **kwargs):
        self.adaptation_rate = kwargs.pop('adaptation_rate', 0.1)
        super().__init__(
            name=name,
            strategy="adaptive",
            cooperation_threshold=0.5,
            trust_threshold=0.5,
            **kwargs
        )
    
    async def make_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """Adapt strategy based on opponent behavior and past success."""
        opponent_id = game_context.get('opponent_id', '')
        
        # Analyze opponent's cooperation rate
        opponent_cooperation_rate = 0.5  # Default
        if opponent_id:
            opponent_cooperation_rate = self.get_cooperation_rate(opponent_id)
        
        # Analyze our own success rate
        recent_payoffs = self.state.payoff_history[-5:] if len(self.state.payoff_history) >= 5 else self.state.payoff_history
        avg_recent_payoff = sum(recent_payoffs) / len(recent_payoffs) if recent_payoffs else 2.5
        
        # Get trust score
        trust_score = self.get_trust_score(opponent_id) if opponent_id else 0.5
        
        # Adaptive decision logic
        cooperation_probability = (
            0.3 * opponent_cooperation_rate +
            0.3 * trust_score +
            0.2 * min(1.0, avg_recent_payoff / 5.0) +
            0.2 * self.state.reputation
        )
        
        # Add some randomness for exploration
        cooperation_probability += random.uniform(-0.1, 0.1)
        cooperation_probability = max(0.0, min(1.0, cooperation_probability))
        
        action = AgentAction.COOPERATE if cooperation_probability > 0.5 else AgentAction.DEFECT
        
        reasoning = (
            f"Adaptive decision based on: opponent cooperation rate={opponent_cooperation_rate:.2f}, "
            f"trust={trust_score:.2f}, recent success={avg_recent_payoff:.2f}, "
            f"reputation={self.state.reputation:.2f} → cooperation probability={cooperation_probability:.2f}"
        )
        
        self.logger.info(f"Adaptive decision: {action.value} (p_coop={cooperation_probability:.3f})")
        
        knowledge_to_share = []
        if action == AgentAction.COOPERATE and opponent_id:
            share_amount = max(1, int(3 * cooperation_probability))
            knowledge_to_share = self.get_knowledge_to_share(opponent_id)[:share_amount]
        
        return GameDecision(
            action=action,
            reasoning=reasoning,
            confidence=abs(cooperation_probability - 0.5) * 2,  # Higher confidence when probability is far from 0.5
            knowledge_to_share=knowledge_to_share
        )


class RandomAgent(BaseGameAgent):
    """Agent that makes random decisions."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(
            name=name,
            strategy="random",
            cooperation_threshold=0.5,
            trust_threshold=0.5,
            **kwargs
        )
    
    async def make_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """Make a random decision."""
        action = random.choice([AgentAction.COOPERATE, AgentAction.DEFECT])
        
        reasoning = f"Random decision: {action.value}"
        confidence = 0.5  # Always neutral confidence for random decisions
        
        self.logger.info(f"Random decision: {action.value}")
        
        knowledge_to_share = []
        if action == AgentAction.COOPERATE and 'opponent_id' in game_context:
            if random.random() > 0.5:  # 50% chance to share knowledge when cooperating
                knowledge_to_share = self.get_knowledge_to_share(game_context['opponent_id'])[:random.randint(1, 3)]
        
        return GameDecision(
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            knowledge_to_share=knowledge_to_share
        )