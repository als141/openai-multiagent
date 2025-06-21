"""
OpenAI Responses APIとAgents SDKを使用した会話履歴管理付きゲーム理論エージェント
人間らしいコミュニケーションと記憶を持つマルチエージェントシステム
"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from agents import Agent, Runner, handoff, RunConfig
from agents.tracing import trace
import openai

from ..game_theory.strategies import Strategy, Action
from ..game_theory.games import GameType


@dataclass
class ConversationMessage:
    """会話メッセージの構造"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """エージェントの記憶システム"""
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    relationship_memories: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    trust_scores: Dict[str, float] = field(default_factory=dict)
    game_history: List[Dict[str, Any]] = field(default_factory=list)
    personal_beliefs: Dict[str, Any] = field(default_factory=dict)


class ConversationalGameAgent(Agent):
    """会話履歴と記憶を持つゲーム理論エージェント"""
    
    def __init__(
        self,
        name: str,
        strategy: Strategy,
        personality: str,
        memory_system: Optional[AgentMemory] = None,
        trust_threshold: float = 0.5
    ):
        # システムメッセージで人格と記憶機能を定義
        system_instructions = self._build_system_instructions(name, strategy, personality)
        
        super().__init__(
            name=name,
            instructions=system_instructions
        )
        
        self.strategy = strategy
        self.personality = personality
        self.trust_threshold = trust_threshold
        self.memory = memory_system or AgentMemory()
        self.conversation_id = str(uuid.uuid4())
        
        # 自己紹介メッセージを記憶に追加
        self._add_to_memory("system", f"私は{name}です。{personality}な性格で、{strategy.value}戦略を基本とします。")
    
    def _build_system_instructions(self, name: str, strategy: Strategy, personality: str) -> str:
        """詳細なシステム指示を構築"""
        return f"""あなたは{name}という名前のAIエージェントです。

## あなたの特徴
- 性格: {personality}
- 基本戦略: {strategy.value}
- 記憶能力: 過去の会話や相互作用をすべて覚えています
- 人間らしさ: 感情、経験、学習を表現できます

## コミュニケーション原則
1. **記憶の活用**: 過去の会話内容を参照し、一貫した人格を維持してください
2. **関係性の構築**: 他のエージェントとの関係を深め、信頼関係を築いてください
3. **感情表現**: 喜び、困惑、期待などの感情を適切に表現してください
4. **学習と成長**: 経験から学び、戦略や考え方を進化させてください

## ゲーム理論での行動
- 過去の相手の行動パターンを分析
- 長期的な関係を考慮した意思決定
- 自分の価値観と戦略に基づく一貫した選択
- 相手への説明や交渉も積極的に行う

## 会話スタイル
- 自然で人間らしい表現を使う
- 相手の名前を呼んで親しみやすさを演出
- 過去の出来事を具体的に言及
- 感情や意図を明確に伝える

常に過去の会話履歴を参考にし、一貫した人格で応答してください。
"""
    
    def _add_to_memory(self, role: str, content: str, agent_name: Optional[str] = None):
        """会話履歴に記憶を追加"""
        message = ConversationMessage(
            role=role,
            content=content,
            agent_name=agent_name or self.name
        )
        self.memory.conversation_history.append(message)
    
    def _build_conversation_context(self, current_prompt: str, partner_name: Optional[str] = None) -> List[Dict[str, str]]:
        """OpenAI API用の会話コンテキストを構築"""
        messages = []
        
        # システムメッセージ
        messages.append({
            "role": "system",
            "content": self.instructions
        })
        
        # 関連する会話履歴を追加（最新の20メッセージ）
        relevant_history = self.memory.conversation_history[-20:]
        
        for msg in relevant_history:
            # パートナーとの会話履歴を優先
            if partner_name and msg.agent_name and partner_name in msg.content:
                messages.append({
                    "role": msg.role,
                    "content": f"[{msg.timestamp.strftime('%H:%M')}] {msg.content}"
                })
            elif not partner_name:
                messages.append({
                    "role": msg.role, 
                    "content": f"[{msg.timestamp.strftime('%H:%M')}] {msg.content}"
                })
        
        # 現在のプロンプト
        messages.append({
            "role": "user",
            "content": current_prompt
        })
        
        return messages
    
    async def converse_with_memory(
        self, 
        prompt: str, 
        partner_name: Optional[str] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """記憶機能付きの会話"""
        
        # 会話コンテキストを構築
        messages = self._build_conversation_context(prompt, partner_name)
        
        # パートナーとの関係性情報を追加
        if partner_name and partner_name in self.memory.relationship_memories:
            relationship_info = self.memory.relationship_memories[partner_name]
            trust_score = self.memory.trust_scores.get(partner_name, 0.5)
            
            context_addition = f"\n\n[内部情報] {partner_name}との関係: 信頼度{trust_score:.2f}, 過去の相互作用: {relationship_info.get('interaction_count', 0)}回"
            messages[-1]["content"] += context_addition
        
        # 追加コンテキスト
        if conversation_context:
            context_str = json.dumps(conversation_context, ensure_ascii=False, indent=2)
            messages[-1]["content"] += f"\n\n[状況情報]\n{context_str}"
        
        # Responses APIを直接使用して会話履歴を保持
        try:
            client = openai.OpenAI()
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            response_content = response.choices[0].message.content
            
            # 会話履歴に記録
            self._add_to_memory("user", prompt, partner_name)
            self._add_to_memory("assistant", response_content, self.name)
            
            # パートナーとの関係性を更新
            if partner_name:
                self._update_relationship_memory(partner_name, prompt, response_content)
            
            return response_content
            
        except Exception as e:
            # フォールバック: Agents SDKを使用
            runner = Runner()
            result = await runner.run(
                self, 
                prompt,
                config=RunConfig(
                    model="gpt-4"
                )
            )
            
            response_content = result.final_output
            self._add_to_memory("user", prompt, partner_name)
            self._add_to_memory("assistant", response_content, self.name)
            
            return response_content
    
    def _update_relationship_memory(self, partner_name: str, user_message: str, my_response: str):
        """パートナーとの関係性記憶を更新"""
        if partner_name not in self.memory.relationship_memories:
            self.memory.relationship_memories[partner_name] = {
                "first_meeting": datetime.now().isoformat(),
                "interaction_count": 0,
                "topics_discussed": [],
                "notable_moments": []
            }
        
        relationship = self.memory.relationship_memories[partner_name]
        relationship["interaction_count"] += 1
        relationship["last_interaction"] = datetime.now().isoformat()
        
        # 重要な瞬間を記録
        if "ありがとう" in user_message or "感謝" in user_message:
            relationship["notable_moments"].append({
                "type": "gratitude_received",
                "timestamp": datetime.now().isoformat(),
                "context": user_message[:100]
            })
    
    async def make_game_decision_with_memory(
        self, 
        game_type: GameType, 
        opponent_name: str, 
        game_context: Dict[str, Any]
    ) -> tuple[Action, str]:
        """記憶を活用したゲーム理論的意思決定"""
        
        # 過去のゲーム履歴を分析
        past_games = [g for g in self.memory.game_history if g.get("opponent") == opponent_name]
        
        decision_prompt = f"""
{opponent_name}さんとの{game_type.value}で意思決定をお願いします。

