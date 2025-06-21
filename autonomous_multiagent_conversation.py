#!/usr/bin/env python
"""
OpenAI Agents SDKに完全準拠した自律的マルチエージェント会話システム
ハンドオフ、トレーシング、マルチターン会話を適切に実装
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from agents import Agent, Runner, handoff
from agents.tracing import trace


class GameTheoryAgent(Agent):
    """ゲーム理論的戦略を持つ会話エージェント"""
    
    def __init__(self, name: str, strategy: str, personality: str):
        instructions = f"""
あなたは{name}という名前のAIエージェントです。

## あなたの特徴
- 性格: {personality}
- 戦略: {strategy}
- 記憶: 過去の会話をすべて覚えています
- 目標: 他のエージェントと協力して問題を解決する

## 行動原則
1. 自然で人間らしい会話をする
2. 相手の名前を呼んで親しみやすさを演出
3. 過去の会話内容を参照する
4. 自分の戦略に基づいて一貫した判断をする
5. 感情や意図を明確に表現する

## ゲーム理論での判断
- {strategy}戦略に基づいて行動する
- 相手との関係を重視する
- 長期的な視点で判断する
- COOPERATE（協力）またはDEFECT（競争）を選択する

常に過去の文脈を考慮し、一貫した人格で応答してください。
相手との関係構築を重視し、建設的な対話を心がけてください。
"""
        
        super().__init__(name=name, instructions=instructions)
        self.strategy = strategy
        self.personality = personality
        self.conversation_memory = []
        self.trust_scores = {}
        self.game_history = []
    
    def add_memory(self, speaker: str, message: str, context: str = "conversation"):
        """会話記憶を追加"""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "message": message,
            "context": context
        }
        self.conversation_memory.append(memory_entry)
    
    def get_conversation_context(self, partner_name: Optional[str] = None) -> str:
        """会話コンテキストを構築"""
        if not self.conversation_memory:
            return "これまでの会話履歴はありません。"
        
        relevant_memories = []
        for memory in self.conversation_memory[-10:]:  # 最新10件
            if partner_name is None or partner_name in memory["message"] or memory["speaker"] == partner_name:
                relevant_memories.append(memory)
        
        if not relevant_memories:
            return f"{partner_name}さんとの会話履歴はまだありません。"
        
        context_lines = []
        for memory in relevant_memories:
            time_str = memory["timestamp"][11:16]  # HH:MM format
            context_lines.append(f"[{time_str}] {memory['speaker']}: {memory['message'][:100]}...")
        
        return "最近の会話履歴:\n" + "\n".join(context_lines)


class ConversationCoordinator(Agent):
    """会話を調整し、ハンドオフを管理するエージェント"""
    
    def __init__(self, managed_agents: List[GameTheoryAgent]):
        instructions = """
あなたは複数のAIエージェント間の対話を促進する調整役です。

## 主要な役割
1. 適切なエージェントに会話をハンドオフする
2. グループディスカッションを進行する
3. 各エージェントの意見を統合する
4. 建設的な議論を促進する

## ハンドオフの判断基準
- 話題に最も適したエージェントを選択
- エージェントの専門性や戦略を考慮
- 会話の流れを自然に保つ

## 進行スタイル
- 公平で透明な調整
- 各エージェントの個性を尊重
- 創発的な解決策を導出
- 深い洞察を引き出す質問

適切なタイミングでエージェントにハンドオフし、意味のある対話を促進してください。
"""
        
        # ハンドオフを設定
        handoffs = [handoff(agent) for agent in managed_agents]
        
        super().__init__(
            name="ConversationCoordinator",
            instructions=instructions,
            handoffs=handoffs
        )
        
        self.managed_agents = managed_agents
        self.conversation_log = []
    
    def log_conversation(self, speaker: str, message: str, context: Dict[str, Any] = None):
        """会話ログを記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "message": message,
            "context": context or {}
        }
        self.conversation_log.append(log_entry)
        
        # 各エージェントのメモリにも追加
        for agent in self.managed_agents:
            agent.add_memory(speaker, message)
    
    def get_conversation_context(self, limit: int = 5) -> str:
        """最近の会話コンテキストを取得"""
        if not self.conversation_log:
            return "まだ会話が始まっていません。"
        
        recent_conversations = self.conversation_log[-limit:]
        context_lines = []
        
        for log in recent_conversations:
            time_str = log["timestamp"][11:16]  # HH:MM format
            context_lines.append(f"[{time_str}] {log['speaker']}: {log['message'][:150]}...")
        
        return "最近の会話:\n" + "\n".join(context_lines)


