"""Tests for agent classes and behavior."""

import pytest
import asyncio
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.base_agent import BaseGameAgent, AgentAction, AgentState, GameDecision
from src.agents.game_agents import CooperativeAgent, CompetitiveAgent, TitForTatAgent, AdaptiveAgent, RandomAgent
from src.agents.coordinator import GameCoordinator


class TestAgentState:
    """Test AgentState functionality."""
    
    def test_initial_state(self):
        """Test initial agent state."""
        state = AgentState()
        
        assert state.trust_scores == {}
        assert state.knowledge_base == []
        assert state.cooperation_history == []
        assert state.payoff_history == []
        assert state.reputation == 0.5
    
    def test_trust_update_cooperation(self):
        """Test trust update with cooperation."""
        state = AgentState()
        
        # Initial cooperation should increase trust
        state.update_trust("agent1", True)
        assert state.trust_scores["agent1"] == 0.6
        
        # Continued cooperation should increase further
        state.update_trust("agent1", True)
        assert state.trust_scores["agent1"] == 0.7
    
    def test_trust_update_defection(self):
        """Test trust update with defection."""
        state = AgentState()
        state.trust_scores["agent1"] = 0.5
        
        # Defection should decrease trust
        state.update_trust("agent1", False)
        assert state.trust_scores["agent1"] == 0.3
    
    def test_trust_decay(self):
        """Test trust decay for other agents."""
        state = AgentState()
        state.trust_scores["agent1"] = 0.8
        state.trust_scores["agent2"] = 0.6
        
        # Update trust for agent1, should decay agent2's trust
        state.update_trust("agent1", True, decay_rate=0.1)
        
        assert state.trust_scores["agent1"] == 0.9
        assert state.trust_scores["agent2"] == 0.54  # 0.6 * 0.9


class TestGameAgents:
    """Test specific agent implementations."""
    
    def test_cooperative_agent_creation(self):
        """Test CooperativeAgent creation."""
        agent = CooperativeAgent("TestCoop")
        
        assert agent.name == "TestCoop"
        assert agent.strategy == "always_cooperate"
        assert agent.cooperation_threshold == 0.2
        assert agent.trust_threshold == 0.3
    
    def test_competitive_agent_creation(self):
        """Test CompetitiveAgent creation."""
        agent = CompetitiveAgent("TestComp")
        
        assert agent.name == "TestComp"
        assert agent.strategy == "always_defect"
        assert agent.cooperation_threshold == 0.8
        assert agent.trust_threshold == 0.7
    
    @pytest.mark.asyncio
    async def test_cooperative_agent_decision(self):
        """Test CooperativeAgent always cooperates."""
        agent = CooperativeAgent("TestCoop")
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        decision = await agent.make_decision(context)
        
        assert decision.action == AgentAction.COOPERATE
        assert decision.confidence > 0.8
        assert "cooperation" in decision.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_competitive_agent_decision_low_trust(self):
        """Test CompetitiveAgent defects with low trust."""
        agent = CompetitiveAgent("TestComp")
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        decision = await agent.make_decision(context)
        
        assert decision.action == AgentAction.DEFECT
        assert decision.confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_competitive_agent_decision_high_trust(self):
        """Test CompetitiveAgent can cooperate with high trust."""
        agent = CompetitiveAgent("TestComp")
        agent.state.trust_scores["opponent"] = 0.9  # High trust
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        decision = await agent.make_decision(context)
        
        assert decision.action == AgentAction.COOPERATE
        assert "trust" in decision.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_tit_for_tat_first_move(self):
        """Test TitForTat starts with cooperation."""
        agent = TitForTatAgent("TestTFT")
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        decision = await agent.make_decision(context)
        
        assert decision.action == AgentAction.COOPERATE
        assert "first interaction" in decision.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_tit_for_tat_mirror_cooperation(self):
        """Test TitForTat mirrors cooperation."""
        agent = TitForTatAgent("TestTFT")
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        opponent_history = [AgentAction.COOPERATE]
        
        decision = await agent.make_decision(context, opponent_history)
        
        assert decision.action == AgentAction.COOPERATE
        assert "cooperated last time" in decision.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_tit_for_tat_mirror_defection(self):
        """Test TitForTat mirrors defection."""
        agent = TitForTatAgent("TestTFT")
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        opponent_history = [AgentAction.DEFECT]
        
        decision = await agent.make_decision(context, opponent_history)
        
        assert decision.action == AgentAction.DEFECT
        assert "defected last time" in decision.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_adaptive_agent_adaptation(self):
        """Test AdaptiveAgent adapts based on context."""
        agent = AdaptiveAgent("TestAdaptive")
        
        # Start with some history
        agent.state.payoff_history = [1.0, 1.5, 2.0]  # Poor performance
        agent.state.trust_scores["opponent"] = 0.8
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        decision = await agent.make_decision(context)
        
        assert isinstance(decision.action, AgentAction)
        assert "adaptive" in decision.reasoning.lower()
        assert 0.0 <= decision.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_random_agent_decision(self):
        """Test RandomAgent makes valid decisions."""
        agent = RandomAgent("TestRandom")
        
        context = {"game_type": "prisoners_dilemma", "opponent_id": "opponent"}
        decision = await agent.make_decision(context)
        
        assert decision.action in [AgentAction.COOPERATE, AgentAction.DEFECT]
        assert decision.confidence == 0.5
        assert "random" in decision.reasoning.lower()