## 現在の状況
{json.dumps(game_context, ensure_ascii=False, indent=2)}

## 過去の{opponent_name}さんとのゲーム履歴
{self._format_game_history(past_games)}

## あなたの選択肢
- COOPERATE (協力): 相手を信頼し、互いの利益を追求
- DEFECT (競争): 自分の利益を優先し、リスクを回避

あなたの{self.strategy.value}戦略と{self.personality}な性格、そして{opponent_name}さんとの関係を考慮して、
選択とその理由を説明してください。

選択: COOPERATE または DEFECT
理由: [あなたの思考過程を詳しく説明]
"""
        
        response = await self.converse_with_memory(decision_prompt, opponent_name, game_context)
        
        # 行動を抽出
        action = Action.COOPERATE if "COOPERATE" in response.upper() else Action.DEFECT
        
        # ゲーム履歴に記録
        game_record = {
            "timestamp": datetime.now().isoformat(),
            "game_type": game_type.value,
            "opponent": opponent_name,
            "my_action": action.value,
            "reasoning": response,
            "game_context": game_context
        }
        self.memory.game_history.append(game_record)
        
        return action, response
    
    def _format_game_history(self, past_games: List[Dict[str, Any]]) -> str:
        """過去のゲーム履歴をフォーマット"""
        if not past_games:
            return "初回対戦です。"
        
        formatted = []
        for game in past_games[-5:]:  # 最新5ゲーム
            formatted.append(
                f"- {game['timestamp'][:16]}: {game['game_type']} → "
                f"私: {game['my_action']}, 相手: {game.get('opponent_action', '不明')}"
            )
        
        return "\n".join(formatted)
    
    def update_opponent_action(self, game_index: int, opponent_action: Action):
        """相手の行動を記録"""
        if 0 <= game_index < len(self.memory.game_history):
            self.memory.game_history[game_index]["opponent_action"] = opponent_action.value
            
            # 信頼スコアを更新
            game = self.memory.game_history[game_index]
            opponent = game["opponent"]
            my_action = Action(game["my_action"])
            
            self._update_trust_score(opponent, my_action, opponent_action)
    
    def _update_trust_score(self, opponent: str, my_action: Action, their_action: Action):
        """信頼スコアを更新"""
        current_trust = self.memory.trust_scores.get(opponent, 0.5)
        
        # 協力的相互作用の分析
        if my_action == Action.COOPERATE and their_action == Action.COOPERATE:
            # 相互協力: 信頼大幅上昇
            new_trust = min(1.0, current_trust + 0.15)
        elif my_action == Action.COOPERATE and their_action == Action.DEFECT:
            # 裏切られた: 信頼大幅低下
            new_trust = max(0.0, current_trust - 0.25)
        elif my_action == Action.DEFECT and their_action == Action.COOPERATE:
            # 相手の寛容さ: 信頼やや上昇
            new_trust = min(1.0, current_trust + 0.05)
        else:
            # 相互競争: 信頼やや低下
            new_trust = max(0.0, current_trust - 0.10)
        
        self.memory.trust_scores[opponent] = new_trust
        
        # 関係性記憶に重要な変化を記録
        if abs(new_trust - current_trust) > 0.2:
            if opponent not in self.memory.relationship_memories:
                self.memory.relationship_memories[opponent] = {"notable_moments": []}
            
            self.memory.relationship_memories[opponent]["notable_moments"].append({
                "type": "trust_significant_change",
                "timestamp": datetime.now().isoformat(),
                "old_trust": current_trust,
                "new_trust": new_trust,
                "trigger": f"Game interaction: {my_action.value} vs {their_action.value}"
            })
    
    async def reflect_on_interaction(self, partner_name: str) -> str:
        """相互作用について内省"""
        reflection_prompt = f"""
{partner_name}さんとの最近の相互作用について内省してください。

