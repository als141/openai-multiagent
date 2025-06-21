#!/usr/bin/env python
"""OpenAI Agents SDKの簡単なテスト"""

import asyncio
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

async def test_import():
    """インポートテスト"""
    print("🧪 インポートテスト")
    
    try:
        from agents import Agent, Runner
        print("  ✅ Agent, Runner インポート成功")
        
        # 基本エージェントを作成
        agent = Agent(
            name="TestAgent",
            instructions="あなたは協力的なテストエージェントです。"
        )
        print("  ✅ Agent 作成成功")
        
        # Runner を使って実行
        runner = Runner()
        result = await runner.run(agent, "こんにちは、簡単に自己紹介してください。")
        print("  ✅ 基本実行成功")
        print(f"  回答: {result.final_output}")
        
    except ImportError as e:
        print(f"  ❌ インポートエラー: {e}")
    except Exception as e:
        print(f"  ❌ 実行エラー: {e}")


async def test_handoffs():
    """ハンドオフテスト"""
    print("\n🤝 ハンドオフテスト")
    
    try:
        from agents import Agent, Runner, handoff
        print("  ✅ handoff インポート成功")
        
        # 専門エージェントを作成
        math_agent = Agent(
            name="数学者",
            instructions="あなたは数学の専門家です。"
        )
        
        coordinator = Agent(
            name="コーディネーター",
            instructions="適切な専門家に質問を転送してください。",
            handoffs=[handoff(math_agent)]
        )
        print("  ✅ ハンドオフ設定成功")
        
        # テスト実行
        runner = Runner()
        result = await runner.run(coordinator, "2 + 2 はいくつですか？")
        print("  ✅ ハンドオフ実行成功")
        print(f"  回答: {result.final_output}")
        
    except ImportError as e:
        print(f"  ❌ インポートエラー: {e}")
    except Exception as e:
        print(f"  ❌ 実行エラー: {e}")


async def test_multi_agents():
    """複数エージェント基本テスト"""
    print("\n👥 複数エージェント基本テスト")
    
    try:
        from agents import Agent, Runner
        
        # 異なる性格のエージェントを作成
        agents = [
            Agent(
                name="協力者",
                instructions="あなたは常に協力的で建設的な回答をします。"
            ),
            Agent(
                name="分析者", 
                instructions="あなたは論理的で分析的な回答をします。"
            ),
            Agent(
                name="創造者",
                instructions="あなたは創造的で革新的な回答をします。"
            )
        ]
        
        question = "チームワークを向上させる方法を一つ提案してください。"
        
        runner = Runner()
        responses = []
        
        for agent in agents:
            result = await runner.run(agent, question)
            responses.append(f"{agent.name}: {result.final_output}")
            print(f"  {agent.name}: {result.final_output}")
        
        print("  ✅ 複数エージェント実行成功")
        
        # 統合的な分析
        integrator = Agent(
            name="統合者",
            instructions="複数の視点を統合して最適な解決策を提案してください。"
        )
        
        integration_prompt = f"""
以下の3つの提案を統合して、最も効果的なチームワーク向上策を提案してください：

{chr(10).join(responses)}

各提案の良い点を組み合わせた総合的な解決策を提示してください。
"""
        
        result = await runner.run(integrator, integration_prompt)
        print(f"\n  統合解決策: {result.final_output}")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")


async def main():
    """メインテスト"""
    print("🚀 OpenAI Agents SDK 基本テスト開始")
    print("=" * 50)
    
    # APIキーチェック
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        await test_import()
        await test_handoffs()
        await test_multi_agents()
        
        print("\n" + "=" * 50)
        print("✅ 基本テスト完了")
        print("OpenAI Agents SDK が正常に動作しています")
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())