class TestAgentInteractions:
    """Test agent interaction mechanisms."""
    
    def test_agent_state_update(self):
        """Test agent state updates after interactions."""
        agent = CooperativeAgent("TestAgent")
        
        # Simulate interaction
        agent.update_state("opponent", AgentAction.COOPERATE, 3.0, AgentAction.COOPERATE)
        
        assert agent.state.trust_scores["opponent"] == 0.6  # Increased from 0.5
        assert len(agent.state.cooperation_history) == 1
        assert len(agent.state.payoff_history) == 1
        assert agent.state.payoff_history[0] == 3.0
    
    def test_knowledge_sharing(self):
        """Test knowledge sharing mechanisms."""
        agent = CooperativeAgent("TestAgent")
        
        # Share knowledge
        knowledge = ["fact1", "fact2", "fact3"]
        agent.share_knowledge(knowledge)
        
        assert len(agent.state.knowledge_base) == 3
        assert "fact1" in agent.state.knowledge_base
        
        # Don't duplicate knowledge
        agent.share_knowledge(["fact1", "fact4"])
        assert len(agent.state.knowledge_base) == 4
        assert agent.state.knowledge_base.count("fact1") == 1
    
    def test_knowledge_to_share_trust_based(self):
        """Test knowledge sharing based on trust."""
        agent = CooperativeAgent("TestAgent")
        agent.share_knowledge(["secret1", "secret2", "secret3"])
        
        # Low trust - no sharing
        agent.state.trust_scores["low_trust"] = 0.1
        knowledge = agent.get_knowledge_to_share("low_trust")
        assert len(knowledge) == 0
        
        # High trust - share knowledge
        agent.state.trust_scores["high_trust"] = 0.8
        knowledge = agent.get_knowledge_to_share("high_trust")
        assert len(knowledge) > 0
    
    def test_cooperation_rate_calculation(self):
        """Test cooperation rate calculation."""
        agent = CooperativeAgent("TestAgent")
        
        # Add cooperation history
        agent.state.cooperation_history = [
            ("agent1", AgentAction.COOPERATE),
            ("agent1", AgentAction.DEFECT),
            ("agent1", AgentAction.COOPERATE),
            ("agent2", AgentAction.COOPERATE)
        ]
        
        # Overall cooperation rate
        overall_rate = agent.get_cooperation_rate()
        assert overall_rate == 0.75  # 3/4 cooperative actions
        
        # Agent-specific cooperation rate
        agent1_rate = agent.get_cooperation_rate("agent1")
        assert agent1_rate == 2/3  # 2/3 cooperative with agent1


