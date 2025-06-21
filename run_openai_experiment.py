#!/usr/bin/env python
"""OpenAI Agents SDKを使用したマルチエージェント実験の実行スクリプト"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.experiments.openai_multi_agent_experiment import MultiAgentExperiment
from src.agents.openai_game_agent import GameTheoryAgent, CoordinatorAgent
from src.game_theory.strategies import Strategy
from src.game_theory.games import GameType


async def run_quick_demo():
    """簡単なデモを実行"""
    print("🚀 OpenAI Agents SDK デモを開始")
    
    # 2エージェントでの簡単な実験
    agents = [
        GameTheoryAgent("Alice", Strategy.COOPERATIVE, "協力的で優しい"),
        GameTheoryAgent("Bob", Strategy.TIT_FOR_TAT, "公平を重視する")
    ]
    
    experiment = MultiAgentExperiment("quick_demo")
    
    # 囚人のジレンマを5ラウンド実行
    await experiment.run_game_theory_interaction(agents, GameType.PRISONERS_DILEMMA, rounds=5)
    
    # 知識共有セッション
    coordinator = CoordinatorAgent(managed_agents=agents)
    await experiment.run_knowledge_sharing_session(
        agents, coordinator,
        "効率的なチームワークの構築方法"
    )
    
    experiment._save_results()
    print("✅ デモ完了")


async def run_custom_experiment(
    agent_count: int,
    game_rounds: int,
    problems: List[str]
):
    """カスタム実験を実行"""
    print(f"🔧 カスタム実験を開始 (エージェント数: {agent_count})")
    
    # 指定された数のエージェントを作成
    strategies = [Strategy.COOPERATIVE, Strategy.COMPETITIVE, Strategy.TIT_FOR_TAT, 
                 Strategy.ADAPTIVE, Strategy.RANDOM]
    agents = []
    
    for i in range(agent_count):
        strategy = strategies[i % len(strategies)]
        personality = ["協力的", "競争的", "公平", "柔軟", "創造的"][i % 5]
        agent = GameTheoryAgent(
            name=f"Agent_{i+1}",
            strategy=strategy,
            personality=f"{personality}な性格を持つ"
        )
        agents.append(agent)
    
    experiment = MultiAgentExperiment("custom_experiment")
    
    # ゲーム理論的相互作用
    for game_type in [GameType.PRISONERS_DILEMMA, GameType.PUBLIC_GOODS]:
        await experiment.run_game_theory_interaction(agents, game_type, rounds=game_rounds)
    
    # 問題解決
    coordinator = CoordinatorAgent(managed_agents=agents)
    for problem in problems:
        await experiment.run_complex_problem_solving(agents, coordinator, problem)
    
    experiment._analyze_final_trust_network(agents)
    experiment._save_results()
    print("✅ カスタム実験完了")


async def run_benchmark_experiment():
    """ベンチマーク実験を実行"""
    print("📊 ベンチマーク実験を開始")
    
    experiment = MultiAgentExperiment("benchmark_experiment")
    
    # 標準的なエージェントセットを作成
    agents = experiment.create_diverse_agents()
    coordinator = CoordinatorAgent(managed_agents=agents)
    
    # ベンチマーク問題
    benchmark_problems = [
        # 多角的視点が必要な問題
        "都市の交通渋滞を解決しながら環境負荷を最小化する総合的な交通システムの設計",
        
        # 利害対立の調整が必要な問題  
        "限られた水資源を農業、工業、生活用水に公平かつ効率的に配分する方法",
        
        # 創造的解決が必要な問題
        "高齢化社会における世代間の知識継承と技術革新を両立させるシステム",
        
        # 倫理的判断が必要な問題
        "個人のプライバシーと公共の安全のバランスを取るAI監視システムの設計",
        
        # グローバルな協調が必要な問題
        "国際的な炭素排出権取引と発展途上国の経済成長を両立させる枠組み"
    ]
    
    # 各ゲームタイプで実験
    for game_type in GameType:
        await experiment.run_game_theory_interaction(agents, game_type, rounds=20)
    
    # 知識共有セッション
    knowledge_topics = [
        "分散型意思決定システムの最適化",
        "競争と協力のバランス戦略",
        "創発的イノベーションの促進方法"
    ]
    
    for topic in knowledge_topics:
        await experiment.run_knowledge_sharing_session(agents, coordinator, topic)
    
    # ベンチマーク問題を解決
    for problem in benchmark_problems:
        result = await experiment.run_complex_problem_solving(agents, coordinator, problem)
        
        # 単一エージェントでも同じ問題を解かせて比較
        single_agent = agents[0]  # 代表として1エージェント
        prompt = f"問題: {problem}\n\nこの問題に対する解決策を提案してください。"
        
        from agents import Runner, RunConfig
        runner = Runner()
        single_result = await runner.run(single_agent, prompt, config=RunConfig(
            max_token_count=500,
            save_sensitive_data=False
        ))
        
        print(f"\n  単一エージェント vs マルチエージェント:")
        print(f"  創発性スコア: {result['evaluation']['emergence_score']:.2f}")
        print(f"  単一解の長さ: {len(single_result.final_output)}")
        print(f"  統合解の長さ: {len(result['emergent_solution'])}")
    
    experiment._save_results()
    print("✅ ベンチマーク実験完了")


def main():
    """メインエントリーポイント"""
    # 環境変数を読み込み
    load_dotenv()
    
    # OpenAI APIキーの確認
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        print("  .env ファイルに OPENAI_API_KEY=sk-... を設定してください")
        return
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='OpenAI Agents SDK マルチエージェント実験')
    
    subparsers = parser.add_subparsers(dest='mode', help='実行モード')
    
    # デモモード
    demo_parser = subparsers.add_parser('demo', help='簡単なデモを実行')
    
    # フル実験モード
    full_parser = subparsers.add_parser('full', help='完全な実験を実行')
    full_parser.add_argument('--name', type=str, default='創発的問題解決実験',
                            help='実験名')
    
    # カスタム実験モード
    custom_parser = subparsers.add_parser('custom', help='カスタム実験を実行')
    custom_parser.add_argument('--agents', type=int, default=3,
                              help='エージェント数')
    custom_parser.add_argument('--rounds', type=int, default=10,
                              help='ゲームラウンド数')
    custom_parser.add_argument('--problems', nargs='+',
                              default=["持続可能な社会の実現"],
                              help='解決する問題のリスト')
    
    # ベンチマークモード
    bench_parser = subparsers.add_parser('benchmark', help='ベンチマーク実験を実行')
    
    args = parser.parse_args()
    
    # 実行
    try:
        if args.mode == 'demo':
            asyncio.run(run_quick_demo())
        elif args.mode == 'full':
            experiment = MultiAgentExperiment(args.name)
            asyncio.run(experiment.run_full_experiment())
        elif args.mode == 'custom':
            asyncio.run(run_custom_experiment(
                args.agents, args.rounds, args.problems
            ))
        elif args.mode == 'benchmark':
            asyncio.run(run_benchmark_experiment())
        else:
            # デフォルトはフル実験
            experiment = MultiAgentExperiment("創発的問題解決実験")
            asyncio.run(experiment.run_full_experiment())
            
    except KeyboardInterrupt:
        print("\n⚠️ 実験が中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()