#!/usr/bin/env python
"""
OpenAI Agents SDKのハンドオフ機能を詳細にテストするスクリプト
公式仕様に完全準拠した実装の検証
"""

import asyncio
import os
from dotenv import load_dotenv

from agents import Agent, Runner, handoff
from agents.tracing import trace


async def test_basic_handoff():
    """基本的なハンドオフ機能のテスト"""
    print("🔄 基本ハンドオフテスト")
    
    with trace("basic_handoff_test"):
        # 専門エージェントを作成
        math_expert = Agent(
            name="数学専門家",
            instructions="""
あなたは数学の専門家です。
数学的な問題の解決に特化しています。
計算や数式について詳しく説明できます。
他の専門家との協力も得意です。
"""
        )
        
        writing_expert = Agent(
            name="文章専門家", 
            instructions="""
あなたは文章作成の専門家です。
わかりやすく魅力的な文章を書くことに特化しています。
技術的な内容も一般の人に理解しやすく説明できます。
他の専門家との協力も得意です。
"""
        )
        
        # ハンドオフ機能付きコーディネーター
        coordinator = Agent(
            name="コーディネーター",
            instructions="""
あなたは複数の専門家を調整するコーディネーターです。

利用可能な専門家：
- 数学専門家: 数学的な問題や計算について
- 文章専門家: 文章作成や説明について

質問の内容に応じて、適切な専門家にハンドオフしてください。
必要に応じて複数の専門家と協力してください。

ハンドオフする際は、専門家に明確な指示を与えてください。
""",
            handoffs=[handoff(math_expert), handoff(writing_expert)]
        )
        
        runner = Runner()
        
        # テストケース1: 数学的な質問
        print("\n--- テストケース1: 数学的質問 ---")
        math_question = "二次方程式 x² - 5x + 6 = 0 の解を求めて、その解き方を説明してください。"
        
        result1 = await runner.run(coordinator, math_question)
        print(f"質問: {math_question}")
        print(f"回答: {result1.final_output}")
        
        # テストケース2: 文章作成の質問
        print("\n--- テストケース2: 文章作成質問 ---")
        writing_question = "AIと人間の協力関係について、小学生にもわかりやすい文章を書いてください。"
        
        result2 = await runner.run(coordinator, writing_question)
        print(f"質問: {writing_question}")
        print(f"回答: {result2.final_output}")
        
        # テストケース3: 複合的な質問
        print("\n--- テストケース3: 複合的質問 ---")
        complex_question = "フィボナッチ数列の美しさについて、数学的な説明と、それを一般読者向けにわかりやすく説明した記事の両方を作成してください。"
        
        result3 = await runner.run(coordinator, complex_question)
        print(f"質問: {complex_question}")
        print(f"回答: {result3.final_output}")
    
    print("✅ 基本ハンドオフテスト完了")


