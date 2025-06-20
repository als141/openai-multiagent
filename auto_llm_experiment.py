#!/usr/bin/env python3
"""
OpenAI LLMを使用したゲーム理論実験（自動実行版）

このスクリプトは実際にOpenAI GPT-4o-miniを使用してエージェント間の
戦略的相互作用を実行し、詳細な会話履歴と推論過程を記録します。
"""

import asyncio
import os
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
            print(f"💭 {self.name} の応答を受信")
            
            decision_data = json.loads(content)
            
            # 決定をログ
            decision = SimpleGameDecision(
                action=decision_data.get("action", "DEFECT"),
                reasoning=decision_data.get("reasoning", "理由なし"),
                confidence=float(decision_data.get("confidence", 0.5)),
                knowledge_to_share=decision_data.get("knowledge_to_share", [])
            )
            
            print(f"🎯 {self.name} の決定: {decision.action} (信頼度: {decision.confidence:.2f})")
            print(f"📝 理由: {decision.reasoning[:60]}...")
            
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
            "cooperative": "常に協力的で信頼できる行動を取り、長期的関係を重視してください。相手が裏切っても協力を続ける傾向があります。",
            "competitive": "個人の利益を最大化し、戦略的に相手より優位に立つことを目指してください。協力よりも競争を優先します。",
            "tit_for_tat": "初回は必ず協力し、その後は相手の前回行動を真似してください。相手が協力すれば協力、裏切れば裏切ります。",
            "adaptive": "相手の行動パターンを学習し、状況に応じて最適な戦略を選択してください。過去の結果を分析して行動を調整します。"
        }
        
        specific_instruction = strategy_instructions.get(self.strategy, "")
        
        return base_instructions + "\n\n戦略ガイド: " + specific_instruction
    
    def _build_prompt(self, game_context: Dict[str, Any]) -> str:
        """意思決定用プロンプトを構築"""
        
        parts = []
        parts.append("## 現在の状況")
        parts.append(f"ゲーム: {game_context.get('game_type', '囚人のジレンマ')}")
        parts.append(f"ラウンド: {game_context.get('round', 1)}")
        
        if 'opponent' in game_context:
            parts.append(f"相手: {game_context['opponent']}")
        
        if 'opponent_last_action' in game_context and game_context['opponent_last_action']:
            parts.append(f"相手の前回行動: {game_context['opponent_last_action']}")
        
        if 'my_history' in game_context and game_context['my_history']:
            parts.append(f"私の行動履歴: {' → '.join(game_context['my_history'][-3:])}")  # 最近3回
        
        if 'opponent_history' in game_context and game_context['opponent_history']:
            parts.append(f"相手の行動履歴: {' → '.join(game_context['opponent_history'][-3:])}")  # 最近3回
        
        parts.append("\n## 報酬マトリックス（囚人のジレンマ）")
        parts.append("- 両者協力: (3,3)")
        parts.append("- 自分協力/相手裏切り: (0,5)")
        parts.append("- 自分裏切り/相手協力: (5,0)")
        parts.append("- 両者裏切り: (1,1)")
        
        parts.append("\n上記の情報を基に、あなたの戦略に従って最適な行動を決定してください。")
        
        return "\n".join(parts)
    
    def _fallback_decision(self) -> SimpleGameDecision:
        """エラー時のフォールバック決定"""
        if self.strategy == "cooperative":
            action = "COOPERATE"
        elif self.strategy == "competitive":
            action = "DEFECT"
        elif self.strategy == "tit_for_tat":
            action = "COOPERATE"  # 初回は協力
        else:
            action = "COOPERATE"
        
        return SimpleGameDecision(
            action=action,
            reasoning=f"LLMエラー時のフォールバック ({self.strategy}戦略に基づく)",
            confidence=0.3
        )