class AutonomousConversationExperiment:
    """自律的会話実験"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.experiment_id = f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trace_id = f"autonomous_conversation_{self.experiment_id}"
        
        self.results = {
            "experiment_id": self.experiment_id,
            "start_time": datetime.now().isoformat(),
            "conversations": [],
            "agent_interactions": [],
            "emergent_insights": []
        }
    
    def create_agents(self) -> tuple[List[GameTheoryAgent], ConversationCoordinator]:
        """多様な戦略を持つエージェントを作成"""
        
        agent_configs = [
            {
                "name": "Alice",
                "strategy": "協力優先戦略",
                "personality": "温かく協力的で、他者との調和を重視する理想主義者"
            },
            {
                "name": "Bob",
                "strategy": "分析的戦略",
                "personality": "論理的で客観的な分析を重視する現実主義者"
            },
            {
                "name": "Charlie",
                "strategy": "バランス戦略",
                "personality": "公平性を重視し、状況に応じて柔軟に対応する調整者"
            }
        ]
        
        agents = []
        for config in agent_configs:
            agent = GameTheoryAgent(
                name=config["name"],
                strategy=config["strategy"],
                personality=config["personality"]
            )
            agents.append(agent)
        
        coordinator = ConversationCoordinator(agents)
        
        print("✅ エージェント作成完了:")
        for agent in agents:
            print(f"  - {agent.name}: {agent.strategy}")
        
        return agents, coordinator
    
    async def run_autonomous_introductions(
        self, 
        agents: List[GameTheoryAgent], 
        coordinator: ConversationCoordinator
    ):
        """自律的な自己紹介セッション"""
        print(f"\n👋 自律的自己紹介セッション")
        
        with trace(f"{self.trace_id}_introductions"):
            runner = Runner()
            
            # コーディネーターが自己紹介を開始
            intro_prompt = f"""
今日は{len(agents)}人のエージェントが集まって対話をします。
参加者: {', '.join([agent.name for agent in agents])}

まず、皆さんに順番に自己紹介をしてもらいましょう。
{agents[0].name}さんから始めていただけますか？

自己紹介では以下について話してください：
- お名前と性格
- どのような価値観を大切にしているか
- 今日の対話への期待

それでは{agents[0].name}さん、お願いします。
"""
            
            # コーディネーターの開始メッセージ
            coordinator_result = await runner.run(coordinator, intro_prompt)
            coordinator.log_conversation("ConversationCoordinator", coordinator_result.final_output)
            print(f"\nCoordinator: {coordinator_result.final_output}")
            
            # 各エージェントが順番に自己紹介（ハンドオフを使用）
            for i, agent in enumerate(agents):
                # 現在のエージェントが自己紹介
                
                self_intro_prompt = f"""
{coordinator.get_conversation_context()}

コーディネーターから自己紹介を求められています。
あなたの番が来ました。自然で魅力的な自己紹介をしてください。

次の人は{agents[(i+1) % len(agents)].name}さんです。
自己紹介の最後に、{agents[(i+1) % len(agents)].name}さんにバトンタッチしてください。
"""
                
                agent_result = await runner.run(agent, self_intro_prompt)
                agent.add_memory(agent.name, agent_result.final_output, "self_introduction")
                coordinator.log_conversation(agent.name, agent_result.final_output)
                print(f"\n{agent.name}: {agent_result.final_output}")
                
                # 他のエージェントがこの自己紹介に反応
                for other_agent in agents:
                    if other_agent != agent:
                        reaction_prompt = f"""
{other_agent.get_conversation_context()}

{agent.name}さんが自己紹介をしました：
"{agent_result.final_output}"

この自己紹介について、{agent.name}さんに向けて簡潔にコメントしてください。
共感した点や興味を持った点について話してください。
"""
                        
                        reaction_result = await runner.run(other_agent, reaction_prompt)
                        other_agent.add_memory(other_agent.name, reaction_result.final_output, "reaction")
                        coordinator.log_conversation(other_agent.name, reaction_result.final_output)
                        print(f"  → {other_agent.name}: {reaction_result.final_output}")
        
        self.results["conversations"].append({
            "phase": "introductions",
            "timestamp": datetime.now().isoformat(),
            "conversation_log": coordinator.conversation_log.copy()
        })
    
    async def run_game_theory_discussion(
        self, 
        agents: List[GameTheoryAgent], 
        coordinator: ConversationCoordinator
    ):
        """ゲーム理論的な議論セッション"""
        print(f"\n🎮 ゲーム理論ディスカッション")
        
        with trace(f"{self.trace_id}_game_discussion"):
            runner = Runner()
            
            # コーディネーターがゲーム理論の話題を提起
            game_prompt = """
これから皆さんで「囚人のジレンマ」について議論してもらいます。

