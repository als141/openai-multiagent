"""Game coordinator for managing multi-agent interactions."""

import asyncio
import os
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass
from datetime import datetime
import json
import uuid

from ..game_theory.games import BaseGame, PrisonersDilemma, PublicGoodsGame, KnowledgeSharingGame, GameResult, GameType
from ..game_theory.payoff import RewardMatrix
from ..agents.base_agent import BaseGameAgent
from ..agents.game_agents import CooperativeAgent, CompetitiveAgent, TitForTatAgent, AdaptiveAgent, RandomAgent
from ..agents.llm_agent import LLMAgentFactory
from ..utils.logger import get_logger, setup_logger
from ..utils.conversation_tracker import conversation_tracker
from ..utils.experiment_logger import ExperimentLogger


@dataclass
class ExperimentConfig:
    """Configuration for game experiments."""
    game_types: List[GameType]
    agent_types: List[str]
    num_rounds: int
    num_repetitions: int
    save_results: bool = True
    results_dir: str = "results"
    reward_matrix: Optional[RewardMatrix] = None
    enable_conversation_tracking: bool = True
    enable_detailed_logging: bool = True
    experiment_description: str = ""


class GameCoordinator:
    """Coordinates games between multiple agents with research-grade tracking."""
    
    def __init__(
        self,
        logger_name: str = "coordinator",
        log_level: str = "INFO",
        results_dir: str = "results"
    ):
        self.logger = setup_logger(logger_name, log_level)
        self.results_dir = results_dir
        self.games: Dict[GameType, BaseGame] = {}
        self.agents: Dict[str, BaseGameAgent] = {}
        self.experiment_results: List[Dict[str, Any]] = []
        
        # Research tracking components
        self.experiment_logger: Optional[ExperimentLogger] = None
        self.current_experiment_id: Optional[str] = None
        
        # Ensure results directory exists
        os.makedirs(results_dir, exist_ok=True)
        
        # Initialize available games
        self._initialize_games()
    
    def _initialize_games(self) -> None:
        """Initialize available game types."""
        self.games[GameType.PRISONERS_DILEMMA] = PrisonersDilemma()
        self.games[GameType.PUBLIC_GOODS] = PublicGoodsGame()
        self.games[GameType.KNOWLEDGE_SHARING] = KnowledgeSharingGame()
    
    def register_agent(self, agent: BaseGameAgent) -> None:
        """Register an agent with the coordinator."""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name} ({agent.strategy})")
    
    def create_agent(
        self,
        agent_type: str,
        name: str,
        use_llm: bool = False,
        **kwargs
    ) -> BaseGameAgent:
        """エージェントを作成・登録する。
        
        Args:
            agent_type: エージェントタイプ
            name: エージェント名
            use_llm: LLMエージェントを使用するか
            **kwargs: 追加引数
        """
        if use_llm:
            # LLMエージェントを作成
            llm_factory_methods = {
                "cooperative": LLMAgentFactory.create_cooperative_agent,
                "competitive": LLMAgentFactory.create_competitive_agent,
                "tit_for_tat": LLMAgentFactory.create_tit_for_tat_agent,
                "adaptive": LLMAgentFactory.create_adaptive_agent,
                "random": LLMAgentFactory.create_random_agent
            }
            
            if agent_type not in llm_factory_methods:
                raise ValueError(f"未知のLLMエージェントタイプ: {agent_type}")
            
            factory_method = llm_factory_methods[agent_type]
            agent = factory_method(name, **kwargs)
        else:
            # 従来のルールベースエージェントを作成
            agent_classes = {
                "cooperative": CooperativeAgent,
                "competitive": CompetitiveAgent,
                "tit_for_tat": TitForTatAgent,
                "adaptive": AdaptiveAgent,
                "random": RandomAgent
            }
            
            if agent_type not in agent_classes:
                raise ValueError(f"未知のエージェントタイプ: {agent_type}")
            
            agent_class = agent_classes[agent_type]
            agent = agent_class(name, **kwargs)
        
        self.register_agent(agent)
        return agent
    
    def get_game(self, game_type: GameType) -> BaseGame:
        """Get a game instance by type."""
        if game_type not in self.games:
            raise ValueError(f"Unknown game type: {game_type}")
        return self.games[game_type]
    
    async def run_single_game(
        self,
        game_type: GameType,
        agent_names: List[str],
        num_rounds: int,
        context: Optional[Dict[str, Any]] = None,
        enable_conversation_tracking: bool = False
    ) -> GameResult:
        """Run a single game between specified agents with optional conversation tracking."""
        game = self.get_game(game_type)
        agents = [self.agents[name] for name in agent_names if name in self.agents]
        
        if len(agents) < 2:
            raise ValueError("Need at least 2 agents to run a game")
        
        self.logger.info(
            f"Starting {game_type.value} between {[a.name for a in agents]} "
            f"for {num_rounds} rounds"
        )
        
        # Set up conversation tracking if enabled
        session_id = None
        if enable_conversation_tracking:
            session_id = f"game_{uuid.uuid4().hex[:8]}_{game_type.value}"
            conversation_tracker.start_session(
                session_id=session_id,
                participants=[a.name for a in agents],
                game_type=game_type.value,
                metadata={
                    "num_rounds": num_rounds,
                    "experiment_id": self.current_experiment_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Add session_id to context
            game_context = context or {}
            game_context.update({
                "session_id": session_id,
                "enable_conversation_tracking": True
            })
        else:
            game_context = context
        
        # Log to experiment logger if available
        if self.experiment_logger:
            self.experiment_logger.log_agent_interaction(
                agent1_name=agents[0].name,
                agent2_name=agents[1].name if len(agents) > 1 else "group",
                game_type=game_type.value,
                round_number=0,  # Game start
                actions={"status": "game_started"},
                payoffs={},
                additional_data={
                    "num_rounds": num_rounds,
                    "session_id": session_id
                }
            )
        
        # Reset game state
        game.reset()
        
        try:
            # Run the game
            result = await game.play_full_game(agents, num_rounds, game_context)
            
            # End conversation tracking
            if session_id:
                conversation_tracker.end_session(
                    session_id=session_id,
                    final_outcomes={
                        "winner": result.winner,
                        "payoffs": result.payoffs,
                        "cooperation_rates": result.cooperation_rates,
                        "total_rounds": result.rounds
                    }
                )
            
            # Log completion to experiment logger
            if self.experiment_logger:
                self.experiment_logger.log_agent_interaction(
                    agent1_name=agents[0].name,
                    agent2_name=agents[1].name if len(agents) > 1 else "group",
                    game_type=game_type.value,
                    round_number=result.rounds + 1,  # Game end
                    actions={"status": "game_completed"},
                    payoffs=result.payoffs,
                    additional_data={
                        "winner": result.winner,
                        "cooperation_rates": result.cooperation_rates,
                        "session_id": session_id
                    }
                )
            
            self.logger.info(
                f"Game completed. Winner: {result.winner or 'Tie'}. "
                f"Final payoffs: {result.payoffs}"
            )
            
            return result
            
        except Exception as e:
            # Log error and end tracking
            if self.experiment_logger:
                self.experiment_logger.log_error(e, f"Game execution: {game_type.value}")
            
            if session_id:
                conversation_tracker.end_session(
                    session_id=session_id,
                    final_outcomes={"error": str(e)}
                )
            
            raise
    
    async def run_tournament(
        self,
        game_type: GameType,
        num_rounds: int,
        num_repetitions: int = 1,
        context: Optional[Dict[str, Any]] = None,
        enable_conversation_tracking: bool = False
    ) -> List[GameResult]:
        """Run a tournament between all registered agents with optional conversation tracking."""
        if len(self.agents) < 2:
            raise ValueError("Need at least 2 agents for a tournament")
        
        agent_names = list(self.agents.keys())
        results = []
        
        self.logger.info(
            f"Starting tournament: {game_type.value}, "
            f"{len(agent_names)} agents, {num_rounds} rounds, "
            f"{num_repetitions} repetitions"
        )
        
        # Log tournament start
        if self.experiment_logger:
            self.experiment_logger.start_phase(
                f"tournament_{game_type.value}",
                f"Tournament with {len(agent_names)} agents, {num_rounds} rounds, {num_repetitions} repetitions"
            )
        
        total_matches = len(agent_names) * (len(agent_names) - 1) // 2 * num_repetitions
        match_count = 0
        
        # Run all pairwise combinations
        for i in range(len(agent_names)):
            for j in range(i + 1, len(agent_names)):
                agent1, agent2 = agent_names[i], agent_names[j]
                
                for rep in range(num_repetitions):
                    match_count += 1
                    self.logger.info(f"Match {match_count}/{total_matches}: {agent1} vs {agent2} (rep {rep+1})")
                    
                    try:
                        result = await self.run_single_game(
                            game_type, [agent1, agent2], num_rounds, context, enable_conversation_tracking
                        )
                        
                        # Add tournament metadata
                        result.additional_metrics = result.additional_metrics or {}
                        result.additional_metrics.update({
                            "tournament_match": f"{agent1}_vs_{agent2}",
                            "repetition": rep + 1,
                            "match_number": match_count,
                            "total_matches": total_matches,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        results.append(result)
                        
                        # Log performance metrics
                        if self.experiment_logger:
                            self.experiment_logger.log_performance_metric(
                                "tournament_match_completion",
                                match_count / total_matches,
                                "percentage",
                                f"{agent1}_vs_{agent2}_rep_{rep+1}"
                            )
                            
                    except Exception as e:
                        self.logger.error(f"Error in match {match_count}: {e}")
                        if self.experiment_logger:
                            self.experiment_logger.log_error(e, f"Tournament match {match_count}: {agent1} vs {agent2}")
        
        # End tournament phase
        if self.experiment_logger:
            tournament_stats = {
                "total_matches": len(results),
                "successful_matches": len([r for r in results if r.winner is not None or len(r.payoffs) > 0]),
                "average_cooperation_rate": sum(
                    sum(r.cooperation_rates.values()) / len(r.cooperation_rates)
                    for r in results if r.cooperation_rates
                ) / len(results) if results else 0
            }
            self.experiment_logger.end_phase(f"tournament_{game_type.value}", tournament_stats)
        
        self.logger.info(f"Tournament completed. Total matches: {len(results)}")
        return results
    
    async def run_experiment(self, config: ExperimentConfig) -> Dict[str, Any]:
        """Run a complete experiment with multiple games and configurations."""
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_experiment_id = experiment_id
        
        # Initialize experiment logger if detailed logging is enabled
        if config.enable_detailed_logging:
            self.experiment_logger = ExperimentLogger(experiment_id, self.results_dir)
            self.experiment_logger.start_phase(
                "experiment_setup",
                f"Initializing experiment: {config.experiment_description or 'Multi-agent game theory experiment'}"
            )
        
        experiment_results = {
            "experiment_id": experiment_id,
            "config": {
                "game_types": [gt.value for gt in config.game_types],
                "agent_types": config.agent_types,
                "num_rounds": config.num_rounds,
                "num_repetitions": config.num_repetitions,
                "enable_conversation_tracking": config.enable_conversation_tracking,
                "enable_detailed_logging": config.enable_detailed_logging,
                "description": config.experiment_description
            },
            "agents": {name: agent.strategy for name, agent in self.agents.items()},
            "results": {}
        }
        
        self.logger.info(f"Starting experiment {experiment_id}")
        
        try:
            # End setup phase
            if self.experiment_logger:
                self.experiment_logger.end_phase("experiment_setup", {
                    "total_agents": len(self.agents),
                    "total_game_types": len(config.game_types),
                    "estimated_total_games": len(config.game_types) * len(self.agents) * (len(self.agents) - 1) // 2 * config.num_repetitions
                })
            
            # Run tournaments for each game type
            for i, game_type in enumerate(config.game_types):
                self.logger.info(f"Running {game_type.value} tournament ({i+1}/{len(config.game_types)})")
                
                # Set up custom reward matrix if provided
                if config.reward_matrix and game_type == GameType.PRISONERS_DILEMMA:
                    game = self.games[game_type]
                    if isinstance(game, PrisonersDilemma):
                        game.reward_matrix = config.reward_matrix
                        game.payoff_calculator.reward_matrix = config.reward_matrix
                
                tournament_results = await self.run_tournament(
                    game_type, 
                    config.num_rounds, 
                    config.num_repetitions,
                    context=None,
                    enable_conversation_tracking=config.enable_conversation_tracking
                )
                
                experiment_results["results"][game_type.value] = [
                    self._serialize_game_result(result) for result in tournament_results
                ]
                
                # Log game type completion
                if self.experiment_logger:
                    self.experiment_logger.log_performance_metric(
                        "game_type_completion",
                        (i + 1) / len(config.game_types),
                        "percentage",
                        f"Completed {game_type.value}"
                    )
            
            # Generate final analysis
            if self.experiment_logger:
                self.experiment_logger.start_phase("experiment_analysis", "Generating final analysis and reports")
                
                # Save detailed results with analysis
                self.experiment_logger.save_detailed_results(experiment_results)
                
                # Export logs to CSV
                self.experiment_logger.export_logs_csv()
                
                # Save experiment state
                self.experiment_logger.save_experiment_state({
                    "agent_statistics": self.get_agent_statistics(),
                    "conversation_history_count": len(conversation_tracker.completed_sessions),
                    "total_experiments_run": len(self.experiment_results) + 1
                })
                
                self.experiment_logger.end_phase("experiment_analysis", {
                    "total_results_saved": sum(len(results) for results in experiment_results["results"].values()),
                    "analysis_files_created": 4  # detailed_results, summary, CSV, state
                })
                
                # Finalize experiment
                self.experiment_logger.finalize_experiment()
        
        except Exception as e:
            if self.experiment_logger:
                self.experiment_logger.log_error(e, "Experiment execution")
                self.experiment_logger.finalize_experiment()
            raise
        
        # Save results if requested
        if config.save_results:
            await self._save_experiment_results(experiment_id, experiment_results)
        
        self.experiment_results.append(experiment_results)
        
        # Export conversation data if tracking was enabled
        if config.enable_conversation_tracking:
            conversation_file = os.path.join(self.results_dir, f"conversations_{experiment_id}.csv")
            conversation_tracker.export_conversations_csv(conversation_file)
            self.logger.info(f"Conversation data exported to {conversation_file}")
        
        self.logger.info(f"Experiment {experiment_id} completed successfully")
        
        # Reset current experiment
        self.current_experiment_id = None
        self.experiment_logger = None
        
        return experiment_results
    
    def _serialize_game_result(self, result: GameResult) -> Dict[str, Any]:
        """Convert GameResult to serializable format."""
        return {
            "game_type": result.game_type.value,
            "participants": result.participants,
            "rounds": result.rounds,
            "actions_history": [
                (name, action.value) for name, action in result.actions_history
            ],
            "payoffs": result.payoffs,
            "cooperation_rates": result.cooperation_rates,
            "winner": result.winner,
            "additional_metrics": result.additional_metrics
        }
    
    async def _save_experiment_results(
        self,
        experiment_id: str,
        results: Dict[str, Any]
    ) -> None:
        """Save experiment results to file."""
        filename = f"experiment_{experiment_id}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def get_agent_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered agents."""
        stats = {}
        
        for name, agent in self.agents.items():
            stats[name] = {
                "strategy": agent.strategy,
                "total_games": len(agent.state.payoff_history),
                "average_payoff": (
                    sum(agent.state.payoff_history) / len(agent.state.payoff_history)
                    if agent.state.payoff_history else 0.0
                ),
                "cooperation_rate": agent.get_cooperation_rate(),
                "reputation": agent.state.reputation,
                "trust_scores": agent.state.trust_scores.copy(),
                "knowledge_count": len(agent.state.knowledge_base)
            }
        
        return stats
    
    def reset_all_agents(self) -> None:
        """Reset all agents to initial state."""
        for agent in self.agents.values():
            agent.state.trust_scores.clear()
            agent.state.knowledge_base.clear()
            agent.state.cooperation_history.clear()
            agent.state.payoff_history.clear()
            agent.state.reputation = 0.5
        
        self.logger.info("All agents reset to initial state")
    
    def create_standard_agent_set(self, use_llm: bool = False) -> None:
        """標準的なエージェントセットを作成する。
        
        Args:
            use_llm: LLMエージェントを使用するか
        """
        agent_configs = [
            ("Alice_Cooperative", "cooperative"),
            ("Bob_Competitive", "competitive"),
            ("Charlie_TitForTat", "tit_for_tat"),
            ("Diana_Adaptive", "adaptive"),
            ("Eve_Random", "random")
        ]
        
        for name, agent_type in agent_configs:
            self.create_agent(agent_type, name, use_llm=use_llm)
        
        agent_type_str = "LLM" if use_llm else "ルールベース"
        self.logger.info(f"{agent_type_str}エージェントセットを作成: {list(self.agents.keys())}")
    
    async def quick_demo(self, use_llm: bool = False) -> Dict[str, Any]:
        """システムのクイックデモを実行する。
        
        Args:
            use_llm: LLMエージェントを使用するか
        """
        demo_type = "LLM" if use_llm else "ルールベース"
        self.logger.info(f"{demo_type}デモを実行中")
        
        # エージェントが存在しない場合は作成
        if not self.agents:
            self.create_standard_agent_set(use_llm=use_llm)
        
        # シンプルな実験を実行
        config = ExperimentConfig(
            game_types=[GameType.PRISONERS_DILEMMA, GameType.KNOWLEDGE_SHARING],
            agent_types=list(set(agent.strategy for agent in self.agents.values())),
            num_rounds=5 if use_llm else 10,  # LLM使用時は短縮
            num_repetitions=1,
            save_results=True,
            enable_conversation_tracking=use_llm,  # LLM使用時のみ会話追跡
            enable_detailed_logging=use_llm,
            experiment_description=f"{demo_type}エージェントによるデモ実験"
        )
        
        return await self.run_experiment(config)