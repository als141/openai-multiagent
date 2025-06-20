"""Type definitions for agents."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class AgentAction(Enum):
    """Possible actions an agent can take in a game."""
    COOPERATE = "cooperate"
    DEFECT = "defect"
    SHARE_KNOWLEDGE = "share_knowledge"
    WITHHOLD_KNOWLEDGE = "withhold_knowledge"


class GameDecision(BaseModel):
    """Structured output for agent decisions."""
    action: AgentAction
    reasoning: str
    confidence: float
    knowledge_to_share: Optional[List[str]] = None