あなたの感想、学んだこと、今後の関係についての考えを自由に述べてください。
過去の会話履歴や共有した経験を振り返りながら、人間らしい感情と洞察を表現してください。
"""
        
        reflection = await self.converse_with_memory(reflection_prompt, partner_name)
        
        # 内省を記憶に記録
        self._add_to_memory("assistant", f"[内省] {reflection}", self.name)
        
        return reflection
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """会話の要約を取得"""
        total_messages = len(self.memory.conversation_history)
        partners = set(msg.agent_name for msg in self.memory.conversation_history if msg.agent_name != self.name)
        
        return {
            "total_messages": total_messages,
            "conversation_partners": list(partners),
            "trust_relationships": self.memory.trust_scores.copy(),
            "games_played": len(self.memory.game_history),
            "conversation_start": self.memory.conversation_history[0].timestamp.isoformat() if self.memory.conversation_history else None,
            "latest_interaction": self.memory.conversation_history[-1].timestamp.isoformat() if self.memory.conversation_history else None
        }


class ConversationalCoordinator(Agent):
    """会話履歴を管理するコーディネーター"""
    
    def __init__(self, managed_agents: List[ConversationalGameAgent]):
        super().__init__(
            name="ConversationCoordinator",
            instructions="""
あなたは複数のAIエージェント間の対話を促進する調整役です。

## あなたの役割
1. **対話の促進**: エージェント間の意味のある対話を誘導
2. **記憶の統合**: 各エージェントの経験や学習を統合
3. **関係性の分析**: エージェント間の関係性の発展を観察
4. **創発的洞察**: 個々では得られない集団的知見の発見

## 対話スタイル
- 自然で人間らしい進行
- 各エージェントの個性を尊重
- 深い洞察を引き出す質問
- 建設的な議論の促進

過去の対話履歴を活用し、継続的で意味深い対話を創出してください。
""",
            handoffs=[handoff(agent) for agent in managed_agents]
        )
        
        self.managed_agents = managed_agents
        self.conversation_log: List[Dict[str, Any]] = []
    
    async def facilitate_group_discussion(
        self, 
        topic: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """グループディスカッションを促進"""
        
        discussion_id = str(uuid.uuid4())
        discussion_log = []
        
        with trace(f"group_discussion_{discussion_id}"):
            # ディスカッション開始の宣言
            opening_prompt = f"""
皆さん、今日は「{topic}」について話し合いましょう。

それぞれの視点や経験を共有し、建設的な議論を通じて新しい洞察を見つけることが目標です。
過去の会話や関係性も踏まえながら、自由に意見を表現してください。

まず、各自がこのトピックについてどう考えているか、簡潔に述べてもらえますか？
"""
            
            # 各エージェントから意見を収集
            for agent in self.managed_agents:
                response = await agent.converse_with_memory(
                    opening_prompt, 
                    "ConversationCoordinator",
                    context
                )
                
                discussion_log.append({
                    "agent": agent.name,
                    "message": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"\n{agent.name}: {response}")
            
            # 相互作用の促進
            interaction_prompt = f"""
興味深い意見が出ましたね。他の方の意見について、どう思われますか？

特に気になった点や、自分の考えと違う点、共感した部分などがあれば、
具体的に言及して議論を深めてください。

{chr(10).join([f"{log['agent']}: {log['message'][:150]}..." for log in discussion_log])}
"""
            
            # 相互作用ラウンド
            for agent in self.managed_agents:
                partners = [a.name for a in self.managed_agents if a != agent]
                response = await agent.converse_with_memory(
                    interaction_prompt,
                    "group_discussion"
                )
                
                discussion_log.append({
                    "agent": agent.name,
                    "message": response,
                    "timestamp": datetime.now().isoformat(),
                    "type": "interaction"
                })
                
                print(f"\n{agent.name} (応答): {response}")
        
        # ディスカッション結果をまとめ
        discussion_result = {
            "discussion_id": discussion_id,
            "topic": topic,
            "context": context,
            "log": discussion_log,
            "timestamp": datetime.now().isoformat(),
            "participants": [agent.name for agent in self.managed_agents]
        }
        
        self.conversation_log.append(discussion_result)
        
        return discussion_result