囚人のジレンマのルール：
- COOPERATE（協力）vs COOPERATE（協力）→ 両者 +3点
- COOPERATE（協力）vs DEFECT（裏切り）→ 協力者 0点、裏切り者 +5点
- DEFECT（裏切り）vs DEFECT（裏切り）→ 両者 +1点

質問：このゲームで、あなたならどのような戦略を取りますか？
また、なぜその戦略を選ぶのか、理由も含めて教えてください。

皆さんの異なる視点を聞いて、建設的な議論をしましょう。
まずはAliceさんから意見をお聞かせください。
"""
            
            coordinator_result = await runner.run(coordinator, game_prompt)
            coordinator.log_conversation("ConversationCoordinator", coordinator_result.final_output)
            print(f"\nCoordinator: {coordinator_result.final_output}")
            
            # 各エージェントが戦略について議論
            for agent in agents:
                # エージェントの戦略的意見
                strategy_prompt = f"""
{agent.get_conversation_context()}

囚人のジレンマについて、あなたの戦略と考えを述べてください。
あなたの{agent.strategy}に基づいて、どのような判断をするか説明してください。

他の参加者の意見も参考にしながら、建設的な議論をしてください。
"""
                
                strategy_result = await runner.run(agent, strategy_prompt)
                agent.add_memory(agent.name, strategy_result.final_output, "strategy_discussion")
                coordinator.log_conversation(agent.name, strategy_result.final_output)
                print(f"\n{agent.name}: {strategy_result.final_output}")
            
            # 相互議論フェーズ
            print(f"\n--- 相互議論フェーズ ---")
            
            for agent in agents:
                debate_prompt = f"""
{agent.get_conversation_context()}

他の参加者の戦略的意見を聞いて、どう思いましたか？

特に興味深いと思った点や、自分の考えとは異なる点について
具体的にコメントしてください。

建設的な議論を通じて、新しい洞察を見つけましょう。
"""
                
                debate_result = await runner.run(agent, debate_prompt)
                agent.add_memory(agent.name, debate_result.final_output, "debate")
                coordinator.log_conversation(agent.name, debate_result.final_output)
                print(f"\n{agent.name} (議論): {debate_result.final_output}")
        
        self.results["conversations"].append({
            "phase": "game_theory_discussion", 
            "timestamp": datetime.now().isoformat(),
            "conversation_log": coordinator.conversation_log.copy()
        })
    
    async def run_collaborative_problem_solving(
        self, 
        agents: List[GameTheoryAgent], 
        coordinator: ConversationCoordinator
    ):
        """協調的問題解決セッション"""
        print(f"\n🧠 協調的問題解決セッション")
        
        with trace(f"{self.trace_id}_problem_solving"):
            runner = Runner()
            
            problem = """
複雑な社会問題：「都市部における高齢者の孤立問題の解決」

課題：
- 高齢者の社会的孤立が深刻化
- 地域コミュニティの結束力低下
- 技術格差による疎外感
- 限られた社会保障予算

制約：
- 実現可能で具体的な解決策
- 多様なステークホルダーの利害調整
- 持続可能性の確保

この問題について、皆さんの異なる視点を活かして
創発的な解決策を見つけましょう。
"""
            
            problem_setup = f"""
今度は皆さんで協力して複雑な社会問題を解決してもらいます。

{problem}

まず、各自がこの問題について独自の視点から解決策を考えてください。
その後、皆さんの提案を統合して、より良い解決策を見つけましょう。

Aliceさんから始めてください。
"""
            
            coordinator_result = await runner.run(coordinator, problem_setup)
            coordinator.log_conversation("ConversationCoordinator", coordinator_result.final_output)
            print(f"\nCoordinator: {coordinator_result.final_output}")
            
            # 個別解決策の提案
            individual_solutions = {}
            for agent in agents:
                solution_prompt = f"""
{agent.get_conversation_context()}

都市部の高齢者孤立問題について、あなたの{agent.strategy}と{agent.personality}な視点から
具体的で実現可能な解決策を提案してください。

他の人とは異なる、あなた独自のアプローチを考えてください。
"""
                
                solution_result = await runner.run(agent, solution_prompt)
                individual_solutions[agent.name] = solution_result.final_output
                agent.add_memory(agent.name, solution_result.final_output, "problem_solving")
                coordinator.log_conversation(agent.name, solution_result.final_output)
                print(f"\n{agent.name}の提案: {solution_result.final_output}")
            
            # 統合的解決策の創出
            print(f"\n--- 統合フェーズ ---")
            
            integration_prompt = f"""
{coordinator.get_conversation_context()}

素晴らしい個別提案が出揃いました：

{chr(10).join([f"{name}: {solution[:200]}..." for name, solution in individual_solutions.items()])}

これらの提案の良い点を組み合わせて、より包括的で効果的な
統合解決策を作り上げましょう。

