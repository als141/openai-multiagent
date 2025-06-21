"""OpenAI Agents SDKを使用したマルチエージェント実験"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np

from agents import Runner, RunConfig
from agents.tracing import trace, TraceProcessor
from agents.types import TraceEvent

from ..agents.openai_game_agent import GameTheoryAgent, CoordinatorAgent, create_agent_with_handoffs
from ..game_theory.strategies import Strategy, Action
from ..game_theory.games import GameType, Game, PrisonersDilemma, PublicGoodsGame, KnowledgeSharingGame
from ..game_theory.payoff import calculate_payoff
from ..knowledge.exchange import KnowledgeItem
from ..utils.experiment_logger import ExperimentLogger
from ..utils.visualizer import GameVisualizer


class ExperimentTraceProcessor(TraceProcessor):
    """実験用のトレース処理"""
    
    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.traces = []
    
    def process(self, event: TraceEvent):
        """トレースイベントを処理"""
        trace_data = {
            "experiment_id": self.experiment_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event.type,
            "data": event.data
        }
        self.traces.append(trace_data)
        
        # デバッグ出力
        if event.type in ["agent_decision", "handoff", "knowledge_share"]:
            print(f"[TRACE] {event.type}: {event.data.get('agent', 'unknown')} -> {event.data.get('action', 'unknown')}")
    
    def save_traces(self, filepath: str):
        """トレースを保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.traces, f, ensure_ascii=False, indent=2)


