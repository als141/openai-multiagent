"""
OpenAI LLMを使用した実際のゲーム理論エージェント
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

from .base_agent import BaseGameAgent
from .types import AgentAction, GameDecision

# 環境変数を読み込み
load_dotenv()


class LLMGameAgent(BaseGameAgent):
    """OpenAI LLMを使用するゲーム理論エージェント"""
    
    def __init__(
        self,
        name: str,
        strategy: str,
        model: str = "gpt-4o-mini",
        instructions: Optional[str] = None,
        cooperation_threshold: float = 0.5,
        trust_threshold: float = 0.5,
        **kwargs
    ):
        """LLMエージェントを初期化
        
        Args:
            name: エージェント名
            strategy: 戦略タイプ
            model: 使用するOpenAIモデル
            instructions: カスタム指示
            cooperation_threshold: 協力判定閾値
            trust_threshold: 信頼判定閾値
        """
        self.model = model
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 親クラスを初期化（OpenAI Agentsは使わず、独自実装）
        self.name = name
        self.strategy = strategy
        self.cooperation_threshold = cooperation_threshold
        self.trust_threshold = trust_threshold
        
        # AgentStateを初期化
        from .base_agent import AgentState
        self.state = AgentState()
        
        # ロガーを設定
        from ..utils.logger import get_logger
        self.logger = get_logger(f"llm_agent.{name}")
        
        # 指示を構築
        self.instructions = instructions or self._build_llm_instructions()
        
        self.logger.info(f"LLMエージェント '{name}' を初期化: 戦略={strategy}, モデル={model}")
    
    def _build_llm_instructions(self) -> str:
        """LLM用の詳細な指示を構築"""
        
        base_instructions = f"""
あなたは'{self.name}'という名前のゲーム理論エージェントです。あなたの戦略は'{self.strategy}'です。

## あなたの役割
多エージェント環境でゲーム理論的相互作用を行い、戦略的意思決定をします。

## あなたの特性
- 名前: {self.name}
- 戦略: {self.strategy}
- 協力閾値: {self.cooperation_threshold}
- 信頼閾値: {self.trust_threshold}

## 意思決定プロセス
1. ゲーム状況と相手の履歴を分析
2. 自分の戦略に基づいて最適な行動を選択
3. 信頼度と将来の期待価値を考慮
4. 明確な推論過程を提供
5. 知識共有の可否を判断

## 利用可能な行動
- COOPERATE: 協力する
- DEFECT: 裏切る
- SHARE_KNOWLEDGE: 知識を共有する
- WITHHOLD_KNOWLEDGE: 知識を秘匿する

## 応答形式
JSON形式で以下の構造で回答してください：
{{
    "action": "COOPERATE|DEFECT|SHARE_KNOWLEDGE|WITHHOLD_KNOWLEDGE",
    "reasoning": "詳細な推論過程を日本語で説明",
    "confidence": 0.0-1.0の信頼度,
    "knowledge_to_share": ["共有する知識のリスト"] または null
}}
"""
        
        # 戦略別の詳細指示
        strategy_specific = {
            "tit_for_tat": """
## Tit-for-Tat戦略の指示
- 初回は必ず協力から始める
- 相手の前回の行動をそのまま真似する
- 相手が協力したら協力、裏切ったら裏切る
- 長期的な関係構築を重視する
""",
            "always_cooperate": """
## 常に協力戦略の指示
- 常に協力的な行動を選択する
- 知識共有を積極的に行う
- 相手の行動に関係なく協力を続ける
- 集団の利益を個人の利益より優先する
""",
            "always_defect": """
## 常に裏切り戦略の指示
- 常に競争的・利己的な行動を選択する
- 知識の共有は最小限に留める
- 個人の利益を最大化することを優先する
- 相手の協力を利用して自分の利益を得る
""",
            "adaptive": """
## 適応戦略の指示
- 相手の行動パターンを学習・分析する
- 過去の結果に基づいて戦略を調整する
- 環境の変化に応じて柔軟に対応する
- 最適な協力レベルを動的に判断する
""",
            "random": """
