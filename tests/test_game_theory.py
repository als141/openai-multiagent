"""Tests for game theory components."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.game_theory.payoff import PayoffCalculator, RewardMatrix
from src.game_theory.strategies import (
    TitForTat, AlwaysCooperate, AlwaysDefect, Random, Adaptive,
    GenerousTitForTat, Pavlov, Grudger, create_strategy, StrategyType
)
from src.game_theory.games import PrisonersDilemma, PublicGoodsGame, KnowledgeSharingGame, GameType
from src.agents.base_agent import AgentAction
from src.agents.game_agents import CooperativeAgent, CompetitiveAgent


class TestRewardMatrix:
    """Test RewardMatrix functionality."""
    
    def test_standard_prisoners_dilemma(self):
        """Test standard prisoner's dilemma matrix."""
        matrix = RewardMatrix.prisoner_dilemma()
        
        assert matrix.cooperate_cooperate == (3, 3)
        assert matrix.cooperate_defect == (0, 5)
        assert matrix.defect_cooperate == (5, 0)
        assert matrix.defect_defect == (1, 1)
    
    def test_payoff_calculation(self):
        """Test payoff calculation for different action combinations."""
        matrix = RewardMatrix.prisoner_dilemma()
        
        # Both cooperate
        payoffs = matrix.get_payoffs(AgentAction.COOPERATE, AgentAction.COOPERATE)
        assert payoffs == (3, 3)
        
        # Mixed actions
        payoffs = matrix.get_payoffs(AgentAction.COOPERATE, AgentAction.DEFECT)
        assert payoffs == (0, 5)
        
        # Both defect
        payoffs = matrix.get_payoffs(AgentAction.DEFECT, AgentAction.DEFECT)
        assert payoffs == (1, 1)
        
        # Knowledge sharing treated as cooperation
        payoffs = matrix.get_payoffs(AgentAction.SHARE_KNOWLEDGE, AgentAction.COOPERATE)
        assert payoffs == (3, 3)
    
    def test_matrix_from_dict(self):
        """Test creating matrix from dictionary."""
        data = {
            "cooperate_cooperate": [2, 2],
            "cooperate_defect": [0, 3],
            "defect_cooperate": [3, 0],
            "defect_defect": [1, 1]
        }
        
        matrix = RewardMatrix.from_dict(data)
        assert matrix.cooperate_cooperate == (2, 2)
        assert matrix.cooperate_defect == (0, 3)
    
    def test_matrix_to_numpy(self):
        """Test conversion to numpy array."""
        matrix = RewardMatrix.prisoner_dilemma()
        np_matrix = matrix.to_numpy()
        
        assert np_matrix.shape == (2, 2, 2)  # [players, actions1, actions2]
        assert np_matrix[0, 0, 0] == 3  # Player 1, both cooperate
        assert np_matrix[1, 0, 0] == 3  # Player 2, both cooperate


