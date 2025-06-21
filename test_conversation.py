#!/usr/bin/env python
"""会話機能の簡単なテスト"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加  
sys.path.insert(0, str(Path(__file__).parent))

from agents import Agent, Runner
from agents.tracing import trace

async def test_basic_conversation():
    """基本的な会話機能をテスト"""
    print("🧪 基本会話テスト")
    
    with trace("basic_conversation_test"):
        # 2つのエージェントを作成
        alice = Agent(
            name="Alice",
            instructions="""
あなたはAliceです。協力的で温かい性格を持っています。
過去の会話を覚えており、相手との関係を大切にします。
自然で人間らしい会話を心がけてください。
"""
        )
        
        bob = Agent(
            name="Bob", 
            instructions="""
あなたはBobです。分析的で合理的な性格を持っています。
過去の会話を覚えており、論理的な議論を好みます。
自然で人間らしい会話を心がけてください。
"""
        )
        
        runner = Runner()
        
        # Aliceから会話開始
        alice_prompt = "Bobさん、初めまして！私はAliceです。あなたについて教えてもらえますか？"
        
        print(f"\nAlice: {alice_prompt}")
        
        # Bobが応答
        bob_response = await runner.run(bob, f"Aliceという人が次のように話しかけています：「{alice_prompt}」\n\nAliceに対して自然に返答してください。")
        print(f"Bob: {bob_response.final_output}")
        
        # Aliceが返答
        alice_response = await runner.run(alice, f"Bobさんが次のように返答しました：「{bob_response.final_output}」\n\nBobさんに対して続けて会話してください。")
        print(f"Alice: {alice_response.final_output}")
        
        # もう一往復
        bob_response2 = await runner.run(bob, f"これまでの会話：\nAlice: {alice_prompt}\nBob: {bob_response.final_output}\nAlice: {alice_response.final_output}\n\nAliceに対して会話を続けてください。")
        print(f"Bob: {bob_response2.final_output}")
    
    print("✅ 基本会話テスト完了")


async def test_game_conversation():
    """ゲーム理論的な会話テスト"""
    print("\n🎮 ゲーム会話テスト")
    
    with trace("game_conversation_test"):
        # 協力的エージェント
        cooperative = Agent(
            name="協力者",
            instructions="""
あなたは協力的な戦略を好むエージェントです。
囚人のジレンマでは基本的に協力(COOPERATE)を選択します。
相手との関係を重視し、長期的な信頼関係を構築したいと考えています。
自然で人間らしい言葉遣いで話してください。
"""
        )
        
        # 競争的エージェント
        competitive = Agent(
            name="競争者",
            instructions="""
あなたは戦略的で合理的なエージェントです。
囚人のジレンマでは慎重に判断し、時には競争(DEFECT)も選択します。
効率と結果を重視しますが、公平性も考慮します。
自然で人間らしい言葉遣いで話してください。
"""
        )
        
        runner = Runner()
        
        # ゲーム前の相談
        game_setup = """
これから囚人のジレンマゲームをプレイします。

ルール：
- COOPERATE（協力）: 両者協力なら両者+3点、一方的協力なら0点
- DEFECT（競争）: 一方的競争なら+5点、両者競争なら+1点

ゲームを始める前に、お互いの考えを聞かせてください。
"""
        
        print(f"\n状況: {game_setup}")
        
        # 協力者の意見
        coop_opinion = await runner.run(cooperative, f"{game_setup}\n\nあなたの考えや戦略について話してください。")
        print(f"\n協力者: {coop_opinion.final_output}")
        
        # 競争者の応答
        comp_response = await runner.run(competitive, f"{game_setup}\n\n協力者が次のように言いました：「{coop_opinion.final_output}」\n\nこれに対するあなたの考えを述べてください。")
        print(f"競争者: {comp_response.final_output}")
        
        # 実際のゲーム決定
        coop_decision = await runner.run(cooperative, f"""
これまでの会話を踏まえて、囚人のジレンマでの行動を決定してください。

会話履歴：
協力者（あなた）: {coop_opinion.final_output}
競争者: {comp_response.final_output}

選択肢: COOPERATE または DEFECT
あなたの選択と理由を述べてください。
""")
        
        comp_decision = await runner.run(competitive, f"""
これまでの会話を踏まえて、囚人のジレンマでの行動を決定してください。

会話履歴：
協力者: {coop_opinion.final_output}
競争者（あなた）: {comp_response.final_output}

選択肢: COOPERATE または DEFECT
あなたの選択と理由を述べてください。
""")
        
        print(f"\n協力者の決定: {coop_decision.final_output}")
        print(f"競争者の決定: {comp_decision.final_output}")
        
        # 結果に対する感想
        coop_action = "COOPERATE" if "COOPERATE" in coop_decision.final_output.upper() else "DEFECT"
        comp_action = "COOPERATE" if "COOPERATE" in comp_decision.final_output.upper() else "DEFECT"
        
        print(f"\n📊 結果: 協力者={coop_action}, 競争者={comp_action}")
        
        # 感想交換
        coop_reflection = await runner.run(cooperative, f"""
ゲーム結果：あなた={coop_action}, 相手={comp_action}

この結果について、どう感じましたか？
相手との今後の関係についても話してください。
""")
        
        comp_reflection = await runner.run(competitive, f"""
ゲーム結果：あなた={comp_action}, 相手={coop_action}

この結果について、どう感じましたか？
相手との今後の関係についても話してください。
""")
        
        print(f"\n協力者の感想: {coop_reflection.final_output}")
        print(f"競争者の感想: {comp_reflection.final_output}")
    
    print("✅ ゲーム会話テスト完了")


async def test_group_discussion():
    """グループディスカッションのテスト"""
    print("\n👥 グループディスカッションテスト")
    
    with trace("group_discussion_test"):
        # 3つのエージェントを作成
        agents = [
            Agent(
                name="理想主義者",
                instructions="あなたは理想を追求し、協力と調和を重視するエージェントです。"
            ),
            Agent(
                name="現実主義者", 
                instructions="あなたは現実的で実用性を重視するエージェントです。"
            ),
            Agent(
                name="革新者",
                instructions="あなたは創造的で新しいアイデアを生み出すのが得意なエージェントです。"
            )
        ]
        
        topic = "AIと人間の共存について"
        
        runner = Runner()
        
        print(f"\nトピック: {topic}")
        
        # 各エージェントの初期意見
        opinions = {}
        for agent in agents:
            opinion = await runner.run(agent, f"「{topic}」について、あなたの考えを述べてください。")
            opinions[agent.name] = opinion.final_output
            print(f"\n{agent.name}: {opinion.final_output}")
        
        # 相互作用
        print(f"\n--- 相互作用フェーズ ---")
        
        for agent in agents:
            other_opinions = [f"{name}: {op}" for name, op in opinions.items() if name != agent.name]
            
            interaction = await runner.run(agent, f"""
他の参加者の意見：
{chr(10).join(other_opinions)}

これらの意見を聞いて、あなたの追加の考えや反応を述べてください。
"""
            )
            print(f"\n{agent.name} (応答): {interaction.final_output}")
    
    print("✅ グループディスカッションテスト完了")


async def main():
    """メインテスト関数"""
    print("🚀 会話機能テスト開始")
    print("=" * 50)
    
    # APIキー確認
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        await test_basic_conversation()
        await test_game_conversation()
        await test_group_discussion()
        
        print("\n" + "=" * 50)
        print("✅ すべての会話テスト完了")
        print("OpenAI Agents SDKによる人間らしい会話が実現できています")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())