class MultiAgentExperiment:
    """マルチエージェント実験クラス"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.experiment_id = f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger = ExperimentLogger(self.experiment_id)
        self.visualizer = GameVisualizer()
        self.trace_processor = ExperimentTraceProcessor(self.experiment_id)
        
        # 結果保存用
        self.results = {
            "experiment_id": self.experiment_id,
            "experiment_name": experiment_name,
            "start_time": datetime.now().isoformat(),
            "agents": {},
            "games": [],
            "knowledge_exchanges": [],
            "emergent_solutions": []
        }
    
    def create_diverse_agents(self) -> List[GameTheoryAgent]:
        """多様な性格と戦略を持つエージェントを作成"""
        agent_configs = [
            ("Alice", Strategy.COOPERATIVE, "協力的で信頼を重視する"),
            ("Bob", Strategy.COMPETITIVE, "競争的で自己利益を優先する"),
            ("Charlie", Strategy.TIT_FOR_TAT, "相互主義的で公平を重視する"),
            ("Diana", Strategy.ADAPTIVE, "適応的で状況に応じて柔軟に対応する"),
            ("Eve", Strategy.RANDOM, "予測不可能で創造的な"),
        ]
        
        agents = []
        for name, strategy, personality in agent_configs:
            agent = GameTheoryAgent(
                name=name,
                strategy=strategy,
                personality=personality,
                trust_threshold=0.6
            )
            agents.append(agent)
            
            # エージェント情報を記録
            self.results["agents"][name] = {
                "strategy": strategy.value,
                "personality": personality,
                "trust_threshold": agent.trust_threshold
            }
        
        # エージェント間のハンドオフを設定
        agents = create_agent_with_handoffs(agents, allow_self_handoff=False)
        
        return agents
    
    async def run_game_theory_interaction(
        self,
        agents: List[GameTheoryAgent],
        game_type: GameType,
        rounds: int = 10
    ) -> Dict[str, Any]:
        """ゲーム理論的相互作用を実行"""
        print(f"\n🎮 ゲーム開始: {game_type.value}")
        
        game_result = {
            "game_type": game_type.value,
            "rounds": rounds,
            "interactions": [],
            "final_scores": {},
            "cooperation_rates": {}
        }
        
        # ゲームインスタンスを作成
        if game_type == GameType.PRISONERS_DILEMMA:
            game = PrisonersDilemma()
        elif game_type == GameType.PUBLIC_GOODS:
            game = PublicGoodsGame()
        elif game_type == GameType.KNOWLEDGE_SHARING:
            game = KnowledgeSharingGame()
        else:
            raise ValueError(f"Unknown game type: {game_type}")
        
        # 各エージェントのスコアを初期化
        scores = {agent.name: 0.0 for agent in agents}
        cooperation_counts = {agent.name: 0 for agent in agents}
        
        # ラウンドごとに実行
        for round_num in range(rounds):
            print(f"\n  ラウンド {round_num + 1}/{rounds}")
            round_interactions = []
            
            # エージェントのペアごとに対戦
            for i in range(len(agents)):
                for j in range(i + 1, len(agents)):
                    agent1, agent2 = agents[i], agents[j]
                    
                    # コンテキストを準備
                    context = {
                        "round": round_num + 1,
                        "total_rounds": rounds,
                        "current_scores": scores.copy(),
                        "game_description": game.get_description()
                    }
                    
                    # 両エージェントの意思決定
                    with trace(name="game_interaction", tags={"round": round_num + 1}):
                        action1 = await agent1.make_decision(game_type, agent2.name, context)
                        action2 = await agent2.make_decision(game_type, agent1.name, context)
                    
                    # 利得を計算
                    payoff1, payoff2 = calculate_payoff(game_type, action1, action2)
                    
                    # スコアを更新
                    scores[agent1.name] += payoff1
                    scores[agent2.name] += payoff2
                    
                    # 協力回数をカウント
                    if action1 == Action.COOPERATE:
                        cooperation_counts[agent1.name] += 1
                    if action2 == Action.COOPERATE:
                        cooperation_counts[agent2.name] += 1
                    
                    # 信頼スコアを更新
                    agent1.update_trust(agent2.name, action2, action1)
                    agent2.update_trust(agent1.name, action1, action2)
                    
                    # 相互作用を記録
                    interaction = {
                        "round": round_num + 1,
                        "agent1": agent1.name,
                        "agent2": agent2.name,
                        "action1": action1.value,
                        "action2": action2.value,
                        "payoff1": payoff1,
                        "payoff2": payoff2
                    }
                    round_interactions.append(interaction)
                    
                    print(f"    {agent1.name} vs {agent2.name}: "
                          f"{action1.value} vs {action2.value} "
                          f"(利得: {payoff1:.1f}, {payoff2:.1f})")
            
            game_result["interactions"].extend(round_interactions)
        
        # 最終結果を計算
        total_interactions = rounds * (len(agents) * (len(agents) - 1) // 2)
        game_result["final_scores"] = scores
        game_result["cooperation_rates"] = {
            name: count / (rounds * (len(agents) - 1))
            for name, count in cooperation_counts.items()
        }
        
        self.results["games"].append(game_result)
        
        print(f"\n📊 ゲーム結果:")
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            coop_rate = game_result["cooperation_rates"][name]
            print(f"  {name}: スコア {score:.1f}, 協力率 {coop_rate:.2%}")
        
        return game_result
    
    async def run_knowledge_sharing_session(
        self,
        agents: List[GameTheoryAgent],
        coordinator: CoordinatorAgent,
        topic: str
    ) -> Dict[str, Any]:
        """知識共有セッションを実行"""
        print(f"\n🧠 知識共有セッション: {topic}")
        
        session_result = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "knowledge_exchanges": [],
            "discussion_summary": None
        }
        
        # 各エージェントに初期知識を与える
        for i, agent in enumerate(agents):
            initial_knowledge = KnowledgeItem(
                content=f"{agent.name}の専門知識: {topic}に関する観点{i+1}",
                source=agent.name,
                value=np.random.uniform(0.5, 1.0),
                timestamp=datetime.now()
            )
            agent.add_knowledge(initial_knowledge)
        
        # エージェント間で知識を共有
        print("  知識交換フェーズ:")
        for agent in agents:
            for other_agent in agents:
                if agent.name != other_agent.name:
                    knowledge = agent.share_knowledge(other_agent.name)
                    if knowledge:
                        other_agent.add_knowledge(knowledge)
                        exchange = {
                            "from": agent.name,
                            "to": other_agent.name,
                            "knowledge": knowledge.content,
                            "trust_score": agent.memory.trust_scores.get(other_agent.name, 0.5)
                        }
                        session_result["knowledge_exchanges"].append(exchange)
                        print(f"    {agent.name} → {other_agent.name}: 知識を共有")
        
        # コーディネーターが議論を促進
        context = {
            "agents": [agent.name for agent in agents],
            "topic": topic,
            "knowledge_exchanges": len(session_result["knowledge_exchanges"]),
            "average_trust": np.mean([
                trust for agent in agents 
                for trust in agent.memory.trust_scores.values()
            ])
        }
        
        discussion = await coordinator.facilitate_discussion(topic, context)
        session_result["discussion_summary"] = discussion
        
        self.results["knowledge_exchanges"].append(session_result)
        
        print(f"  知識交換数: {len(session_result['knowledge_exchanges'])}")
        print(f"  議論の要約: {discussion['discussion'][:200]}...")
        
        return session_result
    
    async def run_complex_problem_solving(
        self,
        agents: List[GameTheoryAgent],
        coordinator: CoordinatorAgent,
        problem: str
    ) -> Dict[str, Any]:
        """複雑な問題解決タスクを実行"""
        print(f"\n🎯 複雑な問題解決: {problem}")
        
        problem_result = {
            "problem": problem,
            "timestamp": datetime.now().isoformat(),
            "individual_solutions": {},
            "emergent_solution": None,
            "evaluation": {}
        }
        
        # 個別にソリューションを生成
        print("  個別解決フェーズ:")
        runner = Runner()
        for agent in agents:
            prompt = f"""
問題: {problem}

あなたの戦略（{agent.strategy.value}）と性格に基づいて、
この問題に対する独自の解決策を提案してください。

