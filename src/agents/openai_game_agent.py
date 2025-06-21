"""OpenAI Agents SDK を使用したゲーム理論エージェントの実装"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from agents import Agent, Runner, RunConfig
from agents.types import GenerationInOut
from agents.tools import handoff
from agents.tracing import trace

from ..game_theory.strategies import Strategy, Action
from ..game_theory.games import GameType
from ..knowledge.exchange import KnowledgeItem


@dataclass
class AgentMemory:
    """エージェントの記憶を管理"""
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    trust_scores: Dict[str, float] = field(default_factory=dict)
    knowledge_base: List[KnowledgeItem] = field(default_factory=list)
    payoff_history: List[float] = field(default_factory=list)


class GameTheoryAgent(Agent):
    """ゲーム理論的な意思決定を行うエージェント"""
    
    def __init__(
        self,
        name: str,
        strategy: Strategy,
        personality: str,
        trust_threshold: float = 0.5,
        handoffs: Optional[List[Agent]] = None,
        tools: Optional[List[Callable]] = None
    ):
        # エージェントの指示を生成
        instructions = self._generate_instructions(personality, strategy)
        
        super().__init__(
            name=name,
            instructions=instructions,
            handoffs=handoffs or [],
            tools=tools or []
        )
        
        self.strategy = strategy
        self.personality = personality
        self.trust_threshold = trust_threshold
        self.memory = AgentMemory()
        self._decision_callback = None
    
    def _generate_instructions(self, personality: str, strategy: Strategy) -> str:
        """エージェントの性格と戦略に基づいた指示を生成"""
        base_instructions = f"""
あなたは{personality}な性格を持つエージェントです。
ゲーム理論的な相互作用において、{strategy.value}戦略を基本としています。

あなたの目標：
1. 他のエージェントとの相互作用を通じて、集団全体の利益を最大化する
2. 自身の利得も考慮しながら、協調的な問題解決を図る
3. 信頼関係を構築し、知識を適切に共有する

意思決定の基準：
- 相手の過去の行動履歴を考慮する
- 信頼スコアに基づいて協力/非協力を判断する
- 長期的な関係構築を重視する

知識共有の原則：
- 信頼できる相手とは積極的に知識を共有する
- 重要な知識は戦略的に活用する
- 集団の問題解決能力向上に貢献する
"""
        
        # 戦略ごとの特別な指示
        strategy_instructions = {
            Strategy.COOPERATIVE: "常に協力を優先し、相手を信頼する姿勢を示す。",
            Strategy.COMPETITIVE: "自己の利益を最大化しつつ、必要に応じて協力する。",
            Strategy.TIT_FOR_TAT: "相手の前回の行動を真似て、協力には協力で、裏切りには裏切りで応じる。",
            Strategy.ADAPTIVE: "状況に応じて柔軟に戦略を変更し、最適な結果を追求する。",
            Strategy.RANDOM: "予測不可能な行動を取り、相手を混乱させることがある。"
        }
        
        if strategy in strategy_instructions:
            base_instructions += f"\n\n特別な戦略指示：\n{strategy_instructions[strategy]}"
        
        return base_instructions
    
    async def make_decision(self, game_type: GameType, opponent: str, context: Dict[str, Any]) -> Action:
        """ゲーム理論的な意思決定を行う"""
        with trace(name=f"{self.name}_decision", tags={"game_type": game_type.value}):
            # 相手の信頼スコアを取得
            trust_score = self.memory.trust_scores.get(opponent, 0.5)
            
            # 過去の相互作用履歴を参照
            relevant_history = [
                h for h in self.memory.interaction_history
                if h.get("opponent") == opponent
            ]
            
            # プロンプトを構築
            prompt = f"""
現在のゲーム: {game_type.value}
対戦相手: {opponent}
信頼スコア: {trust_score:.2f}
過去の相互作用: {len(relevant_history)}回

相手の最近の行動パターン:
{self._analyze_recent_behavior(opponent, relevant_history)}

現在の状況:
{json.dumps(context, ensure_ascii=False, indent=2)}

あなたはどのような行動を取りますか？
選択肢: COOPERATE（協力）または DEFECT（裏切り）