class TestGameCoordinator:
    """Test GameCoordinator functionality."""
    
    def test_coordinator_creation(self):
        """Test GameCoordinator creation."""
        coordinator = GameCoordinator()
        
        assert len(coordinator.games) == 3  # Three game types
        assert len(coordinator.agents) == 0
        assert len(coordinator.experiment_results) == 0
    
    def test_agent_registration(self):
        """Test agent registration."""
        coordinator = GameCoordinator()
        agent = CooperativeAgent("TestAgent")
        
        coordinator.register_agent(agent)
        
        assert "TestAgent" in coordinator.agents
        assert coordinator.agents["TestAgent"] == agent
    
    def test_agent_creation(self):
        """Test agent creation through coordinator."""
        coordinator = GameCoordinator()
        
        agent = coordinator.create_agent("cooperative", "TestCoop")
        
        assert agent.name == "TestCoop"
        assert agent.strategy == "always_cooperate"
        assert "TestCoop" in coordinator.agents
    
    def test_invalid_agent_type(self):
        """Test error handling for invalid agent types."""
        coordinator = GameCoordinator()
        
        with pytest.raises(ValueError):
            coordinator.create_agent("invalid_type", "TestAgent")
    
    def test_standard_agent_set_creation(self):
        """Test creation of standard agent set."""
        coordinator = GameCoordinator()
        
        coordinator.create_standard_agent_set()
        
        assert len(coordinator.agents) == 5
        agent_names = list(coordinator.agents.keys())
        assert any("Cooperative" in name for name in agent_names)
        assert any("Competitive" in name for name in agent_names)
        assert any("TitForTat" in name for name in agent_names)
        assert any("Adaptive" in name for name in agent_names)
        assert any("Random" in name for name in agent_names)
    
    def test_agent_statistics(self):
        """Test agent statistics collection."""
        coordinator = GameCoordinator()
        agent = coordinator.create_agent("cooperative", "TestAgent")
        
        # Add some history
        agent.state.payoff_history = [2.0, 3.0, 2.5]
        agent.state.cooperation_history = [
            ("other", AgentAction.COOPERATE),
            ("other", AgentAction.COOPERATE)
        ]
        
        stats = coordinator.get_agent_statistics()
        
        assert "TestAgent" in stats
        agent_stats = stats["TestAgent"]
        assert agent_stats["strategy"] == "always_cooperate"
        assert agent_stats["total_games"] == 3
        assert agent_stats["average_payoff"] == 2.5
        assert agent_stats["cooperation_rate"] == 1.0
    
    def test_agent_reset(self):
        """Test agent state reset."""
        coordinator = GameCoordinator()
        agent = coordinator.create_agent("cooperative", "TestAgent")
        
        # Add some state
        agent.state.payoff_history = [1.0, 2.0]
        agent.state.trust_scores["other"] = 0.8
        agent.state.knowledge_base = ["knowledge"]
        
        coordinator.reset_all_agents()
        
        assert len(agent.state.payoff_history) == 0
        assert len(agent.state.trust_scores) == 0
        assert len(agent.state.knowledge_base) == 0
        assert agent.state.reputation == 0.5


@pytest.mark.asyncio
class TestAsyncAgentBehavior:
    """Test asynchronous agent behavior."""
    
    async def test_concurrent_decisions(self):
        """Test that multiple agents can make decisions concurrently."""
        agents = [
            CooperativeAgent("Coop"),
            CompetitiveAgent("Comp"),
            TitForTatAgent("TFT")
        ]
        
        context = {"game_type": "prisoners_dilemma"}
        
        # Make decisions concurrently
        tasks = [agent.make_decision(context) for agent in agents]
        decisions = await asyncio.gather(*tasks)
        
        assert len(decisions) == 3
        assert all(isinstance(d, GameDecision) for d in decisions)
        assert all(isinstance(d.action, AgentAction) for d in decisions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])