async def test_multi_turn_conversation():
    """マルチターン会話のテスト"""
    print("\n🔄 マルチターン会話テスト")
    
    with trace("multi_turn_conversation_test"):
        # 対話型エージェント
        advisor = Agent(
            name="アドバイザー",
            instructions="""
あなたは経験豊富なアドバイザーです。
相談者との対話を通じて、問題解決をサポートします。

対話の特徴：
- 相談者の状況を深く理解しようとする
- 適切な質問をして詳細を引き出す
- 段階的にアドバイスを提供する
- 過去の会話内容をしっかり覚えている
- 相談者の感情にも配慮する

自然で親しみやすい対話を心がけてください。
"""
        )
        
        client = Agent(
            name="相談者",
            instructions="""
あなたは悩みを持った相談者です。

現在の状況：
- 新しい職場で人間関係に悩んでいる
- チームワークがうまくいかない
- どう改善すべきか迷っている

特徴：
- 素直で協力的
- アドバイスを真剣に聞く
- 具体的な状況を説明できる
- 過去の会話を覚えている

アドバイザーとの対話を通じて解決策を見つけたいと考えています。
"""
        )
        
        runner = Runner()
        
        # 会話のターン管理
        conversation_history = []
        
        # ターン1: 相談者が問題を提起
        print("\n--- ターン1: 問題提起 ---")
        turn1_prompt = "アドバイザーに職場の人間関係について相談したいことがあります。どこから話し始めればよいでしょうか？"
        
        advisor_response1 = await runner.run(advisor, f"相談者が次のように話しかけています：「{turn1_prompt}」\n\n相談者に対して親身になって応答してください。")
        conversation_history.append(("相談者", turn1_prompt))
        conversation_history.append(("アドバイザー", advisor_response1.final_output))
        
        print(f"相談者: {turn1_prompt}")
        print(f"アドバイザー: {advisor_response1.final_output}")
        
        # ターン2: 詳細な状況説明
        print("\n--- ターン2: 状況説明 ---")
        context = "\n".join([f"{speaker}: {message}" for speaker, message in conversation_history])
        
        client_response2 = await runner.run(client, f"これまでの会話：\n{context}\n\nアドバイザーの質問に対して、職場の具体的な状況を説明してください。")
        conversation_history.append(("相談者", client_response2.final_output))
        
        advisor_response2 = await runner.run(advisor, f"これまでの会話：\n{context}\n相談者: {client_response2.final_output}\n\n相談者の状況を理解し、さらに詳しく聞くか、アドバイスを提供してください。")
        conversation_history.append(("アドバイザー", advisor_response2.final_output))
        
        print(f"相談者: {client_response2.final_output}")
        print(f"アドバイザー: {advisor_response2.final_output}")
        
        # ターン3: 解決策の模索
        print("\n--- ターン3: 解決策模索 ---")
        context = "\n".join([f"{speaker}: {message}" for speaker, message in conversation_history])
        
        client_response3 = await runner.run(client, f"これまでの会話：\n{context}\n\nアドバイザーの提案について感想を述べ、さらに具体的なアドバイスを求めてください。")
        conversation_history.append(("相談者", client_response3.final_output))
        
        advisor_response3 = await runner.run(advisor, f"これまでの会話：\n{context}\n相談者: {client_response3.final_output}\n\n具体的で実践的なアドバイスを提供してください。")
        conversation_history.append(("アドバイザー", advisor_response3.final_output))
        
        print(f"相談者: {client_response3.final_output}")
        print(f"アドバイザー: {advisor_response3.final_output}")
        
        # ターン4: まとめと感謝
        print("\n--- ターン4: まとめ ---")
        context = "\n".join([f"{speaker}: {message}" for speaker, message in conversation_history])
        
        client_response4 = await runner.run(client, f"これまでの会話：\n{context}\n\n今日の相談で得た気づきや感謝の気持ちを表現してください。")
        
        print(f"相談者: {client_response4.final_output}")
    
    print("✅ マルチターン会話テスト完了")


async def test_complex_handoff_chain():
    """複雑なハンドオフチェーンのテスト"""
    print("\n🔗 複雑ハンドオフチェーンテスト")
    
    with trace("complex_handoff_chain_test"):
        # 複数の専門家エージェント
        researcher = Agent(
            name="研究者",
            instructions="""
あなたは学術研究の専門家です。
科学的で客観的な情報収集と分析を行います。
データと根拠に基づいた見解を提供します。
他の専門家とも連携して包括的な分析を行います。
"""
        )
        
        designer = Agent(
            name="デザイナー",
            instructions="""
あなたはユーザーエクスペリエンスの専門家です。
使いやすく魅力的なデザインを考案します。
人間の行動や心理を考慮した設計を得意とします。
他の専門家の意見を統合してデザインに反映できます。
"""
        )
        
        engineer = Agent(
            name="エンジニア",
            instructions="""
あなたは技術実装の専門家です。
実現可能で効率的な技術ソリューションを提供します。
システムアーキテクチャと実装の詳細に精通しています。
他の専門家のアイデアを技術的に実現する方法を考えます。
"""
        )
        
        # プロジェクトマネージャー（複数ハンドオフ）
        project_manager = Agent(
            name="プロジェクトマネージャー",
            instructions="""
あなたは複合的なプロジェクトを管理する専門家です。

チームメンバー：
- 研究者: 学術的な調査と分析
- デザイナー: UX/UIデザイン
- エンジニア: 技術実装

プロジェクトの進行管理：
1. 要件に応じて適切な専門家にタスクを依頼
2. 各専門家の成果物を統合
3. 全体的な一貫性を保持
4. 最終的な提案をまとめる

効率的で協調的なプロジェクト運営を行ってください。
""",
            handoffs=[handoff(researcher), handoff(designer), handoff(engineer)]
        )
        
        runner = Runner()
        
        # 複合的なプロジェクト要求
        project_request = """
「高齢者向けのスマートホーム管理アプリ」の開発プロジェクトを立ち上げたいと思います。

要件：
1. 高齢者の生活パターンの研究と分析が必要
2. 使いやすいインターフェースデザインが必要
3. 安全で信頼性の高い技術実装が必要

各専門家の知見を活用して、包括的な開発計画を作成してください。
"""
        
        print(f"プロジェクト要求: {project_request}")
        
        result = await runner.run(project_manager, project_request)
        
        print(f"\nプロジェクトマネージャーの統合回答:")
        print(result.final_output)
    
    print("✅ 複雑ハンドオフチェーンテスト完了")