理由も含めて回答してください。
"""
            
            # エージェントに意思決定させる
            runner = Runner()
            result = await runner.run(self, prompt, config=RunConfig(
                max_token_count=200,
                save_sensitive_data=False
            ))
            
            # 結果から行動を抽出
            decision_text = result.final_output.lower()
            action = Action.COOPERATE if "cooperate" in decision_text else Action.DEFECT
            
            # 決定を記録
            self._record_decision(game_type, opponent, action, context)
            
            # コールバックがあれば実行
            if self._decision_callback:
                self._decision_callback(self.name, opponent, action, decision_text)
            
            return action
    
    def _analyze_recent_behavior(self, opponent: str, history: List[Dict[str, Any]]) -> str:
        """相手の最近の行動パターンを分析"""
        if not history:
            return "初めての対戦です。"
        
        recent_actions = history[-5:]  # 最近5回の行動
        cooperate_count = sum(1 for h in recent_actions if h.get("opponent_action") == Action.COOPERATE)
        defect_count = len(recent_actions) - cooperate_count
        
        pattern = f"最近{len(recent_actions)}回中、協力{cooperate_count}回、裏切り{defect_count}回"
        
        if cooperate_count > defect_count * 2:
            pattern += " (協力的な傾向)"
        elif defect_count > cooperate_count * 2:
            pattern += " (競争的な傾向)"
        else:
            pattern += " (バランス型)"
        
        return pattern
    
    def _record_decision(self, game_type: GameType, opponent: str, action: Action, context: Dict[str, Any]):
        """意思決定を記録"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "game_type": game_type.value,
            "opponent": opponent,
            "my_action": action,
            "context": context
        }
        self.memory.interaction_history.append(record)
    
    def update_trust(self, opponent: str, their_action: Action, my_action: Action):
        """相手の行動に基づいて信頼スコアを更新"""
        current_trust = self.memory.trust_scores.get(opponent, 0.5)
        
        # 信頼スコアの更新ロジック
        if my_action == Action.COOPERATE and their_action == Action.COOPERATE:
            # 両者協力：信頼上昇
            new_trust = min(1.0, current_trust + 0.1)
        elif my_action == Action.COOPERATE and their_action == Action.DEFECT:
            # 自分が協力、相手が裏切り：信頼大幅低下
            new_trust = max(0.0, current_trust - 0.2)
        elif my_action == Action.DEFECT and their_action == Action.COOPERATE:
            # 自分が裏切り、相手が協力：信頼やや上昇（相手の寛容さを評価）
            new_trust = min(1.0, current_trust + 0.05)
        else:
            # 両者裏切り：信頼やや低下
            new_trust = max(0.0, current_trust - 0.05)
        
        self.memory.trust_scores[opponent] = new_trust
    
    def add_knowledge(self, knowledge: KnowledgeItem):
        """知識ベースに新しい知識を追加"""
        self.memory.knowledge_base.append(knowledge)
    
    def share_knowledge(self, recipient: str) -> Optional[KnowledgeItem]:
        """信頼できる相手と知識を共有"""
        trust_score = self.memory.trust_scores.get(recipient, 0.5)
        
        if trust_score >= self.trust_threshold and self.memory.knowledge_base:
            # 信頼できる相手には価値の高い知識を共有
            valuable_knowledge = sorted(
                self.memory.knowledge_base,
                key=lambda k: k.value,
                reverse=True
            )
            return valuable_knowledge[0] if valuable_knowledge else None
        
        return None
    
    def set_decision_callback(self, callback: Callable):
        """意思決定時のコールバックを設定"""
        self._decision_callback = callback


class CoordinatorAgent(Agent):
    """複数のエージェントを調整する特別なエージェント"""
    
    def __init__(
        self,
        name: str = "Coordinator",
        managed_agents: Optional[List[GameTheoryAgent]] = None
    ):
        instructions = """
あなたは複数のエージェントを調整するコーディネーターです。

主な役割：
1. エージェント間の対話を促進する
2. 問題解決のための協力体制を構築する
3. 知識共有を仲介する
4. 集団の意思決定をまとめる
5. 創発的な解決策を導き出す

調整の原則：
- 各エージェントの個性と戦略を尊重する
- 公平で透明な調整を行う
- 集団全体の利益を最大化する
- 対立を建設的な議論に変える
"""
        
        # 管理するエージェントへのハンドオフを設定
        handoffs = [handoff(agent) for agent in (managed_agents or [])]
        
        super().__init__(
            name=name,
            instructions=instructions,
            handoffs=handoffs
        )
        
        self.managed_agents = managed_agents or []
    
    async def facilitate_discussion(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """エージェント間の議論を促進"""
        with trace(name="facilitate_discussion", tags={"topic": topic}):
            prompt = f"""
議題: {topic}

現在の状況:
{json.dumps(context, ensure_ascii=False, indent=2)}

管理しているエージェント:
{[agent.name for agent in self.managed_agents]}

各エージェントの意見を収集し、建設的な議論を促進してください。
異なる視点を統合し、創発的な解決策を見つけることが目標です。
"""
            
            runner = Runner()
            result = await runner.run(self, prompt, config=RunConfig(
                max_token_count=1000,
                save_sensitive_data=False
            ))
            
            return {
                "facilitator": self.name,
                "topic": topic,
                "discussion": result.final_output,
                "timestamp": datetime.now().isoformat()
            }
    
    def aggregate_decisions(self, decisions: Dict[str, Action]) -> Action:
        """複数のエージェントの決定を集約"""
        cooperate_count = sum(1 for action in decisions.values() if action == Action.COOPERATE)
        total_count = len(decisions)
        
        # 多数決で決定（同数の場合は協力を選択）
        return Action.COOPERATE if cooperate_count >= total_count / 2 else Action.DEFECT


def create_agent_with_handoffs(
    agents: List[GameTheoryAgent],
    allow_self_handoff: bool = False
) -> List[GameTheoryAgent]:
    """エージェント間のハンドオフを設定"""
    for i, agent in enumerate(agents):
        # 他のエージェントへのハンドオフを設定
        other_agents = [a for j, a in enumerate(agents) if allow_self_handoff or i != j]
        agent.handoffs = [handoff(other) for other in other_agents]
    
    return agents