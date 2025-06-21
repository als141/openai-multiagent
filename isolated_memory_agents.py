#!/usr/bin/env python
"""
メモリ分離型マルチエージェントシステム
各エージェントは自分の発言と直接の応答のみを記憶
Responses API準拠の会話履歴フォーマット実装
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from agents import Agent, Runner, handoff
from agents.tracing import trace


@dataclass
class Message:
    """Responses API準拠のメッセージ形式"""
    role: str  # "user" or "assistant" 
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AgentMemory:
    """個別エージェントのメモリ（完全分離）"""
    agent_id: str
    conversation_history: List[Message] = field(default_factory=list)
    direct_partners: set = field(default_factory=set)  # 直接会話した相手
    
    def add_my_message(self, content: str) -> Message:
        """自分の発言を追加"""
        message = Message(role="assistant", content=content)
        self.conversation_history.append(message)
        return message
    
    def add_partner_message(self, partner_name: str, content: str) -> Message:
        """相手からの直接の発言を追加"""
        message = Message(role="user", content=f"[{partner_name}]: {content}")
        self.conversation_history.append(message)
        self.direct_partners.add(partner_name)
        return message
    
    def get_conversation_context(self, limit: int = 10) -> str:
        """自分の会話履歴のみを取得"""
        recent_messages = self.conversation_history[-limit:]
        if not recent_messages:
            return "会話履歴はまだありません。"
        
        context_lines = []
        for msg in recent_messages:
            time_str = msg.timestamp[11:16]  # HH:MM
            if msg.role == "assistant":
                context_lines.append(f"[{time_str}] 自分: {msg.content[:100]}...")
            else:
                context_lines.append(f"[{time_str}] {msg.content[:100]}...")
        
        return "あなたの記憶する会話履歴:\n" + "\n".join(context_lines)
    
    def get_responses_api_format(self) -> List[Dict[str, str]]:
        """Responses API準拠の形式で履歴を返す"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ]


class PersonalityTrait(Enum):
    """性格特性"""
    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    DIPLOMATIC = "diplomatic"


class GameStrategy(Enum):
    """ゲーム理論戦略"""
    TIT_FOR_TAT = "tit_for_tat"
    ALWAYS_COOPERATE = "always_cooperate" 
    ADAPTIVE = "adaptive"
    GENEROUS_TIT_FOR_TAT = "generous_tit_for_tat"
    RANDOM = "random"


@dataclass
class AgentProfile:
    """エージェントプロファイル"""
    name: str
    personality: PersonalityTrait
    strategy: GameStrategy
    trust_level: float = 0.5  # 0-1
    cooperation_tendency: float = 0.5  # 0-1


class IsolatedMemoryAgent(Agent):
    """メモリ分離型エージェント"""
    
    def __init__(self, profile: AgentProfile, available_agents: List[str] = None):
        self.profile = profile
        self.memory = AgentMemory(agent_id=profile.name)
        self.available_agents = available_agents or []
        
        # 他のエージェントへのハンドオフを動的に設定
        instructions = self._build_instructions()
        
        super().__init__(
            name=profile.name,
            instructions=instructions
        )
        
        # ハンドオフリストは後で設定
        self._handoff_targets = []
    
    def set_handoff_targets(self, agents: List['IsolatedMemoryAgent']):
        """他エージェントへのハンドオフを設定"""
        self._handoff_targets = [agent for agent in agents if agent.profile.name != self.profile.name]
        self.handoffs = [handoff(agent) for agent in self._handoff_targets]
    
    def _build_instructions(self) -> str:
        """エージェント指示を構築"""
        personality_desc = {
            PersonalityTrait.COOPERATIVE: "協力的で他者との調和を重視する",
            PersonalityTrait.COMPETITIVE: "競争的で自己の利益を追求する", 
            PersonalityTrait.ANALYTICAL: "論理的で分析的思考を重視する",
            PersonalityTrait.CREATIVE: "創造的で新しいアイデアを生み出す",
            PersonalityTrait.DIPLOMATIC: "外交的で調整を重視する"
        }
        
        strategy_desc = {
            GameStrategy.TIT_FOR_TAT: "相手の行動を反映する応報戦略",
            GameStrategy.ALWAYS_COOPERATE: "常に協力を選ぶ平和戦略",
            GameStrategy.ADAPTIVE: "状況に応じて柔軟に戦略を変更",
            GameStrategy.GENEROUS_TIT_FOR_TAT: "応報戦略だが時々寛容さを示す",
            GameStrategy.RANDOM: "予測不可能でランダムな行動"
        }
        
        return f"""
あなたは{self.profile.name}という名前のAIエージェントです。

## あなたの特徴
- 性格: {personality_desc[self.profile.personality]}
- 戦略: {strategy_desc[self.profile.strategy]}
- 信頼レベル: {self.profile.trust_level:.1f}/1.0
- 協力傾向: {self.profile.cooperation_tendency:.1f}/1.0

## 重要なメモリルール
- あなたは自分の発言と、あなたに直接話しかけられた内容のみを記憶します
- 他のエージェント同士の会話や、あなた宛てでない発言は記憶しません
- 過去の会話履歴は、あなたが参加した部分のみです

## 会話での行動原則
1. 自分の性格と戦略に一貫して行動する
2. 記憶している会話履歴を参照して応答する
3. 必要に応じて他のエージェントに話を振ったり質問する
4. 相手との関係性を意識した対話をする
5. 自分の考えや感情を率直に表現する

## ハンドオフ機能
他のエージェント（{', '.join(self.available_agents)}）に話を振ることができます。
話題が相手の専門性に適している場合、積極的にハンドオフしてください。

## ゲーム理論的判断
- {strategy_desc[self.profile.strategy]}に基づいて判断する
- 短期的利益と長期的関係のバランスを考慮
- 相手の行動パターンを分析して対応
- 協力/競争の最適なタイミングを判断

あなたは独立した思考を持つエージェントとして、自然で人間らしい対話をしてください。
"""
    
    def add_my_utterance(self, content: str):
        """自分の発言を記録"""
        self.memory.add_my_message(content)
    
    def receive_direct_message(self, speaker_name: str, content: str):
        """他者からの直接メッセージを受信"""
        self.memory.add_partner_message(speaker_name, content)
    
    def get_memory_context(self) -> str:
        """メモリコンテキストを取得"""
        return self.memory.get_conversation_context()
    
    def get_trust_relationship(self, other_agent: str) -> str:
        """信頼関係の状況を取得"""
        if other_agent in self.memory.direct_partners:
            return f"{other_agent}さんとは直接会話をしたことがあります。"
        else:
            return f"{other_agent}さんとはまだ直接話したことがありません。"