class SimpleGameRunner:
    """シンプルなゲーム実行器"""
    
    def __init__(self):
        self.results = []
        self.conversation_log = []
    
    async def run_prisoners_dilemma(self, agent1: SimpleLLMAgent, agent2: SimpleLLMAgent, rounds: int = 3):
        """囚人のジレンマを実行"""
        
        print(f"\n🎮 囚人のジレンマゲーム開始")
        print(f"👥 {agent1.name} ({agent1.strategy}) vs {agent2.name} ({agent2.strategy})")
        print(f"🔄 ラウンド数: {rounds}")
        
        game_result = {
            "game_type": "prisoners_dilemma",
            "players": [agent1.name, agent2.name],
            "strategies": [agent1.strategy, agent2.strategy],
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
                "my_history": agent1_history,
                "opponent_last_action": agent2_history[-1] if agent2_history else None
            }
            
            context2 = {
                "game_type": "prisoners_dilemma", 
                "round": round_num,
                "opponent": agent1.name,
                "opponent_history": agent1_history,
                "my_history": agent2_history,
                "opponent_last_action": agent1_history[-1] if agent1_history else None
            }
            
            # 同時意思決定
            print("🤖 両エージェントが同時に思考中...")
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
            
            # 会話ログ記録
            self.conversation_log.append({
                "round": round_num,
                "game": f"{agent1.name} vs {agent2.name}",
                "conversations": [
                    {
                        "agent": agent1.name,
                        "strategy": agent1.strategy,
                        "action": decision1.action,
                        "reasoning": decision1.reasoning,
                        "confidence": decision1.confidence
                    },
                    {
                        "agent": agent2.name,
                        "strategy": agent2.strategy,
                        "action": decision2.action,
                        "reasoning": decision2.reasoning,
                        "confidence": decision2.confidence
                    }
                ]
            })
            
            print(f"🎲 結果: {agent1.name}={decision1.action} ({payoff1}), {agent2.name}={decision2.action} ({payoff2})")
            
            # 協力/裏切りの相互作用を分析
            interaction_type = self._analyze_interaction(decision1.action, decision2.action)
            print(f"🔍 相互作用: {interaction_type}")
        
        # 最終結果
        total1 = game_result["total_payoffs"][agent1.name]
        total2 = game_result["total_payoffs"][agent2.name]
        
        if total1 > total2:
            winner = agent1.name
        elif total2 > total1:
            winner = agent2.name
        else:
            winner = "引き分け"
        
        game_result["winner"] = winner
        
        print(f"\n🏆 ゲーム終了!")
        print(f"勝者: {winner}")
        print(f"最終スコア: {agent1.name}={total1}, {agent2.name}={total2}")
        
        # 協力率を計算
        coop_rate_1 = sum(1 for action in agent1_history if action == "COOPERATE") / len(agent1_history)
        coop_rate_2 = sum(1 for action in agent2_history if action == "COOPERATE") / len(agent2_history)
        
        game_result["cooperation_rates"] = {
            agent1.name: coop_rate_1,
            agent2.name: coop_rate_2
        }
        
        print(f"協力率: {agent1.name}={coop_rate_1:.2f}, {agent2.name}={coop_rate_2:.2f}")
        
        self.results.append(game_result)
        return game_result
    
    def _calculate_payoffs(self, action1: str, action2: str) -> tuple:
        """囚人のジレンマの報酬を計算"""
        
        if action1 == "COOPERATE" and action2 == "COOPERATE":
            return (3, 3)  # 相互協力
        elif action1 == "COOPERATE" and action2 == "DEFECT":
            return (0, 5)  # 裏切られる
        elif action1 == "DEFECT" and action2 == "COOPERATE":
            return (5, 0)  # 裏切る
        else:  # DEFECT and DEFECT
            return (1, 1)  # 相互裏切り
    
    def _analyze_interaction(self, action1: str, action2: str) -> str:
        """相互作用タイプを分析"""
        
        if action1 == "COOPERATE" and action2 == "COOPERATE":
            return "相互協力（Win-Win）"
        elif action1 == "DEFECT" and action2 == "DEFECT":
            return "相互裏切り（Lose-Lose）"
        else:
            return "非対称（一方が搾取）"