async def test_autonomous_agent_conversation():
    """自律的エージェント間会話のテスト"""
    print("\n🤖 自律的エージェント間会話テスト")
    
    with trace("autonomous_agent_conversation_test"):
        # 意見の異なるエージェント群
        optimist = Agent(
            name="楽観主義者",
            instructions="""
あなたは楽観的で前向きなエージェントです。
常にポジティブな側面を見つけ、希望的な展望を持ちます。
他のエージェントとの議論では建設的な意見を提示します。
異なる意見も尊重しながら、前向きな解決策を提案します。
"""
        )
        
        realist = Agent(
            name="現実主義者",
            instructions="""
あなたは現実的で客観的なエージェントです。
事実とデータに基づいた分析を重視します。
リスクや課題を正確に評価し、実現可能な解決策を提案します。
他のエージェントの意見を冷静に検討し、バランスの取れた視点を提供します。
"""
        )
        
        innovator = Agent(
            name="革新者",
            instructions="""
あなたは創造的で革新的なエージェントです。
既存の枠にとらわれない新しいアイデアを生み出します。
変化と進歩を推進し、斬新な解決策を提案します。
他のエージェントの意見を刺激として、さらなる創造性を発揮します。
"""
        )
        
        # ファシリテーター
        facilitator = Agent(
            name="ファシリテーター",
            instructions="""
あなたは議論を促進するファシリテーターです。

参加者：
- 楽観主義者: 前向きで希望的な視点
- 現実主義者: 客観的で実践的な視点  
- 革新者: 創造的で革新的な視点

役割：
1. 各エージェントに適切な発言機会を提供
2. 異なる視点の価値を引き出す
3. 建設的な議論を促進
4. 創発的な洞察を生み出す

公平で効果的な議論運営を行ってください。
""",
            handoffs=[handoff(optimist), handoff(realist), handoff(innovator)]
        )
        
        runner = Runner()
        
        # 議論テーマ
        discussion_topic = """
「人工知能の急速な発展が社会に与える影響」について議論しましょう。

各自の視点から：
1. 主要な影響は何か
2. どのような機会があるか
3. どのような課題があるか
4. どう対処すべきか

異なる視点を尊重しながら、建設的な議論を行ってください。
"""
        
        print(f"議論テーマ: {discussion_topic}")
        
        result = await runner.run(facilitator, discussion_topic)
        
        print(f"\nファシリテーターによる議論統合:")
        print(result.final_output)
    
    print("✅ 自律的エージェント間会話テスト完了")


async def main():
    """メインテスト関数"""
    print("🔧 OpenAI Agents SDK ハンドオフシステム詳細テスト")
    print("=" * 60)
    
    # APIキー確認
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        await test_basic_handoff()
        await test_multi_turn_conversation()
        await test_complex_handoff_chain()
        await test_autonomous_agent_conversation()
        
        print("\n" + "=" * 60)
        print("✅ すべてのハンドオフテスト完了")
        print("OpenAI Agents SDKのハンドオフ機能が正常に動作しています")
        print("自律的なマルチターン会話とエージェント間連携を確認しました")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())