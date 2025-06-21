#!/usr/bin/env python
"""
会話履歴管理とトレーシング機能を完備したマルチエージェント実験
人間らしいコミュニケーションと記憶による創発的問題解決
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from agents import Runner, handoff
from agents.tracing import trace

from src.agents.conversational_game_agent import ConversationalGameAgent, ConversationalCoordinator, AgentMemory
from src.game_theory.strategies import Strategy, Action
from src.game_theory.games import GameType


class ConversationalExperiment:
    """会話重視のマルチエージェント実験"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.experiment_id = f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trace_id = f"experiment_{self.experiment_id}"
        
        self.results = {
            "experiment_id": self.experiment_id,
            "experiment_name": experiment_name,
            "start_time": datetime.now().isoformat(),
            "conversations": [],
            "game_interactions": [],
            "relationship_evolution": [],
            "emergent_insights": []
        }
    
    def create_conversational_agents(self) -> List[ConversationalGameAgent]:
        """人間らしい個性を持つエージェントを作成"""
        
        agent_configs = [
            {
                "name": "Alice",
                "strategy": Strategy.COOPERATIVE,
                "personality": "温かく協力的で、他者の幸福を心から願う理想主義者。過去の経験から人を信じることの大切さを学んだ"
            },
            {
                "name": "Bob", 
                "strategy": Strategy.COMPETITIVE,
                "personality": "分析的で戦略的思考を好む現実主義者。効率と結果を重視するが、公平性も大切にする"
            },
            {
                "name": "Charlie",
                "strategy": Strategy.TIT_FOR_TAT,
                "personality": "正義感が強く、公平性を何より重視する。相手の行動に応じて柔軟に対応する経験豊富な仲裁者"
            }
        ]
        
        agents = []
        for config in agent_configs:
            agent = ConversationalGameAgent(
                name=config["name"],
                strategy=config["strategy"],
                personality=config["personality"],
                memory_system=AgentMemory()
            )
            agents.append(agent)
            
            print(f"✅ {config['name']} を作成: {config['personality'][:50]}...")
        
        return agents
    
    async def run_introductory_conversations(self, agents: List[ConversationalGameAgent]):
        """初期の自己紹介と関係構築"""
        print(f"\n👋 自己紹介フェーズ")
        
        with trace(f"{self.trace_id}_introductions"):
            # 各エージェントが自己紹介
            for i, agent in enumerate(agents):
                introduction_prompt = """
他のエージェントの皆さんに自己紹介をしてください。

以下について話してください：
- あなたの名前と性格
- どのような価値観を大切にしているか
- 他の人との関係でどんなことを重視するか
- 今日の交流への期待

自然で親しみやすい雰囲気で話してください。
"""
                
                intro = await agent.converse_with_memory(
                    introduction_prompt, 
                    "group_introduction"
                )
                
                print(f"\n{agent.name}: {intro}")
                
                # 他のエージェントがこの自己紹介を聞いて反応
                for other_agent in agents:
                    if other_agent != agent:
                        reaction_prompt = f"""
{agent.name}さんが次のように自己紹介しました：

"{intro}"

この自己紹介について、あなたの感想や共感した部分、興味を持った点などを
{agent.name}さんに向けて自然に話してください。
"""
                        
                        reaction = await other_agent.converse_with_memory(
                            reaction_prompt,
                            agent.name
                        )
                        
                        print(f"  → {other_agent.name}: {reaction}")
        
        self.results["conversations"].append({
            "phase": "introductions",
            "timestamp": datetime.now().isoformat(),
            "participants": [agent.name for agent in agents]
        })
    
    async def run_conversational_game_session(
        self, 
        agents: List[ConversationalGameAgent],
        game_type: GameType,
        rounds: int = 3
    ):
        """会話重視のゲーム理論セッション"""
        print(f"\n🎮 {game_type.value} 会話セッション ({rounds}ラウンド)")
        
        with trace(f"{self.trace_id}_game_{game_type.value}"):
            game_results = []
            
            # ペアごとにゲームを実行
            for i in range(len(agents)):
                for j in range(i + 1, len(agents)):
                    agent1, agent2 = agents[i], agents[j]
                    
                    print(f"\n--- {agent1.name} vs {agent2.name} ---")
                    
                    # ゲーム前の会話
                    pre_game_prompt = f"""
{agent2.name}さん、これから{game_type.value}をプレイします。

ゲームを始める前に、お互いの考えや戦略について話し合いませんか？
相手を知ることで、より意味のある相互作用ができると思います。

あなたの考えを{agent2.name}さんに伝えてください。
"""
                    
                    conversation1 = await agent1.converse_with_memory(pre_game_prompt, agent2.name)
                    print(f"{agent1.name}: {conversation1}")
                    
                    response_prompt = f"""
{agent1.name}さんが次のように話しかけています：

"{conversation1}"

{agent1.name}さんに対して、あなたの考えや感情を率直に返答してください。
"""
                    
                    conversation2 = await agent2.converse_with_memory(response_prompt, agent1.name)
                    print(f"{agent2.name}: {conversation2}")
                    
                    # ラウンドごとのゲーム実行
                    for round_num in range(1, rounds + 1):
                        print(f"\n  ラウンド {round_num}")
                        
                        # ゲーム状況の設定
                        game_context = {
                            "round": round_num,
                            "total_rounds": rounds,
                            "opponent": agent2.name if agent1 else agent1.name
                        }
                        
                        # 意思決定（記憶と会話履歴を活用）
                        action1, reasoning1 = await agent1.make_game_decision_with_memory(
                            game_type, agent2.name, game_context
                        )
                        
                        action2, reasoning2 = await agent2.make_game_decision_with_memory(
                            game_type, agent1.name, game_context
                        )
                        
                        # 利得計算
                        payoff1, payoff2 = self._calculate_payoff(action1, action2)
                        
                        # 結果の記録
                        game_result = {
                            "round": round_num,
                            "agent1": agent1.name,
                            "agent2": agent2.name,
                            "action1": action1.value,
                            "action2": action2.value,
                            "payoff1": payoff1,
                            "payoff2": payoff2,
                            "reasoning1": reasoning1,
                            "reasoning2": reasoning2,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        game_results.append(game_result)
                        
                        # 相手の行動を記録
                        agent1.update_opponent_action(len(agent1.memory.game_history) - 1, action2)
                        agent2.update_opponent_action(len(agent2.memory.game_history) - 1, action1)
                        
                        print(f"    {agent1.name}: {action1.value} (利得: {payoff1})")
                        print(f"    {agent2.name}: {action2.value} (利得: {payoff2})")
                        
                        # ラウンド後の感想交換
                        if round_num == rounds:  # 最終ラウンド後
                            reflection_prompt = f"""
{agent2.name}さんとの{game_type.value}が終わりました。

今回のゲームを通じて感じたことや学んだことを、
{agent2.name}さんに向けて話してください。

相手の戦略や人柄についての印象、今後の関係について等、
率直な感想をお聞かせください。
"""
                            
                            reflection1 = await agent1.converse_with_memory(reflection_prompt, agent2.name)
                            reflection2 = await agent2.converse_with_memory(reflection_prompt, agent1.name)
                            
                            print(f"\n{agent1.name}の感想: {reflection1}")
                            print(f"{agent2.name}の感想: {reflection2}")
            
            self.results["game_interactions"].append({
                "game_type": game_type.value,
                "results": game_results,
                "timestamp": datetime.now().isoformat()
            })
            
            return game_results
    
    def _calculate_payoff(self, action1: Action, action2: Action) -> tuple[float, float]:
        """利得計算"""
        if action1 == Action.COOPERATE and action2 == Action.COOPERATE:
            return 3.0, 3.0
        elif action1 == Action.COOPERATE and action2 == Action.DEFECT:
            return 0.0, 5.0
        elif action1 == Action.DEFECT and action2 == Action.COOPERATE:
            return 5.0, 0.0
        else:
            return 1.0, 1.0
    
    async def analyze_relationship_evolution(self, agents: List[ConversationalGameAgent]):
        """関係性の進化を分析"""
        print(f"\n📈 関係性分析フェーズ")
        
        with trace(f"{self.trace_id}_relationship_analysis"):
            relationship_data = {}
            
            for agent in agents:
                agent_relationships = {}
                summary = agent.get_conversation_summary()
                
                for partner in summary["conversation_partners"]:
                    if partner != agent.name and partner != "ConversationCoordinator":
                        trust_score = agent.memory.trust_scores.get(partner, 0.5)
                        relationship_memory = agent.memory.relationship_memories.get(partner, {})
                        
                        agent_relationships[partner] = {
                            "trust_score": trust_score,
                            "interaction_count": relationship_memory.get("interaction_count", 0),
                            "notable_moments": relationship_memory.get("notable_moments", [])
                        }
                
                relationship_data[agent.name] = agent_relationships
                
                # エージェント自身の関係性に対する内省
                reflection_prompt = """
これまでの他のエージェントとの交流を振り返って、

1. 最も印象に残った相互作用
2. 信頼関係がどのように変化したか
3. 相手から学んだこと
4. 今後の関係への期待

について、率直に話してください。
"""
                
                personal_reflection = await agent.converse_with_memory(reflection_prompt)
                print(f"\n{agent.name}の内省:")
                print(personal_reflection)
                
                relationship_data[agent.name]["personal_reflection"] = personal_reflection
            
            self.results["relationship_evolution"].append({
                "timestamp": datetime.now().isoformat(),
                "relationship_data": relationship_data
            })
            
            return relationship_data
    
    async def emergent_problem_solving(
        self, 
        agents: List[ConversationalGameAgent],
        coordinator: ConversationalCoordinator
    ):
        """創発的問題解決セッション"""
        print(f"\n🧠 創発的問題解決フェーズ")
        
        complex_problem = """
「AI時代における人間性の保持と技術進歩の調和」

課題：
人工知能の急速な発展により、多くの仕事が自動化される一方で、
人間らしさや創造性、感情的なつながりの価値が問われています。

どのように技術進歩を活用しながら、人間性を保持し、
より豊かな社会を築くことができるでしょうか？

それぞれの経験や価値観を踏まえて、建設的な議論をお願いします。
"""
        
        with trace(f"{self.trace_id}_emergent_problem_solving"):
            # グループディスカッション
            discussion_result = await coordinator.facilitate_group_discussion(
                "AI時代における人間性の保持と技術進歩の調和",
                {"problem_statement": complex_problem}
            )
            
            # 個別の深い思考
            individual_insights = {}
            for agent in agents:
                deep_thinking_prompt = f"""
先ほどの議論を踏まえて、この問題についてさらに深く考えてみてください。

他の方の意見を聞いて新たに気づいたことや、
あなた独自の視点から見た解決のアイデアを
時間をかけて考えてください。

既存の枠にとらわれない、創造的で実践的な提案をお願いします。
"""
                
                insight = await agent.converse_with_memory(deep_thinking_prompt, "deep_thinking")
                individual_insights[agent.name] = insight
                
                print(f"\n{agent.name}の深い洞察:")
                print(insight)
            
            # 統合的解決策の創出
            integration_prompt = f"""
皆さんの洞察を統合して、創発的で実現可能な解決策を提案してください：

{chr(10).join([f"{name}: {insight}" for name, insight in individual_insights.items()])}

単独では思いつかなかった、集団知によって生まれた新しいアイデアを
具体的に提示してください。
"""
            
            runner = Runner()
            integration_result = await runner.run(coordinator, integration_prompt)
            
            print(f"\n統合的解決策:")
            print(integration_result.final_output)
            
            self.results["emergent_insights"].append({
                "problem": complex_problem,
                "discussion": discussion_result,
                "individual_insights": individual_insights,
                "integrated_solution": integration_result.final_output,
                "timestamp": datetime.now().isoformat()
            })
            
            return integration_result.final_output
    
    async def run_full_experiment(self):
        """完全な会話実験を実行"""
        print(f"🚀 会話重視マルチエージェント実験開始")
        print(f"実験ID: {self.experiment_id}")
        print("=" * 60)
        
        with trace(self.trace_id):
            # 1. エージェント作成
            agents = self.create_conversational_agents()
            coordinator = ConversationalCoordinator(agents)
            
            # 2. 初期会話と関係構築
            await self.run_introductory_conversations(agents)
            
            # 3. ゲーム理論的相互作用（記憶と会話重視）
            await self.run_conversational_game_session(agents, GameType.PRISONERS_DILEMMA, rounds=3)
            
            # 4. 関係性の進化分析
            await self.analyze_relationship_evolution(agents)
            
            # 5. 創発的問題解決
            await self.emergent_problem_solving(agents, coordinator)
            
            # 6. 最終的な会話まとめ
            print(f"\n💬 最終会話セッション")
            
            final_prompt = """
今日の交流全体を振り返って、最も印象深かった瞬間や
学んだことについて話してください。

この経験があなたにとってどのような意味を持つかも
含めて、感想を聞かせてください。
"""
            
            for agent in agents:
                final_reflection = await agent.converse_with_memory(final_prompt, "final_session")
                print(f"\n{agent.name}の最終感想:")
                print(final_reflection)
        
        # 結果保存
        self._save_results()
        
        print(f"\n✅ 実験完了!")
        print(f"詳細な会話履歴とトレースが保存されました")
    
    def _save_results(self):
        """結果とトレースを保存"""
        os.makedirs("results", exist_ok=True)
        
        # メイン結果
        self.results["end_time"] = datetime.now().isoformat()
        
        with open(f"results/{self.experiment_id}_conversation_results.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 結果保存: results/{self.experiment_id}_conversation_results.json")


async def main():
    """メイン実行関数"""
    print("🌟 会話履歴管理付きマルチエージェント実験")
    
    # 環境チェック
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        experiment = ConversationalExperiment("conversational_multiagent")
        await experiment.run_full_experiment()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())