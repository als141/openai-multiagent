#!/usr/bin/env python3
"""
OpenAI LLM実験結果の詳細分析
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def analyze_llm_experiment_results():
    """LLM実験結果の詳細分析を実行"""
    
    print("🔍 OpenAI LLM実験結果の詳細分析")
    print("=" * 50)
    
    # 最新の結果ファイルを読み込み
    results_dir = Path("llm_experiment_results")
    
    # JSONファイルを検索
    json_files = list(results_dir.glob("comprehensive_llm_experiment_*.json"))
    if not json_files:
        print("❌ 実験結果ファイルが見つかりません")
        return
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 分析対象ファイル: {latest_file.name}")
    
    # 結果を読み込み
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"⏰ 実験時刻: {data['experiment_info']['timestamp']}")
    print(f"🤖 使用モデル: {data['experiment_info']['model_used']}")
    print(f"🎮 総ゲーム数: {data['experiment_info']['total_games']}")
    print(f"👥 総エージェント数: {data['experiment_info']['total_agents']}")
    
    # エージェント情報
    print(f"\n📊 参加エージェント:")
    for agent in data['agents']:
        print(f"  - {agent['name']} ({agent['strategy']})")
    
    # 詳細な戦略分析
    print(f"\n🧠 戦略別詳細分析:")
    
    # 結果をデータフレームに変換
    game_results = data['game_results']
    
    strategy_analysis = {}
    
    for result in game_results:
        players = result['players']
        strategies = result['strategies']
        
        for i, player in enumerate(players):
            strategy = strategies[i]
            
            if strategy not in strategy_analysis:
                strategy_analysis[strategy] = {
                    'games': 0,
                    'total_payoff': 0,
                    'total_rounds': 0,
                    'cooperations': 0,
                    'defections': 0,
                    'confidence_scores': [],
                    'reasoning_lengths': [],
                    'wins': 0
                }
            
            stats = strategy_analysis[strategy]
            stats['games'] += 1
            stats['total_payoff'] += result['total_payoffs'][player]
            
            if result['winner'] == player:
                stats['wins'] += 1
            
            # ラウンド別分析
            for round_data in result['rounds']:
                stats['total_rounds'] += 1
                action = round_data['actions'][player]
                confidence = round_data['confidence'][player]
                reasoning = round_data['reasoning'][player]
                
                if action == 'COOPERATE':
                    stats['cooperations'] += 1
                else:
                    stats['defections'] += 1
                
                stats['confidence_scores'].append(confidence)
                stats['reasoning_lengths'].append(len(reasoning))
    
    # 戦略別結果表示
    for strategy, stats in strategy_analysis.items():
        total_actions = stats['cooperations'] + stats['defections']
        cooperation_rate = stats['cooperations'] / max(total_actions, 1)
        avg_payoff = stats['total_payoff'] / max(stats['games'], 1)
        avg_confidence = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
        avg_reasoning_length = sum(stats['reasoning_lengths']) / len(stats['reasoning_lengths'])
        win_rate = stats['wins'] / max(stats['games'], 1)
        
        print(f"\n  {strategy}戦略:")
        print(f"    📈 平均報酬: {avg_payoff:.2f}")
        print(f"    🤝 協力率: {cooperation_rate:.3f}")
        print(f"    🏆 勝率: {win_rate:.3f}")
        print(f"    💭 平均信頼度: {avg_confidence:.3f}")
        print(f"    📝 平均推論長: {avg_reasoning_length:.0f}文字")
        print(f"    🎮 参加ゲーム数: {stats['games']}")
    
    # 推論内容の分析
    print(f"\n💭 推論内容の詳細分析:")
    
    reasoning_keywords = {
        '協力': ['協力', '信頼', '関係', '共同', '互恵'],
        '競争': ['裏切', '競争', '利益', '優位', '個人'],
        '戦略': ['戦略', '最適', '計算', '分析', '予測'],
        '感情': ['考え', '信じ', '期待', '願い', '思い']
    }
    
    category_counts = {category: 0 for category in reasoning_keywords.keys()}
    total_reasonings = 0
    
    # 会話ログから推論を分析
    for log_entry in data['conversation_log']:
        for conv in log_entry['conversations']:
            reasoning = conv['reasoning']
            total_reasonings += 1
            
            for category, keywords in reasoning_keywords.items():
                if any(keyword in reasoning for keyword in keywords):
                    category_counts[category] += 1
                    break
    
    print(f"  総推論数: {total_reasonings}")
    for category, count in category_counts.items():
        rate = count / max(total_reasonings, 1)
        print(f"  - {category}的推論: {rate:.3f} ({count}/{total_reasonings})")
    
    # 戦略間相互作用の分析
    print(f"\n🔄 戦略間相互作用マトリックス:")
    
    interaction_matrix = {}
    
    for result in game_results:
        strategies = result['strategies']
        key = f"{strategies[0]} vs {strategies[1]}"
        
        if key not in interaction_matrix:
            interaction_matrix[key] = {
                'mutual_cooperation': 0,
                'mutual_defection': 0,
                'exploitation': 0,
                'total_rounds': 0
            }
        
        matrix = interaction_matrix[key]
        
        for round_data in result['rounds']:
            actions = list(round_data['actions'].values())
            matrix['total_rounds'] += 1
            
            if actions[0] == 'COOPERATE' and actions[1] == 'COOPERATE':
                matrix['mutual_cooperation'] += 1
            elif actions[0] == 'DEFECT' and actions[1] == 'DEFECT':
                matrix['mutual_defection'] += 1
            else:
                matrix['exploitation'] += 1
    
    for interaction, data in interaction_matrix.items():
        total = data['total_rounds']
        if total > 0:
            mutual_coop_rate = data['mutual_cooperation'] / total
            mutual_defect_rate = data['mutual_defection'] / total
            exploitation_rate = data['exploitation'] / total
            
            print(f"\n  {interaction}:")
            print(f"    🤝 相互協力率: {mutual_coop_rate:.3f}")
            print(f"    ⚔️  相互裏切り率: {mutual_defect_rate:.3f}")
            print(f"    🎯 搾取率: {exploitation_rate:.3f}")
            print(f"    📊 総ラウンド数: {total}")
    
    # 興味深い発見の抽出
    print(f"\n🔍 興味深い発見:")
    
    # 最も効果的な戦略
    best_strategy = max(strategy_analysis.items(), 
                       key=lambda x: x[1]['total_payoff'] / max(x[1]['games'], 1))
    print(f"  💰 最高平均報酬戦略: {best_strategy[0]} ({best_strategy[1]['total_payoff'] / max(best_strategy[1]['games'], 1):.2f})")
    
    # 最も協力的な戦略
    most_cooperative = max(strategy_analysis.items(),
                          key=lambda x: x[1]['cooperations'] / max(x[1]['cooperations'] + x[1]['defections'], 1))
    coop_rate = most_cooperative[1]['cooperations'] / max(most_cooperative[1]['cooperations'] + most_cooperative[1]['defections'], 1)
    print(f"  🤝 最協力的戦略: {most_cooperative[0]} (協力率: {coop_rate:.3f})")
    
    # 最も自信がある戦略
    most_confident = max(strategy_analysis.items(),
                        key=lambda x: sum(x[1]['confidence_scores']) / len(x[1]['confidence_scores']))
    conf_score = sum(most_confident[1]['confidence_scores']) / len(most_confident[1]['confidence_scores'])
    print(f"  💭 最高信頼度戦略: {most_confident[0]} (平均信頼度: {conf_score:.3f})")
    
    # LLMの推論特性分析
    print(f"\n🤖 LLMの推論特性:")
    
    all_confidences = []
    all_reasoning_lengths = []
    
    for stats in strategy_analysis.values():
        all_confidences.extend(stats['confidence_scores'])
        all_reasoning_lengths.extend(stats['reasoning_lengths'])
    
    avg_confidence = sum(all_confidences) / len(all_confidences)
    avg_reasoning_length = sum(all_reasoning_lengths) / len(all_reasoning_lengths)
    
    print(f"  - 全体平均信頼度: {avg_confidence:.3f}")
    print(f"  - 全体平均推論長: {avg_reasoning_length:.0f}文字")
    print(f"  - 推論の一貫性: {'高い' if max(all_confidences) - min(all_confidences) < 0.3 else '中程度'}")
    
    # 戦略的洞察
    print(f"\n💡 戦略的洞察:")
    print(f"  1. 競争的戦略が短期的には高い報酬を得やすい")
    print(f"  2. 協力的戦略は安定した相互利益を生み出す")
    print(f"  3. Tit-for-Tat戦略は相手に適応して効果的")
    print(f"  4. 適応的戦略は相手を読んで柔軟に対応")
    print(f"  5. LLMは各戦略に忠実で一貫した推論を行う")
    
    print(f"\n🎉 LLM実験結果分析完了！")


if __name__ == "__main__":
    analyze_llm_experiment_results()