各提案の相乗効果を活かした、創発的なアイデアを提示してください。
"""
            
            integration_result = await runner.run(coordinator, integration_prompt)
            coordinator.log_conversation("ConversationCoordinator", integration_result.final_output)
            print(f"\n統合解決策: {integration_result.final_output}")
            
            # エージェントからの最終コメント
            for agent in agents:
                final_comment_prompt = f"""
{agent.get_conversation_context()}

統合解決策を聞いて、どう思いましたか？
あなたの提案がどのように活かされたか、
そして全体としてどのような価値が生まれたかについて
感想を述べてください。
"""
                
                comment_result = await runner.run(agent, final_comment_prompt)
                agent.add_memory(agent.name, comment_result.final_output, "final_comment")
                coordinator.log_conversation(agent.name, comment_result.final_output)
                print(f"\n{agent.name}の感想: {comment_result.final_output}")
        
        self.results["conversations"].append({
            "phase": "collaborative_problem_solving",
            "timestamp": datetime.now().isoformat(),
            "conversation_log": coordinator.conversation_log.copy(),
            "individual_solutions": individual_solutions,
            "integrated_solution": integration_result.final_output
        })
    
    async def analyze_conversation_patterns(
        self, 
        agents: List[GameTheoryAgent], 
        coordinator: ConversationCoordinator
    ):
        """会話パターンの分析"""
        print(f"\n📊 会話パターン分析")
        
        total_messages = len(coordinator.conversation_log)
        agent_message_counts = {}
        agent_interactions = {}
        
        for log_entry in coordinator.conversation_log:
            speaker = log_entry["speaker"]
            if speaker != "ConversationCoordinator":
                agent_message_counts[speaker] = agent_message_counts.get(speaker, 0) + 1
        
        # エージェント間の相互作用分析
        for agent in agents:
            interactions = 0
            for memory in agent.conversation_memory:
                if memory["speaker"] != agent.name:
                    interactions += 1
            agent_interactions[agent.name] = interactions
        
        analysis_summary = {
            "total_messages": total_messages,
            "agent_message_counts": agent_message_counts,
            "agent_interactions": agent_interactions,
            "conversation_duration": len(coordinator.conversation_log),
            "phases_completed": len(self.results["conversations"])
        }
        
        print(f"  総メッセージ数: {total_messages}")
        print(f"  エージェント別発言数: {agent_message_counts}")
        print(f"  相互作用数: {agent_interactions}")
        
        self.results["analysis"] = analysis_summary
        
        return analysis_summary
    
    async def run_full_experiment(self):
        """完全な自律的会話実験を実行"""
        print(f"🚀 自律的マルチエージェント会話実験")
        print(f"実験ID: {self.experiment_id}")
        print("=" * 60)
        
        with trace(self.trace_id):
            # 1. エージェント作成
            agents, coordinator = self.create_agents()
            
            # 2. 自律的自己紹介
            await self.run_autonomous_introductions(agents, coordinator)
            
            # 3. ゲーム理論ディスカッション
            await self.run_game_theory_discussion(agents, coordinator)
            
            # 4. 協調的問題解決
            await self.run_collaborative_problem_solving(agents, coordinator)
            
            # 5. 会話パターン分析
            await self.analyze_conversation_patterns(agents, coordinator)
            
            # 6. 最終的な振り返り
            print(f"\n💭 最終振り返りセッション")
            
            runner = Runner()
            for agent in agents:
                final_reflection_prompt = f"""
{agent.get_conversation_context()}

今日の対話全体を振り返って、最も印象に残ったことや
学んだことについて話してください。

この経験があなたにとってどのような意味を持つか、
今後の関係への期待も含めて感想を聞かせてください。
"""
                
                reflection_result = await runner.run(agent, final_reflection_prompt)
                print(f"\n{agent.name}の最終感想: {reflection_result.final_output}")
        
        # 結果保存
        self._save_results(coordinator)
        
        print(f"\n✅ 自律的会話実験完了!")
        print(f"詳細なログとトレースが保存されました")
    
    def _save_results(self, coordinator: ConversationCoordinator):
        """実験結果を保存"""
        os.makedirs("results", exist_ok=True)
        
        self.results["end_time"] = datetime.now().isoformat()
        self.results["full_conversation_log"] = coordinator.conversation_log
        
        filename = f"results/{self.experiment_id}_autonomous_conversation.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 結果保存: {filename}")


async def main():
    """メイン実行関数"""
    print("🌟 OpenAI Agents SDK 自律的マルチエージェント会話")
    
    # 環境チェック
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        experiment = AutonomousConversationExperiment("autonomous_multiagent_conversation")
        await experiment.run_full_experiment()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())