class TestPayoffCalculator:
    """Test PayoffCalculator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matrix = RewardMatrix.prisoner_dilemma()
        self.calculator = PayoffCalculator(self.matrix)
    
    def test_round_payoffs(self):
        """Test single round payoff calculation."""
        payoffs = self.calculator.calculate_round_payoffs(
            AgentAction.COOPERATE, AgentAction.DEFECT
        )
        assert payoffs == (0, 5)
    
    def test_cumulative_payoffs(self):
        """Test cumulative payoff calculation."""
        history = [
            (AgentAction.COOPERATE, AgentAction.COOPERATE),
            (AgentAction.DEFECT, AgentAction.COOPERATE),
            (AgentAction.COOPERATE, AgentAction.DEFECT)
        ]
        
        total1, total2 = self.calculator.calculate_cumulative_payoffs(history)
        assert total1 == 3 + 5 + 0  # 8
        assert total2 == 3 + 0 + 5  # 8
    
    def test_average_payoffs(self):
        """Test average payoff calculation."""
        history = [
            (AgentAction.COOPERATE, AgentAction.COOPERATE),
            (AgentAction.DEFECT, AgentAction.DEFECT)
        ]
        
        avg1, avg2 = self.calculator.calculate_average_payoffs(history)
        assert avg1 == (3 + 1) / 2  # 2.0
        assert avg2 == (3 + 1) / 2  # 2.0
    
    def test_cooperation_rate(self):
        """Test cooperation rate calculation."""
        actions = [
            AgentAction.COOPERATE,
            AgentAction.DEFECT,
            AgentAction.SHARE_KNOWLEDGE,
            AgentAction.DEFECT
        ]
        
        coop_rate = self.calculator.calculate_cooperation_rate(actions)
        assert coop_rate == 0.5  # 2 cooperative out of 4
    
    def test_mutual_cooperation_rate(self):
        """Test mutual cooperation rate calculation."""
        history = [
            (AgentAction.COOPERATE, AgentAction.COOPERATE),
            (AgentAction.COOPERATE, AgentAction.DEFECT),
            (AgentAction.DEFECT, AgentAction.DEFECT),
            (AgentAction.SHARE_KNOWLEDGE, AgentAction.COOPERATE)
        ]
        
        mutual_rate = self.calculator.calculate_mutual_cooperation_rate(history)
        assert mutual_rate == 0.5  # 2 mutual cooperation out of 4
    
    def test_exploitation_rate(self):
        """Test exploitation rate calculation."""
        history = [
            (AgentAction.DEFECT, AgentAction.COOPERATE),  # Player 1 exploits
            (AgentAction.COOPERATE, AgentAction.DEFECT),  # Player 2 exploits
            (AgentAction.COOPERATE, AgentAction.COOPERATE),
            (AgentAction.DEFECT, AgentAction.COOPERATE)   # Player 1 exploits again
        ]
        
        exploit_rate1 = self.calculator.calculate_exploitation_rate(history, player=1)
        exploit_rate2 = self.calculator.calculate_exploitation_rate(history, player=2)
        
        assert exploit_rate1 == 0.5  # 2 exploitations out of 4
        assert exploit_rate2 == 0.25  # 1 exploitation out of 4
    
    def test_game_outcomes_analysis(self):
        """Test comprehensive game analysis."""
        history = [
            (AgentAction.COOPERATE, AgentAction.COOPERATE),
            (AgentAction.DEFECT, AgentAction.COOPERATE),
            (AgentAction.COOPERATE, AgentAction.DEFECT)
        ]
        
        analysis = self.calculator.analyze_game_outcomes(history, "Agent1", "Agent2")
        
        assert analysis["game_summary"]["total_rounds"] == 3
        assert analysis["Agent1"]["total_payoff"] == 8
        assert analysis["Agent2"]["total_payoff"] == 8
        assert analysis["comparative_analysis"]["winner"] == "Tie"


class TestStrategies:
    """Test strategy implementations."""
    
    def test_tit_for_tat_first_move(self):
        """Test TitForTat starts with cooperation."""
        strategy = TitForTat()
        action = strategy.decide(0)
        assert action == AgentAction.COOPERATE
    
    def test_tit_for_tat_mirror(self):
        """Test TitForTat mirrors opponent."""
        strategy = TitForTat()
        
        # First cooperation
        action = strategy.decide(0)
        assert action == AgentAction.COOPERATE
        
        # Mirror cooperation
        action = strategy.decide(1, AgentAction.COOPERATE)
        assert action == AgentAction.COOPERATE
        
        # Mirror defection
        action = strategy.decide(2, AgentAction.DEFECT)
        assert action == AgentAction.DEFECT
    
    def test_always_cooperate(self):
        """Test AlwaysCooperate strategy."""
        strategy = AlwaysCooperate()
        
        for i in range(5):
            action = strategy.decide(i, AgentAction.DEFECT)
            assert action == AgentAction.COOPERATE
    
    def test_always_defect(self):
        """Test AlwaysDefect strategy."""
        strategy = AlwaysDefect()
        
        for i in range(5):
            action = strategy.decide(i, AgentAction.COOPERATE)
            assert action == AgentAction.DEFECT
    
    def test_random_strategy(self):
        """Test Random strategy."""
        strategy = Random(cooperation_probability=1.0)
        
        # With 100% cooperation probability
        action = strategy.decide(0)
        assert action == AgentAction.COOPERATE
        
        strategy = Random(cooperation_probability=0.0)
        
        # With 0% cooperation probability
        action = strategy.decide(0)
        assert action == AgentAction.DEFECT
    
    def test_generous_tit_for_tat(self):
        """Test GenerousTitForTat forgiveness."""
        strategy = GenerousTitForTat(forgiveness_probability=1.0)
        
        # Should forgive defection with 100% probability
        action = strategy.decide(1, AgentAction.DEFECT)
        assert action == AgentAction.COOPERATE
    
    def test_pavlov_win_stay(self):
        """Test Pavlov win-stay behavior."""
        strategy = Pavlov(win_threshold=2.0)
        
        # First move
        action = strategy.decide(0)
        assert action == AgentAction.COOPERATE
        
        # Update with winning payoff
        strategy.update_history(AgentAction.COOPERATE, AgentAction.COOPERATE, 3.0)
        
        # Should stay with cooperation after winning
        action = strategy.decide(1)
        assert action == AgentAction.COOPERATE
    
    def test_pavlov_lose_shift(self):
        """Test Pavlov lose-shift behavior."""
        strategy = Pavlov(win_threshold=2.0)
        strategy.last_action = AgentAction.COOPERATE
        
        # Update with losing payoff
        strategy.update_history(AgentAction.COOPERATE, AgentAction.DEFECT, 0.0)
        
        # Should shift to defection after losing
        action = strategy.decide(1)
        assert action == AgentAction.DEFECT
    
    def test_grudger_forgiveness(self):
        """Test Grudger never forgives."""
        strategy = Grudger()
        
        # Start with cooperation
        action = strategy.decide(0)
        assert action == AgentAction.COOPERATE
        
        # After opponent defects once
        action = strategy.decide(1, AgentAction.DEFECT)
        assert action == AgentAction.DEFECT
        
        # Should continue defecting even if opponent cooperates
        action = strategy.decide(2, AgentAction.COOPERATE)
        assert action == AgentAction.DEFECT
    
    def test_adaptive_learning(self):
        """Test Adaptive strategy learning."""
        strategy = Adaptive(learning_rate=0.5, exploration_rate=0.0)
        
        # Start with some cooperation probability
        initial_prob = strategy.cooperation_probability
        
        # Simulate poor performance
        strategy.update_history(AgentAction.COOPERATE, AgentAction.DEFECT, 0.0)
        strategy.update_history(AgentAction.COOPERATE, AgentAction.DEFECT, 0.0)
        strategy.update_history(AgentAction.COOPERATE, AgentAction.DEFECT, 0.0)
        
        # Should adapt cooperation probability
        action = strategy.decide(3, AgentAction.DEFECT)
        
        # Cooperation probability should have changed
        assert strategy.cooperation_probability != initial_prob
    
    def test_strategy_factory(self):
        """Test strategy factory function."""
        strategy = create_strategy(StrategyType.TIT_FOR_TAT)
        assert isinstance(strategy, TitForTat)
        
        strategy = create_strategy(StrategyType.ALWAYS_COOPERATE)
        assert isinstance(strategy, AlwaysCooperate)
        
        strategy = create_strategy(StrategyType.RANDOM, cooperation_probability=0.8)
        assert isinstance(strategy, Random)
        assert strategy.cooperation_probability == 0.8


class TestGames:
    """Test game implementations."""
    
    @pytest.mark.asyncio
    async def test_prisoners_dilemma_creation(self):
        """Test PrisonersDilemma game creation."""
        game = PrisonersDilemma()
        
        assert game.name == "Prisoner's Dilemma"
        assert game.game_type == GameType.PRISONERS_DILEMMA
        assert game.round_number == 0
        assert len(game.game_history) == 0
    
    @pytest.mark.asyncio
    async def test_prisoners_dilemma_round(self):
        """Test single round of Prisoner's Dilemma."""
        game = PrisonersDilemma()
        
        # Create mock agents
        agent1 = Mock(spec=CooperativeAgent)
        agent1.name = "Agent1"
        agent1.make_decision = AsyncMock(return_value=Mock(
            action=AgentAction.COOPERATE,
            reasoning="Test",
            confidence=0.8,
            knowledge_to_share=[]
        ))
        agent1.update_state = Mock()
        agent1.share_knowledge = Mock()
        
        agent2 = Mock(spec=CompetitiveAgent)
        agent2.name = "Agent2"
        agent2.make_decision = AsyncMock(return_value=Mock(
            action=AgentAction.DEFECT,
            reasoning="Test",
            confidence=0.9,
            knowledge_to_share=[]
        ))
        agent2.update_state = Mock()
        agent2.share_knowledge = Mock()
        
        # Play round
        result = await game.play_round([agent1, agent2])
        
        assert result["round"] == 1
        assert result["actions"]["Agent1"] == AgentAction.COOPERATE
        assert result["actions"]["Agent2"] == AgentAction.DEFECT
        assert result["payoffs"]["Agent1"] == 0  # Sucker's payoff
        assert result["payoffs"]["Agent2"] == 5  # Temptation payoff
        
        # Verify agents were updated
        agent1.update_state.assert_called_once()
        agent2.update_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prisoners_dilemma_full_game(self):
        """Test full Prisoner's Dilemma game."""
        game = PrisonersDilemma()
        
        # Create simple agents that always cooperate/defect
        agent1 = Mock(spec=CooperativeAgent)
        agent1.name = "Cooperator"
        agent1.make_decision = AsyncMock(return_value=Mock(
            action=AgentAction.COOPERATE,
            reasoning="Always cooperate",
            confidence=1.0,
            knowledge_to_share=[]
        ))
        agent1.update_state = Mock()
        agent1.share_knowledge = Mock()
        
        agent2 = Mock(spec=CompetitiveAgent)
        agent2.name = "Defector"
        agent2.make_decision = AsyncMock(return_value=Mock(
            action=AgentAction.DEFECT,
            reasoning="Always defect",
            confidence=1.0,
            knowledge_to_share=[]
        ))
        agent2.update_state = Mock()
        agent2.share_knowledge = Mock()
        
        # Play full game
        result = await game.play_full_game([agent1, agent2], num_rounds=3)
        
        assert result.game_type == GameType.PRISONERS_DILEMMA
        assert result.rounds == 3
        assert len(result.participants) == 2
        assert result.payoffs["Cooperator"] == 0  # 3 rounds * 0 payoff
        assert result.payoffs["Defector"] == 15  # 3 rounds * 5 payoff
        assert result.winner == "Defector"
        assert result.cooperation_rates["Cooperator"] == 1.0
        assert result.cooperation_rates["Defector"] == 0.0
    
    @pytest.mark.asyncio
    async def test_public_goods_game(self):
        """Test PublicGoodsGame functionality."""
        game = PublicGoodsGame(multiplier=2.0, endowment=10.0)
        
        # Create mock agents
        agents = []
        for i in range(3):
            agent = Mock()
            agent.name = f"Agent{i}"
            # Alternate between cooperate and defect
            action = AgentAction.COOPERATE if i % 2 == 0 else AgentAction.DEFECT
            agent.make_decision = AsyncMock(return_value=Mock(
                action=action,
                reasoning="Test",
                confidence=0.8
            ))
            agent.update_state = Mock()
            agents.append(agent)
        
        # Play round
        result = await game.play_round(agents)
        
        assert result["round"] == 1
        assert "contributions" in result
        assert "public_pool" in result
        assert "payoffs" in result
        
        # Check contributions (cooperators contribute 80%, defectors 20%)
        expected_total = (8.0 * 2) + (2.0 * 1)  # 2 cooperators, 1 defector
        assert abs(result["total_contributions"] - expected_total) < 0.1
    
    @pytest.mark.asyncio
    async def test_knowledge_sharing_game(self):
        """Test KnowledgeSharingGame functionality."""
        game = KnowledgeSharingGame(knowledge_value=2.0, sharing_cost=0.5)
        
        # Create mock agents with some knowledge
        agents = []
        for i in range(2):
            agent = Mock()
            agent.name = f"Agent{i}"
            agent.state = Mock()
            agent.state.knowledge_base = [f"knowledge_{i}"]
            agent.get_trust_score = Mock(return_value=0.8)  # High trust
            
            # First agent shares, second doesn't
            if i == 0:
                agent.make_decision = AsyncMock(return_value=Mock(
                    action=AgentAction.SHARE_KNOWLEDGE,
                    reasoning="Share knowledge",
                    confidence=0.8,
                    knowledge_to_share=[f"shared_knowledge_{i}"]
                ))
            else:
                agent.make_decision = AsyncMock(return_value=Mock(
                    action=AgentAction.WITHHOLD_KNOWLEDGE,
                    reasoning="Withhold knowledge",
                    confidence=0.8,
                    knowledge_to_share=[]
                ))
            
            agent.update_state = Mock()
            agent.share_knowledge = Mock()
            agents.append(agent)
        
        # Play round
        result = await game.play_round(agents)
        
        assert result["round"] == 1
        assert "knowledge_shared" in result
        assert "knowledge_received" in result
        assert "payoffs" in result
        
        # First agent should have negative payoff (sharing cost)
        # Second agent should have positive payoff (received knowledge)
        assert result["payoffs"]["Agent0"] < 0  # Paid sharing cost
        assert result["payoffs"]["Agent1"] > 0  # Received knowledge value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])