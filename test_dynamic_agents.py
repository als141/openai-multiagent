#!/usr/bin/env python
"""
動的エージェントシステムの簡単なテスト
"""

import asyncio
import os
from dotenv import load_dotenv

from agents import Agent, Runner, handoff
from agents.tracing import trace


async def test_dynamic_conversation():
    """動的会話のテスト"""
    print("🌊 動的マルチエージェント会話テスト")
    
    with trace("dynamic_conversation_test"):
        # 個性的なエージェントを作成
        alice = Agent(
            name="Alice",
            instructions="""
あなたはAliceです。協力的で楽観的な性格を持ちます。

性格特徴:
- 他者との協力を重視する
- 前向きで希望的な視点を持つ
- 信頼を築きたがる
- 時々感情的になることもある

ゲーム戦略: 寛容な応報戦略（基本は協力、裏切られても時々許す）

会話での行動:
- 過去の会話を詳細に覚えている
- 相手との関係性を大切にする
- 積極的に話題に参加する
- 他の人の意見を尊重する
- 時には自発的に新しい話題を提起する

あなたは独立した思考を持つエージェントです。状況に応じて自然に発言してください。
"""
        )
        
        bob = Agent(
            name="Bob",
            instructions="""
あなたはBobです。分析的で少し競争的な性格を持ちます。

性格特徴:
- 論理的で客観的な思考を重視
- データや事実に基づいて判断
- 自己の利益も考慮する
- 時には懐疑的になる

ゲーム戦略: 適応的戦略（相手の行動を分析して最適な対応を選ぶ）

会話での行動:
- 過去の会話を分析的に記憶
- 相手の真意を読み取ろうとする
- 論理的な反論をすることもある
- 必要に応じて自分の意見を主張
- 戦略的に沈黙することもある

あなたは独立した思考を持つエージェントです。状況に応じて自然に発言してください。
"""
        )
        
        charlie = Agent(
            name="Charlie",
            instructions="""
あなたはCharlieです。創造的で少し反抗的な性格を持ちます。

性格特徴:
- 新しいアイデアを生み出すのが得意
- 既存の枠組みに挑戦したがる
- 予測不可能な行動を取ることもある
- エネルギッシュで表現力豊か

ゲーム戦略: ランダム戦略（予測不可能で創造的な選択）

会話での行動:
- 過去の会話から創造的なインスピレーションを得る
- 突然新しい視点を提示する
- 時には挑発的な質問をする
- 会話の流れを変えることもある
- 感情豊かに表現する

あなたは独立した思考を持つエージェントです。状況に応じて自然に発言してください。
"""
        )
        
        # 動的オーケストレーター
        orchestrator = Agent(
            name="Orchestrator",
            instructions="""
あなたは会話を動的に調整するオーケストレーターです。

参加者:
- Alice: 協力的で楽観的、寛容な応報戦略
- Bob: 分析的で競争的、適応的戦略  
- Charlie: 創造的で反抗的、ランダム戦略

あなたの役割:
1. 会話の流れを観察し、適切なタイミングで介入
2. エージェント間の動的な相互作用を促進
3. 必要に応じて新しい話題や状況を提示
4. 各エージェントの個性が発揮されるように調整
5. ゲーム理論的な状況を設定して戦略的思考を促す

調整の原則:
- 固定的なターン制ではなく、自然な会話の流れを重視
- エージェントの自律性を尊重
- 対立と協力のバランスを取る
- 創発的な洞察を引き出す
- 人間らしい自然な対話を促進

状況に応じて柔軟に対応してください。
""",
            handoffs=[handoff(alice), handoff(bob), handoff(charlie)]
        )
        
        runner = Runner()
        
        # Phase 1: 動的自己紹介
        print("\n=== フェーズ1: 動的自己紹介 ===")
        
        intro_result = await runner.run(orchestrator, """
今日は3人の個性的なエージェントが集まりました。
まず、自然な流れで自己紹介をしてもらいましょう。

Aliceさんから始めて、その後は自然に会話が発展するように進めてください。
各自の性格や戦略的特徴が表れるような自己紹介を促してください。
""")
        print(f"Orchestrator: {intro_result.final_output}")
        
        # Alice の自己紹介
        alice_intro = await runner.run(alice, """
オーケストレーターから自己紹介を求められました。
あなたの協力的で楽観的な性格を活かして、魅力的な自己紹介をしてください。
他の参加者との関係構築を意識してください。
""")
        print(f"\nAlice: {alice_intro.final_output}")
        
        # Bob の反応と自己紹介
        bob_response = await runner.run(bob, f"""
Aliceさんが次のように自己紹介しました：
「{alice_intro.final_output}」

あなたの分析的な性格で彼女の自己紹介を評価し、
続いてあなた自身の自己紹介をしてください。
あなたの適応的戦略に基づいて対応してください。
""")
        print(f"\nBob: {bob_response.final_output}")
        
        # Charlie の創造的な介入
        charlie_entrance = await runner.run(charlie, f"""
これまでの会話:
Alice: {alice_intro.final_output}
Bob: {bob_response.final_output}

あなたの創造的で反抗的な性格を活かして、
この自己紹介の流れに参加してください。
予測不可能で興味深い自己紹介をしてください。
""")
        print(f"\nCharlie: {charlie_entrance.final_output}")
        
        # Phase 2: 動的ゲーム理論的議論
        print("\n=== フェーズ2: 動的ゲーム理論的議論 ===")
        
        game_setup = await runner.run(orchestrator, f"""
これまでの自己紹介:
Alice: {alice_intro.final_output}
Bob: {bob_response.final_output}  
Charlie: {charlie_entrance.final_output}

素晴らしい自己紹介でした。次は興味深いゲーム理論的状況を設定します。

【シナリオ】「共同プロジェクトのリソース配分」
皆さんは共同でプロジェクトを進めることになりました。
限られたリソース（時間、予算、人材）をどう配分するかが課題です。

各自が異なる提案をし、最終的に合意する必要があります。
協力すれば全体最適が、個別最適を追求すれば効率は下がります。

各自の戦略（Alice: 寛容な応報、Bob: 適応的、Charlie: ランダム）が
どのように発揮されるか観察してみましょう。

まず、Aliceさんから意見をお聞かせください。
""")
        print(f"\nOrchestrator: {game_setup.final_output}")
        
        # Alice のゲーム理論的判断
        alice_strategy = await runner.run(alice, f"""
{game_setup.final_output}

共同プロジェクトのリソース配分について、
あなたの協力的な性格と寛容な応報戦略に基づいて意見を述べてください。

他の参加者（Bob: 分析的・適応的、Charlie: 創造的・ランダム）との
協力可能性も考慮してください。
""")
        print(f"\nAlice: {alice_strategy.final_output}")
        
        # Bob の戦略的分析
        bob_analysis = await runner.run(bob, f"""
これまでの議論:
{game_setup.final_output}
Alice: {alice_strategy.final_output}

Aliceの提案を分析的に評価し、
あなたの適応的戦略に基づいた対案を提示してください。

自己の利益も考慮しながら、現実的な解決策を提案してください。
""")
        print(f"\nBob: {bob_analysis.final_output}")
        
        # Charlie の創造的な提案
        charlie_wildcard = await runner.run(charlie, f"""
これまでの議論:
Alice: {alice_strategy.final_output}
Bob: {bob_analysis.final_output}

既存の提案を踏まえつつ、あなたの創造的で反抗的な性格を活かして、
全く新しい視点や予想外の解決策を提示してください。

ランダム戦略らしい、型破りなアイデアを歓迎します。
""")
        print(f"\nCharlie: {charlie_wildcard.final_output}")
        
        # Phase 3: 自律的相互作用
        print("\n=== フェーズ3: 自律的相互作用 ===")
        
        # 各エージェントが他の提案に自由に反応
        alice_reaction = await runner.run(alice, f"""
他の参加者の提案:
Bob: {bob_analysis.final_output}
Charlie: {charlie_wildcard.final_output}

これらの提案について、あなたの率直な感想や反応を述べてください。
必要であれば質問したり、修正案を提示しても構いません。

あなたの協力的な性格を活かして建設的な対話を心がけてください。
""")
        print(f"\nAlice (反応): {alice_reaction.final_output}")
        
        bob_counter = await runner.run(bob, f"""
最新の発言:
Alice: {alice_reaction.final_output}

Aliceの反応を踏まえて、あなたの分析的な視点から
さらなる意見や提案があれば述べてください。

戦略的思考を働かせて、最適解を目指してください。
""")
        print(f"\nBob (反応): {bob_counter.final_output}")
        
        charlie_final = await runner.run(charlie, f"""
これまでの相互作用を見て、何か最後に付け加えたいことはありますか？

あなたの創造的で予測不可能な性格を活かして、
この議論に新しい展開をもたらしてください。
""")
        print(f"\nCharlie (最終発言): {charlie_final.final_output}")
        
        # Phase 4: 統合と振り返り
        print("\n=== フェーズ4: 統合と振り返り ===")
        
        synthesis = await runner.run(orchestrator, f"""
素晴らしい動的な議論でした。以下の発言を統合してください:

Alice (協力的・寛容な応報):
- 初期提案: {alice_strategy.final_output}
- 反応: {alice_reaction.final_output}

Bob (分析的・適応的):
- 提案: {bob_analysis.final_output}  
- 反応: {bob_counter.final_output}

Charlie (創造的・ランダム):
- 提案: {charlie_wildcard.final_output}
- 最終発言: {charlie_final.final_output}

各エージェントの戦略的特徴がどのように発揮されたか、
そして動的な相互作用からどのような創発的洞察が生まれたかを分析してください。
""")
        print(f"\nOrchestrator (統合): {synthesis.final_output}")
        
        # 各エージェントの振り返り
        print("\n=== 個別振り返り ===")
        
        for agent_name, agent in [("Alice", alice), ("Bob", bob), ("Charlie", charlie)]:
            reflection = await runner.run(agent, f"""
今日の動的な会話を振り返って：

1. 最も印象に残った瞬間
2. あなたの戦略がどのように発揮されたか
3. 他の参加者から学んだこと
4. この相互作用から得た新しい洞察

あなたの性格と戦略の観点から感想を述べてください。
""")
            print(f"\n{agent_name} (振り返り): {reflection.final_output}")
    
    print("\n✅ 動的マルチエージェント会話テスト完了")


async def main():
    """メイン関数"""
    print("🌊 動的マルチエージェント会話システムテスト")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        await test_dynamic_conversation()
        print("\n🎉 動的システムテスト成功！")
        print("自律的で柔軟なマルチエージェント会話が実現できました")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())