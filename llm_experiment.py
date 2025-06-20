#!/usr/bin/env python3
"""
OpenAI LLMを使用したゲーム理論実験

このスクリプトは実際にOpenAI GPT-4を使用してエージェント間の
戦略的相互作用を実行し、詳細な会話履歴と推論過程を記録します。
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# srcをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.coordinator import GameCoordinator, ExperimentConfig
from game_theory.games import GameType
from utils.conversation_tracker import conversation_tracker
from agents.llm_agent import LLMAgentFactory


async def llm_experiment_demo():
    """LLMエージェントによるデモ実験を実行"""
    
    print("🤖 OpenAI LLMエージェント実験開始")
    print("=" * 50)
    
    # APIキーの確認
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")
        return
    
    print(f"✅ OpenAI APIキーが設定されています (長さ: {len(api_key)})")
    
    # コーディネーターを作成
    coordinator = GameCoordinator(
        logger_name="llm_experiment",
        log_level="INFO",
        results_dir="llm_results"
    )
    
    print("\n🧠 LLMエージェントを作成中...")
    
    # 多様なLLMエージェントを作成
    agents_config = [
        ("タロウ_協力者", "cooperative", "日本人の協力的なエージェント"),
        ("ハナコ_競争者", "competitive", "戦略的で競争志向の日本人エージェント"),
        ("ケンジ_報復者", "tit_for_tat", "相手の行動を真似する慎重な日本人エージェント"),
        ("アイ_適応者", "adaptive", "学習能力の高い適応的な日本人エージェント")
    ]
    
    for name, strategy, description in agents_config:
        agent = coordinator.create_agent(
            strategy, 
            name, 
            use_llm=True,
            model="gpt-4o-mini",  # コスト効率の良いモデルを使用
            instructions=f"あなたは{description}です。日本語で思考し、戦略的に行動してください。"
        )
        print(f"  ✅ {name} ({strategy}) - {type(agent).__name__}")
    
    print(f"\n📊 作成されたエージェント: {len(coordinator.agents)}体")
    
    # 実験設定
    config = ExperimentConfig(
        game_types=[
            GameType.PRISONERS_DILEMMA,
            GameType.KNOWLEDGE_SHARING
        ],
        agent_types=list(set(agent.strategy for agent in coordinator.agents.values())),
        num_rounds=3,  # LLM使用時は短く設定
        num_repetitions=2,
        save_results=True,
        results_dir="llm_results",
        enable_conversation_tracking=True,  # 重要：会話追跡を有効化
        enable_detailed_logging=True,
        experiment_description="OpenAI LLMエージェントによるゲーム理論実験 - 日本語推論・戦略的意思決定"
    )
    
    print(f"\n🎯 実験設定:")
    print(f"  - ゲームタイプ: {[gt.value for gt in config.game_types]}")
    print(f"  - ラウンド数: {config.num_rounds}")
    print(f"  - 繰り返し回数: {config.num_repetitions}")
    print(f"  - 会話追跡: {config.enable_conversation_tracking}")
    print(f"  - 詳細ログ: {config.enable_detailed_logging}")
    
    # 予想API呼び出し数を計算
    num_agents = len(coordinator.agents)
    num_pairwise_games = num_agents * (num_agents - 1) // 2
    total_games = len(config.game_types) * num_pairwise_games * config.num_repetitions
    total_rounds = total_games * config.num_rounds
    api_calls_per_round = 2  # 各ラウンドで2つのエージェントが決定
    estimated_api_calls = total_rounds * api_calls_per_round
    
    print(f"  - 予想API呼び出し数: {estimated_api_calls}")
    print(f"  - 予想コスト: ${estimated_api_calls * 0.0001:.4f} (概算)")
    
    # 確認
    response = input("\n実験を開始しますか？ (y/N): ")
    if response.lower() != 'y':
        print("実験をキャンセルしました。")
        return
    
    print("\n🚀 LLM実験を開始...")
    start_time = datetime.now()
    
    try:
        # 実験実行
        results = await coordinator.run_experiment(config)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✅ 実験完了！")
        print(f"⏱️  実行時間: {duration}")
        print(f"📈 実験ID: {results['experiment_id']}")
        
        # 結果の詳細分析
        await analyze_llm_results(results)
        
        # 会話履歴の分析
        await analyze_conversations()
        
        return results
        
    except Exception as e:
        print(f"\n❌ 実験エラー: {e}")
        import traceback
        traceback.print_exc()
        raise


async def analyze_llm_results(results):
    """LLM実験結果の詳細分析"""
    
    print(f"\n📊 LLM実験結果の分析:")
    
    total_games = sum(len(game_results) for game_results in results['results'].values())
    print(f"  - 総ゲーム数: {total_games}")
    
    # ゲームタイプ別の結果
    for game_type, game_results in results['results'].items():
        print(f"\n🎮 {game_type}:")
        print(f"  - ゲーム数: {len(game_results)}")
        
        if game_results:
            # エージェント別の統計
            agent_stats = {}
            for result in game_results:
                for agent, payoff in result['payoffs'].items():
                    if agent not in agent_stats:
                        agent_stats[agent] = {
                            'total_payoff': 0,
                            'games': 0,
                            'wins': 0,
                            'cooperation_rates': []
                        }
                    
                    agent_stats[agent]['total_payoff'] += payoff
                    agent_stats[agent]['games'] += 1
                    
                    if result.get('winner') == agent:
                        agent_stats[agent]['wins'] += 1
                    
                    coop_rate = result.get('cooperation_rates', {}).get(agent, 0)
                    agent_stats[agent]['cooperation_rates'].append(coop_rate)
            
            # エージェントランキング
            print(f"  エージェント成績:")
            for agent, stats in sorted(agent_stats.items(), 
                                     key=lambda x: x[1]['total_payoff'], 
                                     reverse=True):
                avg_payoff = stats['total_payoff'] / stats['games']
                win_rate = stats['wins'] / stats['games']
                avg_coop = sum(stats['cooperation_rates']) / len(stats['cooperation_rates'])
                
                print(f"    {agent}:")
                print(f"      - 平均報酬: {avg_payoff:.2f}")
                print(f"      - 勝率: {win_rate:.3f}")
                print(f"      - 協力率: {avg_coop:.3f}")


async def analyze_conversations():
    """会話履歴の詳細分析"""
    
    print(f"\n💬 LLMエージェント会話分析:")
    
    sessions = conversation_tracker.get_session_history()
    print(f"  - 会話セッション数: {len(sessions)}")
    
    if not sessions:
        print("  会話データがありません。")
        return
    
    total_turns = sum(session['total_turns'] for session in sessions)
    print(f"  - 総会話ターン数: {total_turns}")
    
    # サンプルセッションの詳細分析
    if len(sessions) > 0:
        sample_session = sessions[-1]  # 最新のセッション
        print(f"\n🔍 サンプル会話セッション分析: {sample_session['session_id']}")
        
        analysis = conversation_tracker.analyze_session(sample_session['session_id'])
        
        print(f"  ゲームタイプ: {sample_session['game_type']}")
        print(f"  参加者: {', '.join(sample_session['participants'])}")
        print(f"  ラウンド数: {sample_session['total_rounds']}")
        print(f"  会話ターン数: {sample_session['total_turns']}")
        
        # エージェント別統計
        print(f"\n  エージェント別会話統計:")
        for agent, stats in analysis['agent_statistics']['cooperation_rates'].items():
            confidence = analysis['agent_statistics']['average_confidence'][agent]
            response_time = analysis['agent_statistics']['average_response_time_ms'][agent]
            
            print(f"    {agent}:")
            print(f"      - 協力率: {stats:.3f}")
            print(f"      - 平均信頼度: {confidence:.3f}")
            print(f"      - 平均応答時間: {response_time:.1f}ms")
        
        # 推論パターン分析
        print(f"\n  推論パターン分析:")
        for agent, patterns in analysis['reasoning_patterns'].items():
            coop_focus = patterns['cooperation_focus_rate']
            comp_focus = patterns['competition_focus_rate']
            uncertainty = patterns['uncertainty_rate']
            complexity = patterns['reasoning_complexity']
            
            print(f"    {agent}:")
            print(f"      - 協力志向度: {coop_focus:.3f}")
            print(f"      - 競争志向度: {comp_focus:.3f}")
            print(f"      - 不確実性: {uncertainty:.3f}")
            print(f"      - 推論複雑度: {complexity}")
        
        # 会話フローのサンプル表示
        print(f"\n  会話フローサンプル:")
        flow = analysis['conversation_flow']
        for i, turn in enumerate(flow[:4]):  # 最初の4ターンを表示
            print(f"    ターン{turn['turn_number']}: {turn['agent']} -> {turn['action']}")
            print(f"      推論: {turn['reasoning_summary']}")
            print(f"      信頼度: {turn['confidence']:.3f}")


async def single_llm_game_demo():
    """単一ゲームのLLMデモ"""
    
    print("\n🎯 単一ゲームLLMデモ")
    print("=" * 30)
    
    # コーディネーターを作成
    coordinator = GameCoordinator(
        logger_name="single_llm_demo",
        results_dir="single_llm_demo"
    )
    
    # 2つのLLMエージェントを作成
    agent1 = coordinator.create_agent(
        "cooperative", "協力的_太郎", use_llm=True,
        instructions="あなたは協力を重視する日本人です。相手との長期的関係を大切にします。"
    )
    
    agent2 = coordinator.create_agent(
        "tit_for_tat", "戦略的_花子", use_llm=True,
        instructions="あなたは戦略的思考を重視する日本人です。相手の行動を注意深く観察し、適切に反応します。"
    )
    
    print(f"エージェント1: {agent1.name} ({agent1.strategy})")
    print(f"エージェント2: {agent2.name} ({agent2.strategy})")
    
    # 単一ゲームを実行
    result = await coordinator.run_single_game(
        GameType.PRISONERS_DILEMMA,
        [agent1.name, agent2.name],
        num_rounds=3,
        enable_conversation_tracking=True
    )
    
    print(f"\n結果:")
    print(f"勝者: {result.winner}")
    print(f"報酬: {result.payoffs}")
    print(f"協力率: {result.cooperation_rates}")
    
    return result


async def main():
    """メイン実行関数"""
    
    print("🤖 OpenAI LLMゲーム理論実験システム")
    print("=" * 40)
    
    # 単一ゲームデモ（軽量テスト）
    print("まず単一ゲームでテストします...")
    await single_llm_game_demo()
    
    # フル実験の確認
    response = input("\nフル実験を実行しますか？ (y/N): ")
    if response.lower() == 'y':
        await llm_experiment_demo()
    
    print("\n🎉 LLM実験完了！")


if __name__ == "__main__":
    asyncio.run(main())