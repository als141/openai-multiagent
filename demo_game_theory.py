#!/usr/bin/env python
"""ゲーム理論的マルチエージェント相互作用のデモ"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from agents import Agent, Runner, handoff


class GameTheoryDemo:
    """ゲーム理論デモクラス"""
    
    def __init__(self):
        self.results = {
            "experiment_id": f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "interactions": [],
            "agent_stats": {},
            "insights": []
        }
        
    async def create_agents(self):
        """異なる戦略を持つエージェントを作成"""
        
        # 協力的エージェント
        self.cooperative_agent = Agent(
            name="協力者",
            instructions="""
あなたは協力的な戦略を取るエージェントです。

戦略の特徴：
- 常に他者との協力を優先する
- 相手を信頼し、win-winの関係を構築する
- 短期的な損失があっても長期的な利益を重視する

囚人のジレンマでの行動：
- 基本的にCOOPERATE（協力）を選択する
- 相手が裏切っても、再び協力の機会を与える
- 集団全体の利益を最大化することを目指す

回答は簡潔に、選択理由を含めて答えてください。
""")
        
        # 競争的エージェント
        self.competitive_agent = Agent(
            name="競争者",
            instructions="""
あなたは競争的な戦略を取るエージェントです。

戦略の特徴：
- 自己の利益を最大化することを優先する
- 相手の行動を慎重に分析する
- リスクを計算して最適な行動を選択する

囚人のジレンマでの行動：
- 基本的にDEFECT（裏切り）を選択する
- ただし、長期的な関係では協力も検討する
- 相手の戦略に応じて柔軟に対応する

回答は簡潔に、選択理由を含めて答えてください。
""")
        
        # Tit-for-Tat エージェント
        self.tit_for_tat_agent = Agent(
            name="応報者",
            instructions="""
あなたはTit-for-Tat戦略を取るエージェントです。

戦略の特徴：
- 最初は協力から始める
- 相手の前回の行動を真似する
- 裏切りには裏切りで、協力には協力で応じる
- 公平性と相互主義を重視する

囚人のジレンマでの行動：
- 初回はCOOPERATE（協力）を選択
- 相手が前回COOPERATEなら今回もCOOPERATE
- 相手が前回DEFECTなら今回もDEFECT
- 寛容さを示すため、時々協力を試みる

回答は簡潔に、選択理由を含めて答えてください。
""")
        
        # 調整エージェント
        self.coordinator = Agent(
            name="調整者",
            instructions="""
あなたはエージェント間の相互作用を調整し、全体最適を目指すエージェントです。

役割：
- 各エージェントの戦略と行動を分析する
- 集団全体の利益を考慮した提案をする
- 対立を建設的な議論に導く
- 創発的な解決策を見つける

分析の観点：
- 各エージェントの行動パターン
- 信頼関係の構築状況
- 集団の協力度
- 長期的な関係への影響

建設的で公平な分析を提供してください。
""",
            handoffs=[
                handoff(self.cooperative_agent),
                handoff(self.competitive_agent), 
                handoff(self.tit_for_tat_agent)
            ]
        )
        
        self.agents = [
            self.cooperative_agent,
            self.competitive_agent,
            self.tit_for_tat_agent
        ]
        
        # エージェント統計を初期化
        for agent in self.agents:
            self.results["agent_stats"][agent.name] = {
                "cooperate_count": 0,
                "defect_count": 0,
                "total_payoff": 0,
                "interactions": 0
            }
    
    async def run_prisoners_dilemma(self, agent1, agent2, round_num, history):
        """囚人のジレンマを実行"""
        
        # 履歴情報を含むコンテキストを作成
        context = f"""
囚人のジレンマ - ラウンド {round_num}

ゲームルール：
- COOPERATE（協力）& COOPERATE（協力）→ 両者 +3点
- COOPERATE（協力）& DEFECT（裏切り）→ 協力者 0点、裏切り者 +5点  
- DEFECT（裏切り）& DEFECT（裏切り）→ 両者 +1点