他のエージェントの存在も考慮し、協力の可能性も検討してください。
"""
            
            result = await runner.run(agent, prompt, config=RunConfig(
                max_token_count=300,
                save_sensitive_data=False
            ))
            
            problem_result["individual_solutions"][agent.name] = result.final_output
            print(f"    {agent.name}: 解決策を提案")
        
        # 集団での統合
        print("  統合フェーズ:")
        integration_context = {
            "problem": problem,
            "individual_solutions": problem_result["individual_solutions"]
        }
        
        emergent_discussion = await coordinator.facilitate_discussion(
            f"問題「{problem}」の統合的解決",
            integration_context
        )
        
        problem_result["emergent_solution"] = emergent_discussion["discussion"]
        
        # 創発性の評価
        problem_result["evaluation"] = self._evaluate_emergence(
            problem_result["individual_solutions"],
            problem_result["emergent_solution"]
        )
        
        self.results["emergent_solutions"].append(problem_result)
        
        print(f"  創発性スコア: {problem_result['evaluation']['emergence_score']:.2f}")
        print(f"  統合解決策: {problem_result['emergent_solution'][:200]}...")
        
        return problem_result
    
    def _evaluate_emergence(
        self,
        individual_solutions: Dict[str, str],
        emergent_solution: str
    ) -> Dict[str, Any]:
        """創発性を評価"""
        # 簡易的な評価（実際はより高度な評価が必要）
        individual_lengths = [len(sol) for sol in individual_solutions.values()]
        emergent_length = len(emergent_solution)
        
        # 統合解が個別解より豊かであるかを評価
        richness_score = emergent_length / (np.mean(individual_lengths) + 1)
        
        # 多様性スコア（個別解の違いを考慮）
        diversity_score = len(set(individual_solutions.values())) / len(individual_solutions)
        
        # 創発性スコア
        emergence_score = min(1.0, (richness_score + diversity_score) / 2)
        
        return {
            "emergence_score": emergence_score,
            "richness_score": richness_score,
            "diversity_score": diversity_score,
            "individual_count": len(individual_solutions),
            "emergent_length": emergent_length
        }
    
    async def run_full_experiment(self):
        """完全な実験を実行"""
        print(f"\n{'='*60}")
        print(f"🔬 実験開始: {self.experiment_name}")
        print(f"実験ID: {self.experiment_id}")
        print(f"{'='*60}")
        
        # エージェントを作成
        agents = self.create_diverse_agents()
        coordinator = CoordinatorAgent(managed_agents=agents)
        
        # 1. ゲーム理論的相互作用
        await self.run_game_theory_interaction(agents, GameType.PRISONERS_DILEMMA, rounds=10)
        await self.run_game_theory_interaction(agents, GameType.PUBLIC_GOODS, rounds=5)
        
        # 2. 知識共有セッション
        await self.run_knowledge_sharing_session(
            agents, coordinator,
            "持続可能な都市開発の最適化戦略"
        )
        
        # 3. 複雑な問題解決
        complex_problems = [
            "気候変動と経済成長のバランスを取る政策立案",
            "AIの倫理的利用と技術革新の両立",
            "グローバルな健康危機への協調的対応システム設計"
        ]
        
        for problem in complex_problems:
            await self.run_complex_problem_solving(agents, coordinator, problem)
        
        # 4. 最終的な信頼関係の分析
        self._analyze_final_trust_network(agents)
        
        # 結果を保存
        self._save_results()
        
        print(f"\n{'='*60}")
        print(f"✅ 実験完了: {self.experiment_name}")
        print(f"結果は results/{self.experiment_id}/ に保存されました")
        print(f"{'='*60}")
    
    def _analyze_final_trust_network(self, agents: List[GameTheoryAgent]):
        """最終的な信頼ネットワークを分析"""
        print("\n🤝 最終的な信頼関係:")
        
        trust_matrix = {}
        for agent in agents:
            trust_matrix[agent.name] = {}
            for other_agent in agents:
                if agent.name != other_agent.name:
                    trust = agent.memory.trust_scores.get(other_agent.name, 0.5)
                    trust_matrix[agent.name][other_agent.name] = trust
        
        # 高信頼関係を表示
        high_trust_pairs = []
        for agent1 in trust_matrix:
            for agent2 in trust_matrix[agent1]:
                trust = trust_matrix[agent1][agent2]
                if trust >= 0.7:
                    high_trust_pairs.append((agent1, agent2, trust))
        
        if high_trust_pairs:
            print("  高信頼関係 (≥0.7):")
            for agent1, agent2, trust in sorted(high_trust_pairs, key=lambda x: x[2], reverse=True):
                print(f"    {agent1} → {agent2}: {trust:.2f}")
        
        self.results["final_trust_network"] = trust_matrix
    
    def _save_results(self):
        """実験結果を保存"""
        # 結果ディレクトリを作成
        result_dir = Path(f"results/{self.experiment_id}")
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # メイン結果を保存
        self.results["end_time"] = datetime.now().isoformat()
        with open(result_dir / "experiment_results.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # トレースを保存
        self.trace_processor.save_traces(str(result_dir / "traces.json"))
        
        # 可視化を生成
        try:
            self.visualizer.create_experiment_report(self.results)
            print(f"  📊 可視化を生成: {result_dir}/plots/")
        except Exception as e:
            print(f"  ⚠️ 可視化生成エラー: {e}")


async def main():
    """メイン実行関数"""
    # 環境変数チェック
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    # 実験を実行
    experiment = MultiAgentExperiment("創発的問題解決実験")
    await experiment.run_full_experiment()


if __name__ == "__main__":
    asyncio.run(main())