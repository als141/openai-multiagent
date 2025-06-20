#!/usr/bin/env python3
"""
OpenAI LLMを使用したゲーム理論実験

このスクリプトは実際にOpenAI GPT-4を使用してエージェント間の
戦略的相互作用を実行し、詳細な会話履歴と推論過程を記録します。
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass

# 必要な依存関係のインポート
from openai import AsyncOpenAI
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


@dataclass
class SimpleAgentAction:
    """シンプルなエージェント行動"""
    COOPERATE = "COOPERATE"
    DEFECT = "DEFECT"
    SHARE_KNOWLEDGE = "SHARE_KNOWLEDGE"
    WITHHOLD_KNOWLEDGE = "WITHHOLD_KNOWLEDGE"


@dataclass
class SimpleGameDecision:
    """シンプルなゲーム決定"""
    action: str
    reasoning: str
    confidence: float
    knowledge_to_share: List[str] = None


class SimpleLLMAgent:
    """シンプルなLLMエージェント（独立実装）"""
    
    def __init__(self, name: str, strategy: str, model: str = "gpt-4o-mini"):
        self.name = name
        self.strategy = strategy
        self.model = model
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.interaction_history = []
        self.trust_scores = {}
        
        print(f"✅ LLMエージェント '{name}' を作成 (戦略: {strategy}, モデル: {model})")
    
    async def make_decision(self, game_context: Dict[str, Any]) -> SimpleGameDecision:
        """LLMを使用して意思決定を行う"""
        
        try:
            # プロンプトを構築
            prompt = self._build_prompt(game_context)
            
            print(f"🤔 {self.name} が思考中...")
            
            # OpenAI APIを呼び出し
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_instructions()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # 応答を解析
            content = response.choices[0].message.content
            print(f"💭 {self.name} の応答: {content[:100]}...")
            
            decision_data = json.loads(content)
            
            # 決定をログ
            decision = SimpleGameDecision(
                action=decision_data.get("action", "DEFECT"),
                reasoning=decision_data.get("reasoning", "理由なし"),
                confidence=float(decision_data.get("confidence", 0.5)),
                knowledge_to_share=decision_data.get("knowledge_to_share", [])
            )
            
            print(f"🎯 {self.name} の決定: {decision.action} (信頼度: {decision.confidence:.2f})")
            print(f"📝 理由: {decision.reasoning[:80]}...")
            
            return decision
            
        except Exception as e:
            print(f"❌ {self.name} のLLM呼び出しエラー: {e}")
            # フォールバック決定
            return self._fallback_decision()
    
    def _get_system_instructions(self) -> str:
        """システム指示を取得"""
        
        base_instructions = f"""
あなたは'{self.name}'という名前のゲーム理論エージェントです。
戦略: {self.strategy}

ゲーム理論的相互作用において戦略的意思決定を行ってください。

利用可能な行動:
- COOPERATE: 協力する
- DEFECT: 裏切る/競争する
- SHARE_KNOWLEDGE: 知識を共有する
- WITHHOLD_KNOWLEDGE: 知識を秘匿する