対戦相手: {agent2.name}

過去の対戦履歴:
{self._format_history(history, agent1.name, agent2.name)}

あなたの選択: COOPERATE または DEFECT
理由も簡潔に述べてください。
"""
        
        runner = Runner()
        
        # 両エージェントの決定
        result1 = await runner.run(agent1, context.replace(f"対戦相手: {agent2.name}", f"対戦相手: {agent1.name}"))
        result2 = await runner.run(agent2, context)
        
        # 行動を抽出
        action1 = "COOPERATE" if "COOPERATE" in result1.final_output.upper() else "DEFECT"
        action2 = "COOPERATE" if "COOPERATE" in result2.final_output.upper() else "DEFECT"
        
        # 利得を計算
        payoff1, payoff2 = self._calculate_payoff(action1, action2)
        
        # 結果を記録
        interaction = {
            "round": round_num,
            "agent1": agent1.name,
            "agent2": agent2.name,
            "action1": action1,
            "action2": action2,
            "payoff1": payoff1,
            "payoff2": payoff2,
            "reasoning1": result1.final_output,
            "reasoning2": result2.final_output
        }
        
        # 統計を更新
        self._update_stats(agent1.name, action1, payoff1)
        self._update_stats(agent2.name, action2, payoff2)
        
        return interaction
    
    def _format_history(self, history, agent1_name, agent2_name):
        """履歴をフォーマット"""
        if not history:
            return "初回対戦です"
        
        formatted = []
        for h in history[-3:]:  # 最近3回の履歴
            if (h["agent1"] == agent1_name and h["agent2"] == agent2_name) or \
               (h["agent1"] == agent2_name and h["agent2"] == agent1_name):
                formatted.append(f"ラウンド{h['round']}: {h['agent1']}={h['action1']}, {h['agent2']}={h['action2']}")
        
        return "\n".join(formatted) if formatted else "過去の対戦なし"
    
    def _calculate_payoff(self, action1, action2):
        """利得を計算"""
        if action1 == "COOPERATE" and action2 == "COOPERATE":
            return 3, 3
        elif action1 == "COOPERATE" and action2 == "DEFECT":
            return 0, 5
        elif action1 == "DEFECT" and action2 == "COOPERATE":
            return 5, 0
        else:  # both DEFECT
            return 1, 1
    
    def _update_stats(self, agent_name, action, payoff):
        """エージェント統計を更新"""
        stats = self.results["agent_stats"][agent_name]
        if action == "COOPERATE":
            stats["cooperate_count"] += 1
        else:
            stats["defect_count"] += 1
        stats["total_payoff"] += payoff
        stats["interactions"] += 1
    
    async def run_multiple_rounds(self, rounds=10):
        """複数ラウンドの対戦を実行"""
        print(f"🎮 {rounds}ラウンドの囚人のジレンマトーナメント開始")
        
        all_interactions = []
        
        # 全ペアの組み合わせで対戦
        for i in range(len(self.agents)):
            for j in range(i + 1, len(self.agents)):
                agent1, agent2 = self.agents[i], self.agents[j]
                
                print(f"\n--- {agent1.name} vs {agent2.name} ---")
                
                pair_history = []
                for round_num in range(1, rounds + 1):
                    interaction = await self.run_prisoners_dilemma(
                        agent1, agent2, round_num, pair_history
                    )
                    pair_history.append(interaction)
                    all_interactions.append(interaction)
                    
                    print(f"ラウンド{round_num}: {interaction['action1']} vs {interaction['action2']} "
                          f"(利得: {interaction['payoff1']}, {interaction['payoff2']})")
        
        self.results["interactions"] = all_interactions
        
        # 統計を表示
        self._display_stats()
        
        return all_interactions
    
    def _display_stats(self):
        """統計を表示"""
        print(f"\n📊 トーナメント結果:")
        print("-" * 50)
        
        # エージェント別統計
        for agent_name, stats in self.results["agent_stats"].items():
            cooperation_rate = stats["cooperate_count"] / stats["interactions"] if stats["interactions"] > 0 else 0
            avg_payoff = stats["total_payoff"] / stats["interactions"] if stats["interactions"] > 0 else 0
            
            print(f"{agent_name}:")
            print(f"  協力率: {cooperation_rate:.2%}")
            print(f"  平均利得: {avg_payoff:.2f}")
            print(f"  総利得: {stats['total_payoff']}")
            print()
    
    async def analyze_interactions(self):
        """相互作用を分析"""
        print(f"\n🧠 相互作用分析を実行中...")
        
        # 協調的問題解決の分析
        analysis_prompt = f"""