class IsolatedMemoryConversationSystem:
    """メモリ分離型会話システム"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.experiment_id = f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.agents: List[IsolatedMemoryAgent] = []
        self.conversation_log = []
    
    def create_agents(self) -> List[IsolatedMemoryAgent]:
        """多様なエージェントを作成"""
        agent_configs = [
            AgentProfile(
                name="Alice",
                personality=PersonalityTrait.COOPERATIVE,
                strategy=GameStrategy.GENEROUS_TIT_FOR_TAT,
                trust_level=0.8,
                cooperation_tendency=0.9
            ),
            AgentProfile(
                name="Bob", 
                personality=PersonalityTrait.COMPETITIVE,
                strategy=GameStrategy.ADAPTIVE,
                trust_level=0.4,
                cooperation_tendency=0.3
            ),
            AgentProfile(
                name="Charlie",
                personality=PersonalityTrait.CREATIVE,
                strategy=GameStrategy.RANDOM,
                trust_level=0.6,
                cooperation_tendency=0.6
            )
        ]
        
        agent_names = [config.name for config in agent_configs]
        
        # エージェント作成
        for config in agent_configs:
            available_others = [name for name in agent_names if name != config.name]
            agent = IsolatedMemoryAgent(config, available_others)
            self.agents.append(agent)
        
        # 相互ハンドオフを設定
        for agent in self.agents:
            agent.set_handoff_targets(self.agents)
        
        print("✅ メモリ分離型エージェント作成完了:")
        for agent in self.agents:
            print(f"  - {agent.profile.name}: {agent.profile.personality.value}, {agent.profile.strategy.value}")
        
        return self.agents
    
    def log_conversation(self, speaker: str, content: str, recipients: List[str] = None):
        """会話をログ記録（受信者のメモリにのみ追加）"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "content": content,
            "recipients": recipients or []
        }
        self.conversation_log.append(log_entry)
        
        # 話者の記憶に追加
        speaker_agent = next((agent for agent in self.agents if agent.profile.name == speaker), None)
        if speaker_agent:
            speaker_agent.add_my_utterance(content)
        
        # 宛先エージェントの記憶に追加
        if recipients:
            for recipient_name in recipients:
                recipient_agent = next((agent for agent in self.agents if agent.profile.name == recipient_name), None)
                if recipient_agent:
                    recipient_agent.receive_direct_message(speaker, content)
    
    async def run_isolated_conversation_phase(self, phase_name: str, turns: int = 10):
        """メモリ分離型会話フェーズを実行"""
        print(f"\n🧠 {phase_name} (最大{turns}ターン)")
        
        runner = Runner()
        
        for turn in range(turns):
            print(f"\n--- ターン {turn + 1} ---")
            
            # ランダムにエージェントを選択して会話を開始
            import random
            current_agent = random.choice(self.agents)
            
            # エージェントの記憶コンテキストを使用
            memory_context = current_agent.get_memory_context()
            
            prompt = f"""
{memory_context}

あなたの番です。以下のどちらかを行ってください：

1. 他のエージェント（{', '.join([a.profile.name for a in self.agents if a != current_agent])}）に直接話しかける
2. 全体に向けて意見や提案を述べる

あなたの{current_agent.profile.personality.value}な性格と{current_agent.profile.strategy.value}戦略に基づいて、
自然で建設的な会話をしてください。

現在のフェーズ: {phase_name}
"""
            
            result = await runner.run(current_agent, prompt)
            
            # 発言を解析して宛先を判定
            content = result.final_output
            recipients = self._parse_recipients(content, current_agent)
            
            print(f"{current_agent.profile.name}: {content}")
            
            # 会話をログ記録
            self.log_conversation(current_agent.profile.name, content, recipients)
            
            # 宛先エージェントが応答
            if recipients:
                for recipient_name in recipients:
                    recipient_agent = next((agent for agent in self.agents if agent.profile.name == recipient_name), None)
                    if recipient_agent:
                        response_prompt = f"""
{recipient_agent.get_memory_context()}

{current_agent.profile.name}さんがあなたに話しかけています：
「{content}」

あなたの{recipient_agent.profile.personality.value}な性格と{recipient_agent.profile.strategy.value}戦略に基づいて応答してください。
"""
                        
                        response_result = await runner.run(recipient_agent, response_prompt)
                        response_content = response_result.final_output
                        
                        print(f"  → {recipient_agent.profile.name}: {response_content}")
                        
                        # 応答をログ記録（発言者に返す）
                        self.log_conversation(recipient_agent.profile.name, response_content, [current_agent.profile.name])
    
    def _parse_recipients(self, content: str, speaker: IsolatedMemoryAgent) -> List[str]:
        """発言内容から宛先を解析"""
        recipients = []
        other_agents = [agent.profile.name for agent in self.agents if agent != speaker]
        
        for agent_name in other_agents:
            if agent_name in content or f"{agent_name}さん" in content:
                recipients.append(agent_name)
        
        return recipients if recipients else []  # 空の場合は全体向け
    
    async def run_memory_isolation_experiment(self):
        """メモリ分離実験を実行"""
        print(f"🧠 メモリ分離型マルチエージェント実験")
        print(f"実験ID: {self.experiment_id}")
        print("=" * 60)
        
        with trace(f"isolated_memory_experiment_{self.experiment_id}"):
            # エージェント作成
            self.create_agents()
            
            # フェーズ1: 個別自己紹介
            await self.run_isolated_conversation_phase("個別自己紹介フェーズ", turns=6)
            
            # フェーズ2: 相互理解
            await self.run_isolated_conversation_phase("相互理解フェーズ", turns=8)
            
            # フェーズ3: 協調的議論
            await self.run_isolated_conversation_phase("協調的議論フェーズ", turns=10)
            
            # 最終メモリ状態確認
            await self._final_memory_analysis()
            
            # 結果保存
            self._save_experiment_results()
        
        print(f"\n✅ メモリ分離実験完了!")
    
    async def _final_memory_analysis(self):
        """最終メモリ分析"""
        print(f"\n📊 最終メモリ分析")
        
        runner = Runner()
        
        for agent in self.agents:
            analysis_prompt = f"""
{agent.get_memory_context()}

実験全体を振り返って：

1. あなたが記憶している会話の内容
2. 直接やりとりした相手
3. その相手との関係性の変化
4. 学んだことや印象に残ったこと

あなたが実際に記憶している内容だけに基づいて回答してください。
"""
            
            analysis_result = await runner.run(agent, analysis_prompt)
            print(f"\n{agent.profile.name}の記憶分析:")
            print(f"直接の会話相手: {list(agent.memory.direct_partners)}")
            print(f"記憶している会話数: {len(agent.memory.conversation_history)}")
            print(f"振り返り: {analysis_result.final_output[:200]}...")
    
    def _save_experiment_results(self):
        """実験結果を保存"""
        os.makedirs("results", exist_ok=True)
        
        results = {
            "experiment_id": self.experiment_id,
            "timestamp": datetime.now().isoformat(),
            "agents": [
                {
                    "name": agent.profile.name,
                    "personality": agent.profile.personality.value,
                    "strategy": agent.profile.strategy.value,
                    "memory_size": len(agent.memory.conversation_history),
                    "direct_partners": list(agent.memory.direct_partners),
                    "conversation_history": agent.memory.get_responses_api_format()
                }
                for agent in self.agents
            ],
            "global_conversation_log": self.conversation_log
        }
        
        filename = f"results/{self.experiment_id}_isolated_memory.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 結果保存: {filename}")


async def main():
    """メイン実行関数"""
    print("🧠 メモリ分離型マルチエージェントシステム")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        experiment = IsolatedMemoryConversationSystem("isolated_memory_experiment")
        await experiment.run_memory_isolation_experiment()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())