async def run_comprehensive_llm_experiment():
    """包括的なLLM実験を実行"""
    
    print("🤖 OpenAI LLMゲーム理論実験システム")
    print("=" * 50)
    print("実際のGPT-4o-miniを使用してエージェント間の戦略的相互作用を実行します")
    
    # APIキー確認
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEYが設定されていません")
        return
    
    print(f"✅ OpenAI APIキー確認済み")
    
    # エージェント作成
    print("\n🧠 多様なLLMエージェントを作成中...")
    
    agents = [
        SimpleLLMAgent("協力的_太郎", "cooperative"),
        SimpleLLMAgent("競争的_花子", "competitive"),
        SimpleLLMAgent("戦略的_次郎", "tit_for_tat"),
        SimpleLLMAgent("適応的_美咲", "adaptive")
    ]
    
    print(f"✅ {len(agents)}体のエージェントを作成完了")
    
    # ゲーム実行器を作成
    game_runner = SimpleGameRunner()
    
    # ペアワイズゲームを実行
    print(f"\n🎯 ペアワイズゲーム実行開始...")
    print(f"予想API呼び出し数: {len(agents) * (len(agents) - 1) // 2 * 3 * 2} 回")
    print(f"予想コスト: ${len(agents) * (len(agents) - 1) // 2 * 3 * 2 * 0.0001:.4f}")
    
    total_games = 0
    start_time = datetime.now()
    
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            total_games += 1
            agent1, agent2 = agents[i], agents[j]
            
            print(f"\n{'='*20}")
            print(f"📊 ゲーム {total_games}: {agent1.name} vs {agent2.name}")
            print(f"戦略対戦: {agent1.strategy} vs {agent2.strategy}")
            print(f"{'='*20}")
            
            try:
                result = await game_runner.run_prisoners_dilemma(agent1, agent2, rounds=3)
                
                # 戦略分析
                print(f"\n📈 戦略効果分析:")
                for round_data in result["rounds"]:
                    round_num = round_data['round']
                    print(f"  ラウンド{round_num}:")
                    for agent_name, reasoning in round_data["reasoning"].items():
                        confidence = round_data["confidence"][agent_name]
                        action = round_data["actions"][agent_name]
                        agent_obj = next(a for a in [agent1, agent2] if a.name == agent_name)
                        print(f"    {agent_name} ({agent_obj.strategy}): {action}")
                        print(f"      信頼度: {confidence:.2f}")
                        print(f"      推論: {reasoning[:80]}...")
                
            except Exception as e:
                print(f"❌ ゲームエラー: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 実験完了
    print(f"\n🎉 実験完了！")
    print(f"⏱️  実行時間: {duration}")
    print(f"🎮 実行ゲーム数: {total_games}")
    print(f"💬 記録された会話ターン: {len(game_runner.conversation_log)}")
    
    # 詳細分析
    await analyze_comprehensive_results(game_runner.results, agents, game_runner.conversation_log)
    
    # 結果保存
    save_comprehensive_results(game_runner.results, agents, game_runner.conversation_log)
    
    return game_runner.results


async def analyze_comprehensive_results(results: List[Dict], agents: List[SimpleLLMAgent], conversation_log: List[Dict]):
    """包括的な結果分析"""
    
    print(f"\n📊 包括的実験結果分析")
    print("=" * 40)
    
    # エージェント別統計
    agent_stats = {}
    for agent in agents:
        agent_stats[agent.name] = {
            "strategy": agent.strategy,
            "total_payoff": 0,
            "games_played": 0,
            "games_won": 0,
            "cooperation_count": 0,
            "total_actions": 0,
            "avg_confidence": 0,
            "confidence_count": 0
        }
    
    # 統計計算
    for result in results:
        for agent_name in result["players"]:
            stats = agent_stats[agent_name]
            stats["total_payoff"] += result["total_payoffs"][agent_name]
            stats["games_played"] += 1
            
            if result["winner"] == agent_name:
                stats["games_won"] += 1
            
            # 協力率と信頼度計算
            for round_data in result["rounds"]:
                action = round_data["actions"][agent_name]
                confidence = round_data["confidence"][agent_name]
                
                stats["total_actions"] += 1
                stats["confidence_count"] += 1
                stats["avg_confidence"] += confidence
                
                if action == "COOPERATE":
                    stats["cooperation_count"] += 1
    
    # 平均値計算
    for stats in agent_stats.values():
        if stats["confidence_count"] > 0:
            stats["avg_confidence"] /= stats["confidence_count"]
    
    # 成績ランキング
    print(f"\n🏆 エージェント総合成績ランキング:")
    sorted_agents = sorted(agent_stats.items(), key=lambda x: x[1]["total_payoff"], reverse=True)
    
    for rank, (agent_name, stats) in enumerate(sorted_agents, 1):
        avg_payoff = stats["total_payoff"] / max(stats["games_played"], 1)
        win_rate = stats["games_won"] / max(stats["games_played"], 1)
        cooperation_rate = stats["cooperation_count"] / max(stats["total_actions"], 1)
        
        print(f"  {rank}位. {agent_name} ({stats['strategy']}):")
        print(f"    - 平均報酬: {avg_payoff:.2f}")
        print(f"    - 勝率: {win_rate:.3f}")
        print(f"    - 協力率: {cooperation_rate:.3f}")
        print(f"    - 平均信頼度: {stats['avg_confidence']:.3f}")
        print(f"    - 総ゲーム数: {stats['games_played']}")
    
    # 戦略別分析
    print(f"\n🧠 戦略別効果分析:")
    strategy_performance = {}
    
    for agent_name, stats in agent_stats.items():
        strategy = stats["strategy"]
        if strategy not in strategy_performance:
            strategy_performance[strategy] = {
                "agents": [],
                "total_payoff": 0,
                "total_games": 0,
                "total_cooperation": 0,
                "total_actions": 0,
                "total_confidence": 0
            }
        
        perf = strategy_performance[strategy]
        perf["agents"].append(agent_name)
        perf["total_payoff"] += stats["total_payoff"]
        perf["total_games"] += stats["games_played"]
        perf["total_cooperation"] += stats["cooperation_count"]
        perf["total_actions"] += stats["total_actions"]
        perf["total_confidence"] += stats["avg_confidence"]
    
    for strategy, perf in strategy_performance.items():
        avg_payoff = perf["total_payoff"] / max(perf["total_games"], 1)
        avg_cooperation = perf["total_cooperation"] / max(perf["total_actions"], 1)
        avg_confidence = perf["total_confidence"] / len(perf["agents"])
        
        print(f"  {strategy}戦略:")
        print(f"    - 平均報酬: {avg_payoff:.2f}")
        print(f"    - 平均協力率: {avg_cooperation:.3f}")
        print(f"    - 平均信頼度: {avg_confidence:.3f}")
        print(f"    - エージェント: {', '.join(perf['agents'])}")
    
    # 相互作用パターン分析
    print(f"\n🔄 相互作用パターン分析:")
    interaction_matrix = {}
    
    for result in results:
        players = result["players"]
        strategies = result["strategies"]
        key = f"{strategies[0]} vs {strategies[1]}"
        
        if key not in interaction_matrix:
            interaction_matrix[key] = {
                "games": 0,
                "mutual_cooperation": 0,
                "mutual_defection": 0,
                "exploitation": 0,
                "total_rounds": 0
            }
        
        matrix = interaction_matrix[key]
        matrix["games"] += 1
        
        for round_data in result["rounds"]:
            actions = list(round_data["actions"].values())
            matrix["total_rounds"] += 1
            
            if actions[0] == "COOPERATE" and actions[1] == "COOPERATE":
                matrix["mutual_cooperation"] += 1
            elif actions[0] == "DEFECT" and actions[1] == "DEFECT":
                matrix["mutual_defection"] += 1
            else:
                matrix["exploitation"] += 1
    
    for interaction, data in interaction_matrix.items():
        total = data["total_rounds"]
        if total > 0:
            mutual_coop_rate = data["mutual_cooperation"] / total
            mutual_defect_rate = data["mutual_defection"] / total
            exploitation_rate = data["exploitation"] / total
            
            print(f"  {interaction}:")
            print(f"    - 相互協力率: {mutual_coop_rate:.3f}")
            print(f"    - 相互裏切り率: {mutual_defect_rate:.3f}")
            print(f"    - 搾取率: {exploitation_rate:.3f}")
            print(f"    - 総ラウンド数: {total}")
    
    # LLM推論分析
    print(f"\n🧩 LLM推論パターン分析:")
    
    reasoning_keywords = {
        "協力": ["協力", "信頼", "長期", "関係", "互恵"],
        "競争": ["裏切", "競争", "利益", "優位", "戦略"],
        "学習": ["学習", "分析", "パターン", "適応", "観察"],
        "不確実": ["不確実", "判断", "難し", "迷", "複雑"]
    }
    
    reasoning_analysis = {category: 0 for category in reasoning_keywords.keys()}
    total_reasoning = 0
    
    for log_entry in conversation_log:
        for conv in log_entry["conversations"]:
            reasoning = conv["reasoning"].lower()
            total_reasoning += 1
            
            for category, keywords in reasoning_keywords.items():
                if any(keyword in reasoning for keyword in keywords):
                    reasoning_analysis[category] += 1
                    break
    
    print("  推論カテゴリ分布:")
    for category, count in reasoning_analysis.items():
        rate = count / max(total_reasoning, 1)
        print(f"    - {category}志向: {rate:.3f} ({count}/{total_reasoning})")


def save_comprehensive_results(results: List[Dict], agents: List[SimpleLLMAgent], conversation_log: List[Dict]):
    """包括的な結果保存"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("llm_experiment_results")
    results_dir.mkdir(exist_ok=True)
    
    # 1. 詳細結果JSON
    comprehensive_results = {
        "experiment_info": {
            "timestamp": timestamp,
            "model_used": "gpt-4o-mini",
            "total_games": len(results),
            "total_agents": len(agents)
        },
        "agents": [{"name": a.name, "strategy": a.strategy} for a in agents],
        "game_results": results,
        "conversation_log": conversation_log
    }
    
    results_file = results_dir / f"comprehensive_llm_experiment_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細結果を保存: {results_file}")
    
    # 2. 会話履歴テキスト
    conversation_file = results_dir / f"llm_conversations_{timestamp}.txt"
    with open(conversation_file, 'w', encoding='utf-8') as f:
        f.write(f"OpenAI LLMエージェント会話履歴\n")
        f.write(f"実験時刻: {timestamp}\n")
        f.write(f"使用モデル: gpt-4o-mini\n")
        f.write("=" * 80 + "\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"ゲーム {i}: {' vs '.join(result['players'])}\n")
            f.write(f"戦略: {' vs '.join(result['strategies'])}\n")
            f.write("-" * 60 + "\n")
            
            for round_data in result["rounds"]:
                f.write(f"\nラウンド {round_data['round']}:\n")
                
                for agent_name, reasoning in round_data["reasoning"].items():
                    action = round_data["actions"][agent_name]
                    confidence = round_data["confidence"][agent_name]
                    payoff = round_data["payoffs"][agent_name]
                    
                    f.write(f"\n{agent_name}: {action} (信頼度: {confidence:.2f}, 報酬: {payoff})\n")
                    f.write(f"推論: {reasoning}\n")
                
                # ラウンド結果
                actions = list(round_data["actions"].values())
                payoffs = list(round_data["payoffs"].values())
                f.write(f"\nラウンド結果: {actions[0]} vs {actions[1]} → 報酬 ({payoffs[0]}, {payoffs[1]})\n")
            
            # ゲーム最終結果
            f.write(f"\n最終スコア: {result['total_payoffs']}\n")
            f.write(f"勝者: {result['winner']}\n")
            f.write(f"協力率: {result['cooperation_rates']}\n")
            f.write("\n" + "=" * 80 + "\n\n")
    
    print(f"💬 会話履歴を保存: {conversation_file}")
    
    # 3. 統計サマリーCSV
    import csv
    
    stats_file = results_dir / f"llm_statistics_{timestamp}.csv"
    with open(stats_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['agent_name', 'strategy', 'total_payoff', 'avg_payoff', 'games_played', 
                     'games_won', 'win_rate', 'cooperation_rate', 'avg_confidence']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # エージェント統計計算
        for agent in agents:
            agent_games = [r for r in results if agent.name in r["players"]]
            total_payoff = sum(r["total_payoffs"][agent.name] for r in agent_games)
            games_played = len(agent_games)
            games_won = sum(1 for r in agent_games if r["winner"] == agent.name)
            
            # 協力率と信頼度計算
            cooperation_count = 0
            total_actions = 0
            total_confidence = 0
            confidence_count = 0
            
            for result in agent_games:
                for round_data in result["rounds"]:
                    action = round_data["actions"][agent.name]
                    confidence = round_data["confidence"][agent.name]
                    
                    total_actions += 1
                    confidence_count += 1
                    total_confidence += confidence
                    
                    if action == "COOPERATE":
                        cooperation_count += 1
            
            writer.writerow({
                'agent_name': agent.name,
                'strategy': agent.strategy,
                'total_payoff': total_payoff,
                'avg_payoff': total_payoff / max(games_played, 1),
                'games_played': games_played,
                'games_won': games_won,
                'win_rate': games_won / max(games_played, 1),
                'cooperation_rate': cooperation_count / max(total_actions, 1),
                'avg_confidence': total_confidence / max(confidence_count, 1)
            })
    
    print(f"📊 統計データを保存: {stats_file}")
    
    print(f"\n✅ 全ての結果ファイルを {results_dir} に保存完了")


async def main():
    """メイン実行"""
    
    # 自動実行（確認なし）
    await run_comprehensive_llm_experiment()
    
    print("\n🎉 OpenAI LLMゲーム理論実験が完了しました！")
    print("📁 結果は llm_experiment_results/ ディレクトリに保存されています")


if __name__ == "__main__":
    asyncio.run(main())