以下の囚人のジレンマトーナメントの結果を分析してください：

エージェント統計:
{json.dumps(self.results['agent_stats'], ensure_ascii=False, indent=2)}

相互作用の一部:
{json.dumps(self.results['interactions'][:10], ensure_ascii=False, indent=2)}

分析してください：
1. 各エージェントの戦略の効果性
2. エージェント間の相互作用パターン
3. 協力を促進する要因
4. 競争と協力のバランス
5. 創発的な現象があったか

総合的な洞察を提供してください。
"""
        
        runner = Runner()
        analysis_result = await runner.run(self.coordinator, analysis_prompt)
        
        self.results["insights"].append({
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis_result.final_output
        })
        
        print(f"📈 分析結果:")
        print(analysis_result.final_output)
        
        return analysis_result.final_output
    
    async def collaborative_problem_solving(self):
        """協調的問題解決のデモ"""
        print(f"\n🤝 協調的問題解決フェーズ")
        
        problem = """
「持続可能な都市交通システムの設計」

課題：都市部の交通渋滞を解決しながら、環境負荷を最小化し、
市民の利便性を向上させる総合的な交通システムを設計してください。

制約条件：
- 限られた予算
- 既存インフラの活用
- 多様なステークホルダーの利害調整
- 技術的実現可能性

各エージェントは自分の戦略的特徴を活かした解決策を提案してください。
"""
        
        runner = Runner()
        solutions = {}
        
        # 各エージェントが個別に解決策を提案
        for agent in self.agents:
            print(f"\n  {agent.name}の提案:")
            result = await runner.run(agent, problem)
            solutions[agent.name] = result.final_output
            print(f"  {result.final_output[:200]}...")
        
        # 調整者が統合的解決策を提案
        integration_prompt = f"""
各エージェントが提案した都市交通システムの解決策を統合してください：

{chr(10).join([f"{name}: {solution}" for name, solution in solutions.items()])}

各提案の良い点を活かしながら、創発的で実現可能な統合解決策を提案してください。
異なる戦略的視点がどのように相互補完できるかも説明してください。
"""
        
        print(f"\n  調整者による統合:")
        integration_result = await runner.run(self.coordinator, integration_prompt)
        
        self.results["collaborative_solution"] = {
            "problem": problem,
            "individual_solutions": solutions,
            "integrated_solution": integration_result.final_output
        }
        
        print(f"  {integration_result.final_output}")
        
        return integration_result.final_output
    
    def save_results(self):
        """結果を保存"""
        os.makedirs("results", exist_ok=True)
        
        filename = f"results/demo_{self.results['experiment_id']}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 結果を保存しました: {filename}")


async def main():
    """メイン実行関数"""
    print("🚀 ゲーム理論的マルチエージェント実験デモ")
    print("=" * 60)
    
    # 環境変数チェック
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        # デモを実行
        demo = GameTheoryDemo()
        await demo.create_agents()
        
        print("✅ エージェント作成完了")
        
        # 1. ゲーム理論的相互作用
        await demo.run_multiple_rounds(rounds=5)
        
        # 2. 相互作用の分析
        await demo.analyze_interactions()
        
        # 3. 協調的問題解決
        await demo.collaborative_problem_solving()
        
        # 4. 結果保存
        demo.save_results()
        
        print("\n" + "=" * 60)
        print("✅ デモ実験完了")
        print("結果は results/ ディレクトリに保存されました")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())