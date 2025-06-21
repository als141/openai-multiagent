"""Knowledge exchange system for multi-agent interactions."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class KnowledgeType(Enum):
    """Types of knowledge"""
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    STRATEGIC = "strategic"
    EXPERIENTIAL = "experiential"


@dataclass
class KnowledgeItem:
    """Represents a piece of knowledge that can be shared between agents"""
    content: str
    source: str
    knowledge_type: KnowledgeType = KnowledgeType.FACTUAL
    value: float = 1.0
    confidence: float = 1.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class KnowledgeExchange:
    """Manages knowledge exchange between agents"""
    
    def __init__(self):
        self.exchange_history: List[Dict[str, Any]] = []
        self.knowledge_network: Dict[str, List[KnowledgeItem]] = {}
    
    def share_knowledge(
        self,
        sender: str,
        receiver: str,
        knowledge: KnowledgeItem,
        trust_score: float = 0.5
    ) -> bool:
        """Share knowledge between agents"""
        
        # Knowledge sharing decision based on trust
        sharing_threshold = 0.3  # Minimum trust required
        
        if trust_score < sharing_threshold:
            return False
        
        # Record the exchange
        exchange_record = {
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "receiver": receiver,
            "knowledge_content": knowledge.content,
            "knowledge_type": knowledge.knowledge_type.value,
            "knowledge_value": knowledge.value,
            "trust_score": trust_score
        }
        
        self.exchange_history.append(exchange_record)
        
        # Add to receiver's knowledge network
        if receiver not in self.knowledge_network:
            self.knowledge_network[receiver] = []
        
        self.knowledge_network[receiver].append(knowledge)
        
        return True
    
    def get_knowledge_for_agent(self, agent_name: str) -> List[KnowledgeItem]:
        """Get all knowledge available to an agent"""
        return self.knowledge_network.get(agent_name, [])
    
    def get_exchange_history(self) -> List[Dict[str, Any]]:
        """Get the history of knowledge exchanges"""
        return self.exchange_history.copy()
    
    def calculate_knowledge_diversity(self) -> float:
        """Calculate the diversity of knowledge in the system"""
        all_knowledge = []
        for knowledge_list in self.knowledge_network.values():
            all_knowledge.extend(knowledge_list)
        
        if not all_knowledge:
            return 0.0
        
        # Simple diversity measure based on knowledge types
        knowledge_types = set(k.knowledge_type for k in all_knowledge)
        return len(knowledge_types) / len(KnowledgeType)
    
    def get_most_valuable_knowledge(self, agent_name: str, limit: int = 5) -> List[KnowledgeItem]:
        """Get the most valuable knowledge for an agent"""
        agent_knowledge = self.get_knowledge_for_agent(agent_name)
        return sorted(agent_knowledge, key=lambda k: k.value, reverse=True)[:limit]