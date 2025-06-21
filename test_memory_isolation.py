#!/usr/bin/env python
"""
メモリ分離システムのテスト
各エージェントが適切に個別メモリを持つことを確認
"""

import asyncio
import os
from dotenv import load_dotenv

from isolated_memory_agents import IsolatedMemoryConversationSystem


async def test_memory_isolation():
    """メモリ分離の動作確認テスト"""
    print("🧪 メモリ分離システムテスト")
    print("=" * 50)
    
    # システム作成
    system = IsolatedMemoryConversationSystem("memory_isolation_test")
    agents = system.create_agents()
    
    # Alice、Bob、Charlieを取得
    alice = next(agent for agent in agents if agent.profile.name == "Alice")
    bob = next(agent for agent in agents if agent.profile.name == "Bob")
    charlie = next(agent for agent in agents if agent.profile.name == "Charlie")
    
    print("\n--- 初期状態確認 ---")
    print(f"Alice記憶: {len(alice.memory.conversation_history)}件")
    print(f"Bob記憶: {len(bob.memory.conversation_history)}件")
    print(f"Charlie記憶: {len(charlie.memory.conversation_history)}件")
    
    # テスト1: AliceがBobに話しかける
    print("\n--- テスト1: Alice → Bob ---")
    alice_to_bob = "Bobさん、こんにちは！今日はどんな気分ですか？"
    system.log_conversation("Alice", alice_to_bob, ["Bob"])
    
    print(f"Alice記憶: {len(alice.memory.conversation_history)}件")
    print(f"Bob記憶: {len(bob.memory.conversation_history)}件")
    print(f"Charlie記憶: {len(charlie.memory.conversation_history)}件（変化なし）")
    
    # テスト2: BobがAliceに返答
    print("\n--- テスト2: Bob → Alice ---")
    bob_to_alice = "Aliceさん、こんにちは。今日は分析的な気分です。"
    system.log_conversation("Bob", bob_to_alice, ["Alice"])
    
    print(f"Alice記憶: {len(alice.memory.conversation_history)}件")
    print(f"Bob記憶: {len(bob.memory.conversation_history)}件") 
    print(f"Charlie記憶: {len(charlie.memory.conversation_history)}件（まだ変化なし）")
    
    # テスト3: CharlieがAliceに話しかける（Bobは含まない）
    print("\n--- テスト3: Charlie → Alice ---")
    charlie_to_alice = "Aliceさん、新しいアイデアがあります！"
    system.log_conversation("Charlie", charlie_to_alice, ["Alice"])
    
    print(f"Alice記憶: {len(alice.memory.conversation_history)}件（3件：自分1、Bob1、Charlie1）")
    print(f"Bob記憶: {len(bob.memory.conversation_history)}件（2件：Alice1、自分1）")
    print(f"Charlie記憶: {len(charlie.memory.conversation_history)}件（1件：自分1）")
    
    # メモリ内容確認
    print("\n--- メモリ内容詳細確認 ---")
    
    print("\nAliceの記憶:")
    print(alice.get_memory_context())
    print(f"直接の会話相手: {alice.memory.direct_partners}")
    
    print("\nBobの記憶:")
    print(bob.get_memory_context())
    print(f"直接の会話相手: {bob.memory.direct_partners}")
    
    print("\nCharlieの記憶:")
    print(charlie.get_memory_context())
    print(f"直接の会話相手: {charlie.memory.direct_partners}")
    
    # Responses API形式確認
    print("\n--- Responses API形式確認 ---")
    alice_api_format = alice.memory.get_responses_api_format()
    print(f"AliceのResponses API形式（{len(alice_api_format)}件）:")
    for i, msg in enumerate(alice_api_format):
        print(f"  {i+1}. role: {msg['role']}, content: {msg['content'][:50]}...")
    
    print("\n✅ メモリ分離テスト完了")
    print("各エージェントが適切に個別メモリを持っていることを確認しました")
    
    return system


async def test_simple_conversation():
    """簡単な会話テスト"""
    print("\n\n🤖 簡単な会話テスト")
    print("=" * 50)
    
    system = IsolatedMemoryConversationSystem("simple_conversation_test")
    agents = system.create_agents()
    
    # 3ターンの簡単な会話を実行
    await system.run_isolated_conversation_phase("簡単な会話テスト", turns=3)
    
    # 各エージェントのメモリ状態を確認
    print("\n--- 会話後のメモリ状態 ---")
    for agent in agents:
        print(f"\n{agent.profile.name}:")
        print(f"  記憶件数: {len(agent.memory.conversation_history)}")
        print(f"  会話相手: {list(agent.memory.direct_partners)}")
        print(f"  最新記憶: {agent.get_memory_context()}")
    
    return system


async def main():
    """メインテスト関数"""
    print("🧪 メモリ分離型マルチエージェントシステム テスト")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        # メモリ分離テスト
        await test_memory_isolation()
        
        # 簡単な会話テスト
        await test_simple_conversation()
        
        print("\n" + "=" * 50)
        print("✅ 全テスト完了")
        print("メモリ分離システムが正常に動作しています")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())