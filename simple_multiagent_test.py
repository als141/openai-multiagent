#!/usr/bin/env python
"""
シンプルなマルチエージェント会話テスト
OpenAI Agents SDKの機能確認用
"""

import asyncio
import os
from dotenv import load_dotenv

from agents import Agent, Runner, handoff
from agents.tracing import trace


async def simple_conversation_test():
    """シンプルな会話テスト"""
    print("🤖 シンプルマルチエージェント会話テスト")
    
    with trace("simple_multiagent_conversation"):
        # 3つのエージェントを作成
        alice = Agent(
            name="Alice",
            instructions="""
あなたはAliceです。協力的で温かい性格です。
他のエージェントとの関係を大切にし、建設的な対話を心がけます。
過去の会話内容を覚えており、それを参照して返答します。
"""
        )
        
        bob = Agent(
            name="Bob",
            instructions="""
あなたはBobです。分析的で論理的な性格です。
客観的な視点から物事を考え、データや事実に基づいて判断します。
過去の会話内容を覚えており、それを参照して返答します。
"""
        )
        
        charlie = Agent(
            name="Charlie",
            instructions="""
あなたはCharlieです。バランス感覚に優れた調整役です。
異なる意見をまとめ、公平で建設的な解決策を提案します。
過去の会話内容を覚えており、それを参照して返答します。
"""
        )
        
        # コーディネーター（ハンドオフ機能付き）
        coordinator = Agent(
            name="Coordinator",
            instructions="""
あなたは会話を促進するコーディネーターです。

参加者：
- Alice: 協力的で温かい性格
- Bob: 分析的で論理的な性格  
- Charlie: バランス感覚に優れた調整役

役割：
1. 適切なエージェントに会話をハンドオフする
2. 議論を活性化させる質問をする
3. 各エージェントの意見を統合する
4. 建設的で意味のある対話を促進する

自然で効果的な会話進行を心がけてください。
""",
            handoffs=[handoff(alice), handoff(bob), handoff(charlie)]
        )
        
        runner = Runner()
        
        # フェーズ1: 自己紹介
        print("\n=== フェーズ1: 自己紹介 ===")
        
        intro_result = await runner.run(coordinator, """
今日は3人のエージェントが集まって対話をします。
まず、Aliceさんから順番に自己紹介をお願いします。
お名前、性格、今日の対話への期待について話してください。
""")
        print(f"Coordinator: {intro_result.final_output}")
        
        # Aliceの自己紹介
        alice_intro = await runner.run(alice, """
コーディネーターから自己紹介を求められました。
お名前、性格、今日の対話への期待について自然に話してください。
話し終わったら、次はBobさんにお願いしてください。
""")
        print(f"\nAlice: {alice_intro.final_output}")
        
        # Bobの自己紹介
        bob_intro = await runner.run(bob, f"""
これまでの会話:
Coordinator: {intro_result.final_output}
Alice: {alice_intro.final_output}

Aliceさんの自己紹介を受けて、あなたも自己紹介をしてください。
話し終わったら、次はCharlieさんにお願いしてください。
""")
        print(f"\nBob: {bob_intro.final_output}")
        
        # Charlieの自己紹介
        charlie_intro = await runner.run(charlie, f"""
これまでの会話:
Coordinator: {intro_result.final_output}
Alice: {alice_intro.final_output}
Bob: {bob_intro.final_output}

AliceさんとBobさんの自己紹介を受けて、あなたも自己紹介をしてください。
""")
        print(f"\nCharlie: {charlie_intro.final_output}")
        
        # フェーズ2: テーマディスカッション
        print("\n=== フェーズ2: テーマディスカッション ===")
        
        discussion_start = await runner.run(coordinator, f"""
これまでの会話:
Alice: {alice_intro.final_output}
Bob: {bob_intro.final_output}
Charlie: {charlie_intro.final_output}

素晴らしい自己紹介でした。
次は「AIと人間の協力関係」について議論しましょう。
各自の視点から意見を述べてください。
まずAliceさんから意見をお聞かせください。
""")
        print(f"\nCoordinator: {discussion_start.final_output}")
        
        # Aliceの意見
        alice_opinion = await runner.run(alice, f"""
これまでの会話:
[自己紹介フェーズ]
Alice: {alice_intro.final_output}
Bob: {bob_intro.final_output}
Charlie: {charlie_intro.final_output}

[ディスカッション開始]
Coordinator: {discussion_start.final_output}

「AIと人間の協力関係」について、あなたの協力的な視点から意見を述べてください。
""")
        print(f"\nAlice: {alice_opinion.final_output}")
        
        # Bobの意見
        bob_opinion = await runner.run(bob, f"""
これまでの会話:
[自己紹介とディスカッション開始...]
Alice: {alice_opinion.final_output}

「AIと人間の協力関係」について、あなたの分析的な視点から意見を述べてください。
Aliceさんの意見も踏まえながら答えてください。
""")
        print(f"\nBob: {bob_opinion.final_output}")
        
        # Charlieの意見
        charlie_opinion = await runner.run(charlie, f"""
これまでの会話:
Alice: {alice_opinion.final_output}
Bob: {bob_opinion.final_output}

「AIと人間の協力関係」について、あなたのバランス感覚を活かした視点から意見を述べてください。
AliceさんとBobさんの意見も踏まえながら答えてください。
""")
        print(f"\nCharlie: {charlie_opinion.final_output}")
        
        # フェーズ3: 統合と創発的洞察
        print("\n=== フェーズ3: 統合と創発的洞察 ===")
        
        synthesis = await runner.run(coordinator, f"""
素晴らしい議論でした。各自の意見:

Alice: {alice_opinion.final_output}
Bob: {bob_opinion.final_output}
Charlie: {charlie_opinion.final_output}

これらの意見を統合して、新しい洞察や創発的なアイデアを見つけましょう。
3つの視点がどのように相互補完できるかも含めて総括してください。
""")
        print(f"\nCoordinator (統合): {synthesis.final_output}")
        
        # 最終感想
        print("\n=== 最終感想 ===")
        
        for agent_name, agent in [("Alice", alice), ("Bob", bob), ("Charlie", charlie)]:
            final_thoughts = await runner.run(agent, f"""
今日の対話全体を振り返って、印象に残ったことや学んだことを述べてください。

主な内容:
- 自己紹介フェーズ
- AIと人間の協力関係についての議論
- 統合されたアイデア: {synthesis.final_output[:200]}...

あなたの感想を聞かせてください。
""")
            print(f"\n{agent_name} (感想): {final_thoughts.final_output}")
    
    print("\n✅ シンプルマルチエージェント会話テスト完了")


async def main():
    """メイン関数"""
    print("🌟 シンプルマルチエージェント会話システム")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        await simple_conversation_test()
        print("\n🎉 実験成功！")
        print("OpenAI Agents SDKによる自律的マルチエージェント会話が実現できました")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())