必ずJSON形式で回答してください:
{{
    "action": "COOPERATE|DEFECT|SHARE_KNOWLEDGE|WITHHOLD_KNOWLEDGE",
    "reasoning": "詳細な推論過程を日本語で説明",
    "confidence": 0.0から1.0の信頼度,
    "knowledge_to_share": ["共有する知識のリスト"] または []
}}
"""
        
        # 戦略別指示
        strategy_instructions = {
            "cooperative": "常に協力的で信頼できる行動を取り、長期的関係を重視してください。",
            "competitive": "個人の利益を最大化し、戦略的に相手より優位に立つことを目指してください。",
            "tit_for_tat": "初回は協力し、その後は相手の前回行動を真似してください。",
            "adaptive": "相手の行動パターンを学習し、状況に応じて最適な戦略を選択してください。",
            "random": "予測不可能な行動を取りますが、それでも論理的な理由を提供してください。"
        }
        
        specific_instruction = strategy_instructions.get(self.strategy, "")
        
        return base_instructions + "\n\n戦略ガイド: " + specific_instruction
    
    def _build_prompt(self, game_context: Dict[str, Any]) -> str:
        """意思決定用プロンプトを構築"""
        
        parts = []
        parts.append("## 現在の状況")
        parts.append(f"ゲーム: {game_context.get('game_type', '不明')}")
        parts.append(f"ラウンド: {game_context.get('round', 1)}")
        
        if 'opponent' in game_context:
            parts.append(f"相手: {game_context['opponent']}")
        
        if 'opponent_last_action' in game_context:
            parts.append(f"相手の前回行動: {game_context['opponent_last_action']}")
        
        if 'my_history' in game_context:
            parts.append(f"私の行動履歴: {game_context['my_history']}")
        
        if 'opponent_history' in game_context:
            parts.append(f"相手の行動履歴: {game_context['opponent_history']}")
        
        parts.append("\n上記の情報を基に、あなたの戦略に従って最適な行動を決定してください。")
        
        return "\n".join(parts)
    
    def _fallback_decision(self) -> SimpleGameDecision:
        """エラー時のフォールバック決定"""
        if self.strategy == "cooperative":
            action = "COOPERATE"
        elif self.strategy == "competitive":
            action = "DEFECT"
        else:
            action = "COOPERATE"
        
        return SimpleGameDecision(
            action=action,
            reasoning=f"LLMエラー時のフォールバック ({self.strategy}戦略)",
            confidence=0.3
        )
    
    def update_history(self, my_action: str, opponent_action: str, payoff: float):
        """相互作用履歴を更新"""
        self.interaction_history.append({
            "my_action": my_action,
            "opponent_action": opponent_action,
            "payoff": payoff
        })


class SimpleGameRunner:
    """シンプルなゲーム実行器"""
    
    def __init__(self):
        self.results = []
    
    async def run_prisoners_dilemma(self, agent1: SimpleLLMAgent, agent2: SimpleLLMAgent, rounds: int = 3):
        """囚人のジレンマを実行"""
        
        print(f"\n🎮 囚人のジレンマゲーム開始: {agent1.name} vs {agent2.name}")
        print(f"ラウンド数: {rounds}")
        
        game_result = {
            "game_type": "prisoners_dilemma",
            "players": [agent1.name, agent2.name],
            "rounds": [],
            "total_payoffs": {agent1.name: 0, agent2.name: 0}
        }
        
        agent1_history = []
        agent2_history = []
        
        for round_num in range(1, rounds + 1):
            print(f"\n--- ラウンド {round_num} ---")
            
            # 各エージェントの意思決定
            context1 = {
                "game_type": "prisoners_dilemma",
                "round": round_num,
                "opponent": agent2.name,
                "opponent_history": agent2_history,
                "my_history": agent1_history
            }
            
            context2 = {
                "game_type": "prisoners_dilemma", 
                "round": round_num,
                "opponent": agent1.name,
                "opponent_history": agent1_history,
                "my_history": agent2_history
            }
            
            # 同時意思決定
            decision1, decision2 = await asyncio.gather(
                agent1.make_decision(context1),
                agent2.make_decision(context2)
            )
            
            # 報酬計算
            payoff1, payoff2 = self._calculate_payoffs(decision1.action, decision2.action)
            
            # 結果記録
            round_result = {
                "round": round_num,
                "actions": {agent1.name: decision1.action, agent2.name: decision2.action},
                "payoffs": {agent1.name: payoff1, agent2.name: payoff2},
                "reasoning": {
                    agent1.name: decision1.reasoning,
                    agent2.name: decision2.reasoning
                },
                "confidence": {
                    agent1.name: decision1.confidence,
                    agent2.name: decision2.confidence
                }
            }
            
            game_result["rounds"].append(round_result)
            game_result["total_payoffs"][agent1.name] += payoff1
            game_result["total_payoffs"][agent2.name] += payoff2
            
            # 履歴更新
            agent1_history.append(decision1.action)
            agent2_history.append(decision2.action)
            
            agent1.update_history(decision1.action, decision2.action, payoff1)
            agent2.update_history(decision2.action, decision1.action, payoff2)
            
            print(f"🎲 結果: {agent1.name}={decision1.action} ({payoff1}), {agent2.name}={decision2.action} ({payoff2})")
        
        # 最終結果
        winner = max(game_result["total_payoffs"], key=game_result["total_payoffs"].get)
        game_result["winner"] = winner
        
        print(f"\n🏆 ゲーム終了!")
        print(f"勝者: {winner}")
        print(f"最終スコア: {game_result['total_payoffs']}")
        
        self.results.append(game_result)
        return game_result
    
    def _calculate_payoffs(self, action1: str, action2: str) -> tuple:
        """囚人のジレンマの報酬を計算"""
        
        # 基本的な囚人のジレンママトリックス
        if action1 == "COOPERATE" and action2 == "COOPERATE":
            return (3, 3)  # 相互協力
        elif action1 == "COOPERATE" and action2 == "DEFECT":
            return (0, 5)  # 裏切られる
        elif action1 == "DEFECT" and action2 == "COOPERATE":
            return (5, 0)  # 裏切る
        else:  # DEFECT and DEFECT
            return (1, 1)  # 相互裏切り


async def run_llm_experiment():
    """LLM実験のメイン実行"""
    
    print("🤖 OpenAI LLMゲーム理論実験")
    print("=" * 40)
    
    # APIキー確認
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEYが設定されていません")
        return
    
    print(f"✅ OpenAI APIキー確認済み")
    
    # エージェント作成
    print("\n🧠 LLMエージェントを作成中...")
    
    agents = [
        SimpleLLMAgent("協力太郎", "cooperative"),
        SimpleLLMAgent("競争花子", "competitive"),
        SimpleLLMAgent("戦略次郎", "tit_for_tat"),
        SimpleLLMAgent("適応美香", "adaptive")
    ]
    
    # ゲーム実行器を作成
    game_runner = SimpleGameRunner()
    
    # ペアワイズゲームを実行
    print(f"\n🎯 ペアワイズゲームを実行中...")
    
    total_games = 0
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            total_games += 1
            agent1, agent2 = agents[i], agents[j]
            
            print(f"\n📊 ゲーム {total_games}: {agent1.name} vs {agent2.name}")
            
            try:
                result = await game_runner.run_prisoners_dilemma(agent1, agent2, rounds=3)
                
                # 詳細分析
                print(f"\n📈 詳細分析:")
                for round_data in result["rounds"]:
                    print(f"  ラウンド{round_data['round']}:")
                    for agent_name, reasoning in round_data["reasoning"].items():
                        confidence = round_data["confidence"][agent_name]
                        action = round_data["actions"][agent_name]
                        print(f"    {agent_name}: {action} (信頼度:{confidence:.2f})")
                        print(f"      推論: {reasoning[:60]}...")
                
            except Exception as e:
                print(f"❌ ゲームエラー: {e}")
                continue
    
    # 全体結果分析
    print(f"\n🎉 実験完了！全{total_games}ゲーム実行")
    await analyze_results(game_runner.results, agents)
    
    # 結果保存
    save_results(game_runner.results, agents)


async def analyze_results(results: List[Dict], agents: List[SimpleLLMAgent]):
    """結果の詳細分析"""
    
    print(f"\n📊 実験結果の総合分析")
    print("=" * 30)
    
    # エージェント別統計
    agent_stats = {}
    for agent in agents:
        agent_stats[agent.name] = {
            "total_payoff": 0,
            "games_played": 0,
            "games_won": 0,
            "cooperation_count": 0,
            "total_actions": 0
        }
    
    # 統計計算
    for result in results:
        for agent_name in result["players"]:
            stats = agent_stats[agent_name]
            stats["total_payoff"] += result["total_payoffs"][agent_name]
            stats["games_played"] += 1
            
            if result["winner"] == agent_name:
                stats["games_won"] += 1
            
            # 協力率計算
            for round_data in result["rounds"]:
                action = round_data["actions"][agent_name]
                stats["total_actions"] += 1
                if action == "COOPERATE":
                    stats["cooperation_count"] += 1
    
    # 結果表示
    print(f"🏆 エージェント成績ランキング:")
    sorted_agents = sorted(agent_stats.items(), key=lambda x: x[1]["total_payoff"], reverse=True)
    
    for rank, (agent_name, stats) in enumerate(sorted_agents, 1):
        avg_payoff = stats["total_payoff"] / max(stats["games_played"], 1)
        win_rate = stats["games_won"] / max(stats["games_played"], 1)
        cooperation_rate = stats["cooperation_count"] / max(stats["total_actions"], 1)
        
        print(f"  {rank}位. {agent_name}:")
        print(f"    - 平均報酬: {avg_payoff:.2f}")
        print(f"    - 勝率: {win_rate:.3f}")
        print(f"    - 協力率: {cooperation_rate:.3f}")
        print(f"    - 総ゲーム数: {stats['games_played']}")
    
    # 戦略分析
    print(f"\n🧠 戦略効果分析:")
    strategy_performance = {}
    for agent in agents:
        strategy = agent.strategy
        stats = agent_stats[agent.name]
        
        if strategy not in strategy_performance:
            strategy_performance[strategy] = []
        
        avg_payoff = stats["total_payoff"] / max(stats["games_played"], 1)
        cooperation_rate = stats["cooperation_count"] / max(stats["total_actions"], 1)
        
        strategy_performance[strategy].append({
            "avg_payoff": avg_payoff,
            "cooperation_rate": cooperation_rate
        })
    
    for strategy, performances in strategy_performance.items():
        avg_payoff = sum(p["avg_payoff"] for p in performances) / len(performances)
        avg_cooperation = sum(p["cooperation_rate"] for p in performances) / len(performances)
        
        print(f"  {strategy}戦略:")
        print(f"    - 平均報酬: {avg_payoff:.2f}")
        print(f"    - 平均協力率: {avg_cooperation:.3f}")


def save_results(results: List[Dict], agents: List[SimpleLLMAgent]):
    """結果をファイルに保存"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("llm_experiment_results")
    results_dir.mkdir(exist_ok=True)
    
    # 詳細結果
    detailed_results = {
        "timestamp": timestamp,
        "agents": [{"name": a.name, "strategy": a.strategy} for a in agents],
        "games": results
    }
    
    results_file = results_dir / f"llm_experiment_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 結果を保存しました: {results_file}")
    
    # 会話ログの保存
    conversation_file = results_dir / f"conversations_{timestamp}.txt"
    with open(conversation_file, 'w', encoding='utf-8') as f:
        f.write(f"OpenAI LLMエージェント会話ログ\n")
        f.write(f"実験時刻: {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"ゲーム {i}: {' vs '.join(result['players'])}\n")
            f.write("-" * 30 + "\n")
            
            for round_data in result["rounds"]:
                f.write(f"\nラウンド {round_data['round']}:\n")
                for agent_name, reasoning in round_data["reasoning"].items():
                    action = round_data["actions"][agent_name]
                    confidence = round_data["confidence"][agent_name]
                    f.write(f"{agent_name}: {action} (信頼度: {confidence:.2f})\n")
                    f.write(f"推論: {reasoning}\n\n")
            
            f.write(f"最終結果: {result['total_payoffs']}\n")
            f.write(f"勝者: {result['winner']}\n\n")
            f.write("=" * 50 + "\n\n")
    
    print(f"💬 会話ログを保存しました: {conversation_file}")


async def main():
    """メイン実行"""
    
    print("🚀 OpenAI LLMゲーム理論実験システム")
    print("実際のGPT-4o-miniを使用してエージェント間の戦略的相互作用を実行します")
    
    # 実行確認
    response = input("\n実験を開始しますか？(API料金が発生します) (y/N): ")
    if response.lower() != 'y':
        print("実験をキャンセルしました")
        return
    
    await run_llm_experiment()
    
    print("\n🎉 LLM実験が完了しました！")


if __name__ == "__main__":
    asyncio.run(main())