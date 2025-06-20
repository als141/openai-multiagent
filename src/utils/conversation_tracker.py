"""Conversation tracking and analysis for agent interactions."""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from ..agents.types import AgentAction, GameDecision


@dataclass
class ConversationTurn:
    """A single turn in agent conversation."""
    timestamp: str
    agent_name: str
    game_type: str
    round_number: int
    context: Dict[str, Any]
    decision: GameDecision
    reasoning_process: str
    response_time_ms: float
    opponent_last_action: Optional[AgentAction] = None
    trust_level: float = 0.5
    confidence_level: float = 0.5


@dataclass 
class ConversationSession:
    """Complete conversation session between agents."""
    session_id: str
    start_time: str
    end_time: str
    participants: List[str]
    game_type: str
    total_rounds: int
    turns: List[ConversationTurn]
    final_outcomes: Dict[str, Any]
    session_metadata: Dict[str, Any]


class ConversationTracker:
    """Tracks and analyzes agent conversations."""
    
    def __init__(self, results_dir: str = "results/conversations"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.completed_sessions: List[ConversationSession] = []
    
    def start_session(
        self,
        session_id: str,
        participants: List[str],
        game_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Start tracking a new conversation session."""
        session = ConversationSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            end_time="",
            participants=participants,
            game_type=game_type,
            total_rounds=0,
            turns=[],
            final_outcomes={},
            session_metadata=metadata or {}
        )
        
        self.active_sessions[session_id] = session
    
    def record_turn(
        self,
        session_id: str,
        agent_name: str,
        round_number: int,
        context: Dict[str, Any],
        decision: GameDecision,
        reasoning_process: str,
        response_time_ms: float,
        opponent_last_action: Optional[AgentAction] = None,
        trust_level: float = 0.5
    ) -> None:
        """Record a single conversation turn."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            game_type=session.game_type,
            round_number=round_number,
            context=context,
            decision=decision,
            reasoning_process=reasoning_process,
            response_time_ms=response_time_ms,
            opponent_last_action=opponent_last_action,
            trust_level=trust_level,
            confidence_level=decision.confidence
        )
        
        session.turns.append(turn)
        session.total_rounds = max(session.total_rounds, round_number)
    
    def end_session(
        self,
        session_id: str,
        final_outcomes: Dict[str, Any]
    ) -> ConversationSession:
        """End a conversation session and save results."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now().isoformat()
        session.final_outcomes = final_outcomes
        
        # Save to file
        self._save_session(session)
        
        # Move to completed sessions
        self.completed_sessions.append(session)
        del self.active_sessions[session_id]
        
        return session
    
    def _save_session(self, session: ConversationSession) -> None:
        """Save conversation session to file."""
        filename = f"conversation_{session.session_id}.json"
        filepath = self.results_dir / filename
        
        # Convert to serializable format
        session_data = {
            "session_id": session.session_id,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "participants": session.participants,
            "game_type": session.game_type,
            "total_rounds": session.total_rounds,
            "final_outcomes": session.final_outcomes,
            "session_metadata": session.session_metadata,
            "turns": [
                {
                    "timestamp": turn.timestamp,
                    "agent_name": turn.agent_name,
                    "game_type": turn.game_type,
                    "round_number": turn.round_number,
                    "context": turn.context,
                    "decision": {
                        "action": turn.decision.action.value,
                        "reasoning": turn.decision.reasoning,
                        "confidence": turn.decision.confidence,
                        "knowledge_to_share": turn.decision.knowledge_to_share
                    },
                    "reasoning_process": turn.reasoning_process,
                    "response_time_ms": turn.response_time_ms,
                    "opponent_last_action": turn.opponent_last_action.value if turn.opponent_last_action else None,
                    "trust_level": turn.trust_level,
                    "confidence_level": turn.confidence_level
                }
                for turn in session.turns
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """Analyze a conversation session."""
        # Find session
        session = None
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            session = next((s for s in self.completed_sessions if s.session_id == session_id), None)
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Basic statistics
        total_turns = len(session.turns)
        agent_turn_counts = {}
        agent_cooperation_rates = {}
        agent_avg_confidence = {}
        agent_avg_response_time = {}
        reasoning_patterns = {}
        
        for turn in session.turns:
            agent = turn.agent_name
            
            # Turn counts
            agent_turn_counts[agent] = agent_turn_counts.get(agent, 0) + 1
            
            # Cooperation rates
            if agent not in agent_cooperation_rates:
                agent_cooperation_rates[agent] = []
            is_cooperative = turn.decision.action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
            agent_cooperation_rates[agent].append(is_cooperative)
            
            # Average confidence
            if agent not in agent_avg_confidence:
                agent_avg_confidence[agent] = []
            agent_avg_confidence[agent].append(turn.confidence_level)
            
            # Average response time
            if agent not in agent_avg_response_time:
                agent_avg_response_time[agent] = []
            agent_avg_response_time[agent].append(turn.response_time_ms)
            
            # Reasoning patterns
            if agent not in reasoning_patterns:
                reasoning_patterns[agent] = []
            reasoning_patterns[agent].append(turn.decision.reasoning)
        
        # Calculate averages
        for agent in agent_cooperation_rates:
            agent_cooperation_rates[agent] = sum(agent_cooperation_rates[agent]) / len(agent_cooperation_rates[agent])
            agent_avg_confidence[agent] = sum(agent_avg_confidence[agent]) / len(agent_avg_confidence[agent])
            agent_avg_response_time[agent] = sum(agent_avg_response_time[agent]) / len(agent_avg_response_time[agent])
        
        # Conversation flow analysis
        conversation_flow = []
        for i, turn in enumerate(session.turns):
            flow_item = {
                "turn_number": i + 1,
                "agent": turn.agent_name,
                "action": turn.decision.action.value,
                "confidence": turn.confidence_level,
                "trust_level": turn.trust_level,
                "reasoning_summary": turn.decision.reasoning[:100] + "..." if len(turn.decision.reasoning) > 100 else turn.decision.reasoning
            }
            conversation_flow.append(flow_item)
        
        return {
            "session_summary": {
                "session_id": session.session_id,
                "participants": session.participants,
                "game_type": session.game_type,
                "total_rounds": session.total_rounds,
                "total_turns": total_turns,
                "duration": self._calculate_duration(session.start_time, session.end_time),
                "final_outcomes": session.final_outcomes
            },
            "agent_statistics": {
                "turn_counts": agent_turn_counts,
                "cooperation_rates": agent_cooperation_rates,
                "average_confidence": agent_avg_confidence,
                "average_response_time_ms": agent_avg_response_time
            },
            "conversation_flow": conversation_flow,
            "reasoning_patterns": {
                agent: self._analyze_reasoning_patterns(patterns)
                for agent, patterns in reasoning_patterns.items()
            }
        }
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate session duration in seconds."""
        if not end_time:
            return 0.0
        
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        return (end - start).total_seconds()
    
    def _analyze_reasoning_patterns(self, reasoning_list: List[str]) -> Dict[str, Any]:
        """Analyze reasoning patterns for an agent."""
        # Common reasoning keywords
        cooperation_keywords = ['cooperate', 'trust', 'mutual', 'benefit', 'share', 'collaborate']
        competition_keywords = ['defect', 'compete', 'advantage', 'win', 'strategy', 'exploit']
        uncertainty_keywords = ['uncertain', 'maybe', 'perhaps', 'might', 'unsure', 'difficult']
        
        total_reasoning = len(reasoning_list)
        
        cooperation_mentions = sum(
            1 for reasoning in reasoning_list
            if any(keyword in reasoning.lower() for keyword in cooperation_keywords)
        )
        
        competition_mentions = sum(
            1 for reasoning in reasoning_list
            if any(keyword in reasoning.lower() for keyword in competition_keywords)
        )
        
        uncertainty_mentions = sum(
            1 for reasoning in reasoning_list
            if any(keyword in reasoning.lower() for keyword in uncertainty_keywords)
        )
        
        # Average reasoning length
        avg_reasoning_length = sum(len(r) for r in reasoning_list) / total_reasoning if total_reasoning > 0 else 0
        
        return {
            "total_reasoning_instances": total_reasoning,
            "cooperation_focus_rate": cooperation_mentions / total_reasoning if total_reasoning > 0 else 0,
            "competition_focus_rate": competition_mentions / total_reasoning if total_reasoning > 0 else 0,
            "uncertainty_rate": uncertainty_mentions / total_reasoning if total_reasoning > 0 else 0,
            "average_reasoning_length": avg_reasoning_length,
            "reasoning_complexity": "high" if avg_reasoning_length > 200 else "medium" if avg_reasoning_length > 100 else "low"
        }
    
    def get_session_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get history of completed sessions."""
        sessions = self.completed_sessions
        if limit:
            sessions = sessions[-limit:]
        
        return [
            {
                "session_id": session.session_id,
                "participants": session.participants,
                "game_type": session.game_type,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "total_rounds": session.total_rounds,
                "total_turns": len(session.turns),
                "final_outcomes": session.final_outcomes
            }
            for session in sessions
        ]
    
    def export_conversations_csv(self, output_file: str) -> None:
        """Export conversation data to CSV for analysis."""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'session_id', 'timestamp', 'agent_name', 'game_type', 'round_number',
                'action', 'reasoning', 'confidence', 'trust_level', 'response_time_ms',
                'opponent_last_action', 'knowledge_shared_count'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for session in self.completed_sessions:
                for turn in session.turns:
                    writer.writerow({
                        'session_id': session.session_id,
                        'timestamp': turn.timestamp,
                        'agent_name': turn.agent_name,
                        'game_type': turn.game_type,
                        'round_number': turn.round_number,
                        'action': turn.decision.action.value,
                        'reasoning': turn.decision.reasoning,
                        'confidence': turn.confidence_level,
                        'trust_level': turn.trust_level,
                        'response_time_ms': turn.response_time_ms,
                        'opponent_last_action': turn.opponent_last_action.value if turn.opponent_last_action else '',
                        'knowledge_shared_count': len(turn.decision.knowledge_to_share) if turn.decision.knowledge_to_share else 0
                    })


# Global conversation tracker instance
conversation_tracker = ConversationTracker()