## ランダム戦略の指示
- ランダムに行動を選択する（ただし合理的な理由を提供）
- 予測不可能性を維持する
- 時々驚くような行動を取る
- それでも基本的な論理性は保つ
"""
        }
        
        specific_instruction = strategy_specific.get(self.strategy, "")
        
        return base_instructions + "\n" + specific_instruction
    
    async def make_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """LLMを使用して意思決定を行う"""
        
        try:
            # プロンプトを構築
            prompt = self._build_decision_prompt(game_context, opponent_history)
            
            # OpenAI APIを呼び出し
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.instructions},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # 適度な創造性
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # 応答を解析
            content = response.choices[0].message.content
            self.logger.debug(f"LLM応答: {content}")
            
            decision_data = json.loads(content)
            
            # GameDecisionオブジェクトを作成
            action_str = decision_data.get("action", "DEFECT")
            try:
                action = AgentAction(action_str)
            except ValueError:
                self.logger.warning(f"無効な行動 '{action_str}'、DEFECTにフォールバック")
                action = AgentAction.DEFECT
            
            decision = GameDecision(
                action=action,
                reasoning=decision_data.get("reasoning", "LLM推論が取得できませんでした"),
                confidence=float(decision_data.get("confidence", 0.5)),
                knowledge_to_share=decision_data.get("knowledge_to_share")
            )
            
            self.logger.info(
                f"意思決定完了: {action.value} "
                f"(信頼度: {decision.confidence:.3f})"
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(f"LLM意思決定でエラー: {e}")
            # フォールバック決定
            return self._fallback_decision(game_context, opponent_history)
    
    def _build_decision_prompt(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> str:
        """意思決定用のプロンプトを構築"""
        
        prompt_parts = []
        
        # ゲーム情報
        prompt_parts.append("## 現在のゲーム状況")
        prompt_parts.append(f"ゲームタイプ: {game_context.get('game_type', '不明')}")
        prompt_parts.append(f"ラウンド番号: {game_context.get('round_number', 1)}")
        
        if 'opponent_id' in game_context:
            opponent_id = game_context['opponent_id']
            prompt_parts.append(f"対戦相手: {opponent_id}")
            
            # 相手への信頼度
            trust_score = self.get_trust_score(opponent_id)
            prompt_parts.append(f"相手への信頼度: {trust_score:.3f}")
        
        # 報酬マトリックス情報
        if 'reward_matrix' in game_context:
            prompt_parts.append("\n## 報酬マトリックス")
            matrix = game_context['reward_matrix']
            if hasattr(matrix, '__dict__'):
                prompt_parts.append(f"協力-協力: {getattr(matrix, 'cooperate_cooperate', 'N/A')}")
                prompt_parts.append(f"協力-裏切り: {getattr(matrix, 'cooperate_defect', 'N/A')}")
                prompt_parts.append(f"裏切り-協力: {getattr(matrix, 'defect_cooperate', 'N/A')}")
                prompt_parts.append(f"裏切り-裏切り: {getattr(matrix, 'defect_defect', 'N/A')}")
        
        # 相手の行動履歴
        if opponent_history:
            prompt_parts.append("\n## 相手の行動履歴")
            prompt_parts.append(f"総インタラクション数: {len(opponent_history)}")
            
            # 協力率を計算
            cooperative_actions = sum(
                1 for action in opponent_history
                if action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]
            )
            cooperation_rate = cooperative_actions / len(opponent_history)
            prompt_parts.append(f"相手の協力率: {cooperation_rate:.3f}")
            
            # 最近の行動
            recent_actions = opponent_history[-5:]
            recent_str = " → ".join([action.value for action in recent_actions])
            prompt_parts.append(f"最近の行動: {recent_str}")
        else:
            prompt_parts.append("\n## 相手の行動履歴")
            prompt_parts.append("初回のインタラクション（履歴なし）")
        
        # 自分の状態
        prompt_parts.append("\n## あなたの現在の状態")
        prompt_parts.append(f"評判スコア: {self.state.reputation:.3f}")
        prompt_parts.append(f"知識ベースサイズ: {len(self.state.knowledge_base)}")
        
        if self.state.payoff_history:
            avg_payoff = sum(self.state.payoff_history) / len(self.state.payoff_history)
            prompt_parts.append(f"平均報酬: {avg_payoff:.3f}")
        
        # 全体的な協力率
        overall_coop_rate = self.get_cooperation_rate()
        prompt_parts.append(f"あなたの全体協力率: {overall_coop_rate:.3f}")
        
        # 戦略的考慮事項
        prompt_parts.append("\n## 戦略的考慮事項")
        prompt_parts.append("以下を考慮して最適な行動を選択してください：")
        prompt_parts.append("1. あなたの基本戦略との整合性")
        prompt_parts.append("2. 相手の行動パターンと信頼性")
        prompt_parts.append("3. 短期的利益と長期的関係のバランス")
        prompt_parts.append("4. 知識共有による相互利益の可能性")
        
        # その他のゲーム固有情報
        if game_context.get('game_type') == 'public_goods':
            prompt_parts.append(f"\n公共財ゲーム固有情報:")
            prompt_parts.append(f"- 初期資金: {game_context.get('endowment', 'N/A')}")
            prompt_parts.append(f"- 乗数: {game_context.get('multiplier', 'N/A')}")
            prompt_parts.append(f"- プレイヤー数: {game_context.get('num_players', 'N/A')}")
        
        elif game_context.get('game_type') == 'knowledge_sharing':
            prompt_parts.append(f"\n知識共有ゲーム固有情報:")
            prompt_parts.append(f"- 知識価値: {game_context.get('knowledge_value', 'N/A')}")
            prompt_parts.append(f"- 共有コスト: {game_context.get('sharing_cost', 'N/A')}")
        
        prompt_parts.append("\n上記の情報を基に、JSON形式で最適な決定を行ってください。")
        
        return "\n".join(prompt_parts)
    
    def _fallback_decision(
        self,
        game_context: Dict[str, Any],
        opponent_history: Optional[List[AgentAction]] = None
    ) -> GameDecision:
        """LLMが失敗した場合のフォールバック決定"""
        
        # 戦略に基づく簡単なルール
        if self.strategy == "always_cooperate":
            action = AgentAction.COOPERATE
            reasoning = "LLMエラー時のフォールバック: 常に協力戦略"
        elif self.strategy == "always_defect":
            action = AgentAction.DEFECT
            reasoning = "LLMエラー時のフォールバック: 常に裏切り戦略"
        elif self.strategy == "tit_for_tat":
            if opponent_history and len(opponent_history) > 0:
                last_action = opponent_history[-1]
                if last_action in [AgentAction.COOPERATE, AgentAction.SHARE_KNOWLEDGE]:
                    action = AgentAction.COOPERATE
                else:
                    action = AgentAction.DEFECT
                reasoning = f"LLMエラー時のフォールバック: Tit-for-Tat（相手の前回行動: {last_action.value}）"
            else:
                action = AgentAction.COOPERATE
                reasoning = "LLMエラー時のフォールバック: Tit-for-Tat初回は協力"
        else:
            # デフォルト
            action = AgentAction.COOPERATE if self.cooperation_threshold > 0.5 else AgentAction.DEFECT
            reasoning = f"LLMエラー時のフォールバック: 協力閾値{self.cooperation_threshold}に基づく決定"
        
        return GameDecision(
            action=action,
            reasoning=reasoning,
            confidence=0.3  # フォールバック時は低い信頼度
        )


class LLMAgentFactory:
    """LLMエージェントのファクトリークラス"""
    
    @staticmethod
    def create_cooperative_agent(name: str, **kwargs) -> LLMGameAgent:
        """協力的エージェントを作成"""
        return LLMGameAgent(
            name=name,
            strategy="always_cooperate",
            cooperation_threshold=0.8,
            trust_threshold=0.6,
            **kwargs
        )
    
    @staticmethod
    def create_competitive_agent(name: str, **kwargs) -> LLMGameAgent:
        """競争的エージェントを作成"""
        return LLMGameAgent(
            name=name,
            strategy="always_defect",
            cooperation_threshold=0.2,
            trust_threshold=0.4,
            **kwargs
        )
    
    @staticmethod
    def create_tit_for_tat_agent(name: str, **kwargs) -> LLMGameAgent:
        """Tit-for-Tatエージェントを作成"""
        return LLMGameAgent(
            name=name,
            strategy="tit_for_tat",
            cooperation_threshold=0.5,
            trust_threshold=0.5,
            **kwargs
        )
    
    @staticmethod
    def create_adaptive_agent(name: str, **kwargs) -> LLMGameAgent:
        """適応的エージェントを作成"""
        return LLMGameAgent(
            name=name,
            strategy="adaptive",
            cooperation_threshold=0.6,
            trust_threshold=0.5,
            **kwargs
        )
    
    @staticmethod
    def create_random_agent(name: str, **kwargs) -> LLMGameAgent:
        """ランダムエージェントを作成"""
        return LLMGameAgent(
            name=name,
            strategy="random",
            cooperation_threshold=0.5,
            trust_threshold=0.5,
            **kwargs
        )