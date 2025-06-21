#!/usr/bin/env python
"""OpenAI Agents SDKの基本機能をテストするスクリプト"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from agents import Agent, Runner, RunConfig


async def test_basic_agent():
    """基本的なエージェント機能をテスト"""
    print("🧪 基本エージェント機能のテスト")
    
    # シンプルなエージェントを作成
    agent = Agent(
        name="TestAgent",
        instructions="あなたは協力的で知的なテスト用エージェントです。簡潔に答えてください。"
    )
    
    # 基本的な質問
    runner = Runner()
    test_questions = [
        "2+2の答えは？",
        "ゲーム理論の囚人のジレンマについて一文で説明してください。",
        "協力と競争のバランスについてどう考えますか？"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n  テスト {i}: {question}")
        try:
            result = await runner.run(agent, question, config=RunConfig(
                max_token_count=100,
                save_sensitive_data=False
            ))
            print(f"  答え: {result.final_output}")
        except Exception as e:
            print(f"  エラー: {e}")
    
    print("✅ 基本エージェントテスト完了")


async def test_multi_agent_handoff():
    """マルチエージェントとハンドオフをテスト"""
    print("\n🤝 マルチエージェントハンドオフのテスト")
    
    # 2つの専門エージェントを作成
    math_agent = Agent(
        name="数学者",
        instructions="あなたは数学の専門家です。数学的な問題を解決します。"
    )
    
    philosopher_agent = Agent(
        name="哲学者", 
        instructions="あなたは哲学の専門家です。倫理的・哲学的な問題を考察します。"
    )
    
    # ハンドオフを設定
    from agents.tools import handoff
    coordinator = Agent(
        name="コーディネーター",
        instructions="質問の内容に応じて適切な専門家に回答を依頼してください。",
        handoffs=[handoff(math_agent), handoff(philosopher_agent)]
    )
    
    # テスト質問
    test_cases = [
        "確率論の基本について教えてください",
        "人工知能の倫理的な課題について考察してください",
        "ゲーム理論における協力の価値について"  # 両方の専門性が必要
    ]
    
    runner = Runner()
    for i, question in enumerate(test_cases, 1):
        print(f"\n  テストケース {i}: {question}")
        try:
            result = await runner.run(coordinator, question, config=RunConfig(
                max_token_count=200,
                save_sensitive_data=False
            ))
            print(f"  回答: {result.final_output[:150]}...")
        except Exception as e:
            print(f"  エラー: {e}")
    
    print("✅ ハンドオフテスト完了")


async def test_game_theory_simulation():
    """ゲーム理論シミュレーションの簡単なテスト"""
    print("\n🎮 ゲーム理論シミュレーションのテスト")
    
    # 協力的エージェント
    cooperative_agent = Agent(
        name="協力者",
        instructions="あなたは常に協力を選ぶ戦略を取ります。囚人のジレンマでは常にCOOPERATE（協力）を選択します。"
    )
    
    # 競争的エージェント
    competitive_agent = Agent(
        name="競争者",
        instructions="あなたは自己利益を最大化する戦略を取ります。囚人のジレンマでは基本的にDEFECT（裏切り）を選択します。"
    )
    
    # 囚人のジレンマをシミュレート
    scenario = """
囚人のジレンマゲーム:
- COOPERATE（協力）: 両者が協力すれば両者とも利得+3
- DEFECT（裏切り）: 一方が裏切れば裏切った側+5、裏切られた側0
- 両者裏切りなら両者とも利得+1

相手の戦略は分からない状況で、あなたの選択は？
COOPERATE または DEFECT で答えてください。理由も簡潔に。
"""
    
    runner = Runner()
    
    agents = [cooperative_agent, competitive_agent]
    for agent in agents:
        print(f"\n  {agent.name}の選択:")
        try:
            result = await runner.run(agent, scenario, config=RunConfig(
                max_token_count=150,
                save_sensitive_data=False
            ))
            action = "COOPERATE" if "COOPERATE" in result.final_output.upper() else "DEFECT"
            print(f"  行動: {action}")
            print(f"  理由: {result.final_output}")
        except Exception as e:
            print(f"  エラー: {e}")
    
    print("✅ ゲーム理論シミュレーションテスト完了")


async def test_knowledge_sharing():
    """知識共有の簡単なテスト"""
    print("\n🧠 知識共有のテスト")
    
    # 異なる専門知識を持つエージェント
    agents = [
        Agent(
            name="技術者",
            instructions="あなたは技術的な専門知識を持ちます。イノベーションと効率性を重視します。"
        ),
        Agent(
            name="社会学者", 
            instructions="あなたは社会的な専門知識を持ちます。人間関係と社会影響を重視します。"
        ),
        Agent(
            name="経済学者",
            instructions="あなたは経済的な専門知識を持ちます。コストと利益を重視します。"
        )
    ]
    
    # 統合的な問題
    problem = """
「リモートワークの普及による社会変化」について、
あなたの専門分野の観点から重要なポイントを1つ提示してください。
他の専門家と協力することを前提に、50文字以内で要点を述べてください。
"""
    
    runner = Runner()
    perspectives = []
    
    for agent in agents:
        print(f"\n  {agent.name}の視点:")
        try:
            result = await runner.run(agent, problem, config=RunConfig(
                max_token_count=100,
                save_sensitive_data=False
            ))
            perspective = result.final_output
            perspectives.append(f"{agent.name}: {perspective}")
            print(f"  観点: {perspective}")
        except Exception as e:
            print(f"  エラー: {e}")
    
    # 統合的な議論を促進
    if perspectives:
        integration_prompt = f"""
以下の専門家の観点を統合して、リモートワークの普及による社会変化について
総合的な洞察を提示してください：

{chr(10).join(perspectives)}

各観点を考慮して、創発的な解決策や新しい視点を提案してください。
"""
        
        integrator = Agent(
            name="統合者",
            instructions="複数の専門的観点を統合し、創発的な洞察を生み出すことができます。"
        )
        
        print(f"\n  統合的洞察:")
        try:
            result = await runner.run(integrator, integration_prompt, config=RunConfig(
                max_token_count=300,
                save_sensitive_data=False
            ))
            print(f"  統合結果: {result.final_output}")
        except Exception as e:
            print(f"  エラー: {e}")
    
    print("✅ 知識共有テスト完了")


async def main():
    """メインテスト関数"""
    print("🚀 OpenAI Agents SDK 統合テスト開始")
    print("=" * 50)
    
    # 環境変数チェック
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        print("  .env ファイルに OPENAI_API_KEY=sk-... を設定してください")
        return
    
    try:
        # 各テストを実行
        await test_basic_agent()
        await test_multi_agent_handoff()
        await test_game_theory_simulation()
        await test_knowledge_sharing()
        
        print("\n" + "=" * 50)
        print("✅ すべてのテストが完了しました")
        print("OpenAI Agents SDKの基本機能が正常に動作しています")
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 環境変数を読み込み
    load_dotenv()
    
    # テストを実行
    asyncio.run(main())