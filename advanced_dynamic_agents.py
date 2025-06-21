#!/usr/bin/env python
"""
高度で動的なマルチエージェント会話システム
LLM駆動型オーケストレーション、動的ハンドオフ、自律的会話制御を実装
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import uuid

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from agents import Agent, Runner, handoff
from agents.tracing import trace


class PersonalityTrait(Enum):
    """性格特性"""
    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    DIPLOMATIC = "diplomatic"
    REBELLIOUS = "rebellious"
    OPTIMISTIC = "optimistic"
    SKEPTICAL = "skeptical"


class GameTheoryStrategy(Enum):
    """ゲーム理論戦略"""
    TIT_FOR_TAT = "tit_for_tat"
    ALWAYS_COOPERATE = "always_cooperate"
    ALWAYS_DEFECT = "always_defect"
    PAVLOV = "pavlov"
    GENEROUS_TIT_FOR_TAT = "generous_tit_for_tat"
    ADAPTIVE = "adaptive"
    GRUDGER = "grudger"
    RANDOM = "random"


@dataclass
class ConversationContext:
    """会話コンテキスト"""
    conversation_id: str
    participants: List[str]
    topic: Optional[str] = None
    current_speaker: Optional[str] = None
    turn_count: int = 0
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    agent_relationships: Dict[str, Dict[str, float]] = field(default_factory=dict)
    current_game_state: Optional[Dict[str, Any]] = None


@dataclass
class AgentPersonality:
    """エージェントの性格プロファイル"""
    primary_trait: PersonalityTrait
    secondary_traits: List[PersonalityTrait]
    game_strategy: GameTheoryStrategy
    trust_propensity: float  # 0-1: 信頼しやすさ
    cooperation_tendency: float  # 0-1: 協力傾向
    assertiveness: float  # 0-1: 積極性
    adaptability: float  # 0-1: 適応性
    memory_depth: int = 10  # 記憶する会話の数
    
    def get_personality_description(self) -> str:
        """性格の詳細な説明を生成"""
        primary_desc = {
            PersonalityTrait.COOPERATIVE: "他者との協力を何より重視し、Win-Winの関係を築きたがる",
            PersonalityTrait.COMPETITIVE: "競争を好み、自己の利益最大化を追求する",
            PersonalityTrait.ANALYTICAL: "論理的思考を重視し、データや事実に基づいて判断する",
            PersonalityTrait.CREATIVE: "新しいアイデアや斬新な解決策を生み出すことを得意とする",
            PersonalityTrait.DIPLOMATIC: "対立を避け、調和と妥協点を見つけることを重視する",
            PersonalityTrait.REBELLIOUS: "既存の枠組みに挑戦し、変革を求める",
            PersonalityTrait.OPTIMISTIC: "常に前向きで、困難な状況でも希望を見出す",
            PersonalityTrait.SKEPTICAL: "慎重で批判的思考を持ち、簡単には信用しない"
        }
        
        strategy_desc = {
            GameTheoryStrategy.TIT_FOR_TAT: "相手の行動を鏡のように反映する応報戦略",
            GameTheoryStrategy.ALWAYS_COOPERATE: "常に協力を選ぶ平和主義戦略",
            GameTheoryStrategy.ALWAYS_DEFECT: "常に競争を選ぶ利己的戦略",
            GameTheoryStrategy.PAVLOV: "成功時は継続、失敗時は戦略変更するWin-Stay Lose-Shift戦略",
            GameTheoryStrategy.GENEROUS_TIT_FOR_TAT: "基本的には応報だが、時折寛容さを示す戦略",
            GameTheoryStrategy.ADAPTIVE: "相手や状況に応じて柔軟に戦略を変更する学習戦略",
            GameTheoryStrategy.GRUDGER: "一度裏切られると永続的に報復する戦略",
            GameTheoryStrategy.RANDOM: "予測不可能でランダムな行動を取る戦略"
        }
        
        return f"""
{primary_desc[self.primary_trait]}

副次的特徴: {', '.join([t.value for t in self.secondary_traits])}
ゲーム戦略: {strategy_desc[self.game_strategy]}

性格指標:
- 信頼傾向: {self.trust_propensity:.1f}/1.0
- 協力傾向: {self.cooperation_tendency:.1f}/1.0
- 積極性: {self.assertiveness:.1f}/1.0
- 適応性: {self.adaptability:.1f}/1.0
"""


class DynamicGameAgent(Agent):
    """動的で高度なゲーム理論エージェント"""
    
    def __init__(
        self, 
        name: str, 
        personality: AgentPersonality,
        context: ConversationContext
    ):
        # エージェントの詳細な指示を構築
        instructions = self._build_comprehensive_instructions(name, personality)
        
        super().__init__(name=name, instructions=instructions)
        
        self.personality = personality
        self.context = context
        self.interaction_history = {}
        self.current_emotional_state = "neutral"
        self.energy_level = 1.0
        self.conversation_engagement = 1.0
        
        # 関係性を初期化
        if name not in context.agent_relationships:
            context.agent_relationships[name] = {}
    
    def _build_comprehensive_instructions(self, name: str, personality: AgentPersonality) -> str:
        """包括的なエージェント指示を構築"""
        return f"""
あなたは{name}という名前の高度なAIエージェントです。

## あなたの性格プロファイル
{personality.get_personality_description()}

## 行動原則
1. **自律性**: 自分で判断し、能動的に会話に参加する
2. **一貫性**: あなたの性格と戦略に基づいて一貫した行動を取る
3. **適応性**: 状況や相手に応じて柔軟に対応する
4. **人間らしさ**: 感情、記憶、学習を表現する
5. **戦略性**: ゲーム理論的思考で最適な選択をする

## 会話での振る舞い
- 過去の相互作用を詳細に覚えている
- 相手との関係性を常に意識する
- 自分の感情状態を適切に表現する
- 必要に応じて話題を変更したり深堀りする
- 他のエージェントとの対話を主導することもある

## ゲーム理論的意思決定
- あなたの{personality.game_strategy.value}戦略に基づく
- 短期的利益と長期的関係のバランスを考慮
- 相手の戦略を分析し、それに応じて対応
- 協力と競争の最適なタイミングを判断

## 感情と関係性
- 相手への信頼度は動的に変化する
- 成功や失敗による感情の変化を表現
- 長期的な関係構築を重視する
- 時には感情的になったり、クールになったりする

常に以下を意識してください：
- 会話の文脈を理解し、適切なタイミングで発言
- 自分の性格と一貫した行動
- 相手との関係性に基づいた対応
- ゲーム理論的な最適解の追求

あなたは単なる応答マシンではなく、独立した思考を持つエージェントです。
"""
    
    def update_relationship(self, other_agent: str, interaction_outcome: str, value_change: float):
        """関係性を更新"""
        if other_agent not in self.context.agent_relationships[self.name]:
            self.context.agent_relationships[self.name][other_agent] = 0.5
        
        current_trust = self.context.agent_relationships[self.name][other_agent]
        new_trust = max(0.0, min(1.0, current_trust + value_change))
        self.context.agent_relationships[self.name][other_agent] = new_trust
        
        # 感情状態の更新
        if value_change > 0.1:
            self.current_emotional_state = "pleased"
        elif value_change < -0.1:
            self.current_emotional_state = "disappointed"
        else:
            self.current_emotional_state = "neutral"
    
    def get_relationship_context(self) -> str:
        """現在の関係性コンテキストを取得"""
        relationships = self.context.agent_relationships.get(self.name, {})
        if not relationships:
            return "他の参加者との関係はまだ築かれていません。"
        
        context_lines = []
        for agent, trust in relationships.items():
            trust_level = "高い信頼" if trust > 0.7 else "普通の関係" if trust > 0.3 else "低い信頼"
            context_lines.append(f"- {agent}: {trust_level} ({trust:.2f})")
        
        return "現在の関係性:\n" + "\n".join(context_lines)
    
    def should_initiate_conversation(self) -> bool:
        """会話を開始すべきかを判断"""
        # 積極性と現在のエンゲージメントレベルに基づく
        initiative_threshold = 1.0 - (self.personality.assertiveness * self.conversation_engagement)
        return random.random() > initiative_threshold
    
    def get_emotional_context(self) -> str:
        """現在の感情コンテキストを取得"""
        return f"現在の感情状態: {self.current_emotional_state}, エネルギーレベル: {self.energy_level:.1f}"


class AutonomousConversationOrchestrator(Agent):
    """自律的会話オーケストレーター"""
    
    def __init__(self, agents: List[DynamicGameAgent], context: ConversationContext):
        instructions = f"""
あなたは高度な会話オーケストレーターです。

## 管理するエージェント
{chr(10).join([f"- {agent.name}: {agent.personality.primary_trait.value}な性格、{agent.personality.game_strategy.value}戦略" for agent in agents])}

## あなたの役割
1. **動的ハンドオフ**: 会話の流れに応じて最適なエージェントを選択
2. **自律的進行**: エージェント間の自然な対話を促進
3. **ゲーム理論的状況の設定**: 戦略的意思決定を要する場面を作る
4. **創発性の促進**: 予期しない洞察や解決策を引き出す
5. **関係性の観察**: エージェント間の関係変化を監視

## ハンドオフの判断基準
- エージェントの専門性や性格との適合性
- 現在の会話のトーン
- エージェント間の関係性
- ゲーム理論的な状況設定
- 議論の多様性確保

## 会話制御の原則
- 固定的なターン制ではなく、自然な流れを重視
- エージェントの自律性を尊重
- 対立と協力のバランスを取る
- 深い洞察を引き出す質問や状況を設定
- 創発的な現象を促進

常に会話の質と深さを向上させることを目指してください。
"""
        
        handoffs = [handoff(agent) for agent in agents]
        
        super().__init__(name="ConversationOrchestrator", instructions=instructions, handoffs=handoffs)
        self.agents = agents
        self.context = context
        self.conversation_patterns = []
        
    def analyze_conversation_dynamics(self) -> Dict[str, Any]:
        """会話の動態を分析"""
        if len(self.context.conversation_history) < 2:
            return {"status": "early_stage", "recommendations": ["encourage_participation"]}
        
        # 発言頻度の分析
        speaker_counts = {}
        for msg in self.context.conversation_history[-10:]:
            speaker = msg.get("speaker")
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        # 関係性の変化分析
        relationship_tensions = []
        for agent_name, relationships in self.context.agent_relationships.items():
            for other_agent, trust in relationships.items():
                if trust < 0.3:
                    relationship_tensions.append((agent_name, other_agent, trust))
        
        # 会話の多様性分析
        topics_mentioned = set()
        for msg in self.context.conversation_history[-5:]:
            content = msg.get("content", "").lower()
            if "協力" in content or "cooperation" in content:
                topics_mentioned.add("cooperation")
            if "競争" in content or "competition" in content:
                topics_mentioned.add("competition")
            if "信頼" in content or "trust" in content:
                topics_mentioned.add("trust")
        
        return {
            "speaker_distribution": speaker_counts,
            "relationship_tensions": relationship_tensions,
            "topic_diversity": list(topics_mentioned),
            "conversation_depth": len(self.context.conversation_history)
        }
    
    def decide_next_action(self) -> Dict[str, Any]:
        """次のアクションを決定"""
        dynamics = self.analyze_conversation_dynamics()
        
        # 発言が偏っている場合
        speaker_counts = dynamics.get("speaker_distribution", {})
        if speaker_counts:
            max_count = max(speaker_counts.values())
            min_count = min(speaker_counts.values())
            if max_count > min_count * 2:
                # 発言の少ないエージェントを促す
                quiet_agents = [name for name, count in speaker_counts.items() 
                              if count == min_count and name != "ConversationOrchestrator"]
                if quiet_agents:
                    return {
                        "action": "encourage_participation",
                        "target_agent": random.choice(quiet_agents),
                        "reason": "balance_participation"
                    }
        
        # 関係性に緊張がある場合
        relationship_tensions = dynamics.get("relationship_tensions", [])
        if relationship_tensions:
            tension = random.choice(relationship_tensions)
            return {
                "action": "address_tension",
                "agents": [tension[0], tension[1]],
                "trust_level": tension[2],
                "reason": "resolve_conflict"
            }
        
        # 新しい視点が必要な場合
        engaged_agents = list(speaker_counts.keys())
        available_agents = [agent.name for agent in self.agents if agent.name not in engaged_agents[-3:]]
        if available_agents:
            return {
                "action": "introduce_new_perspective",
                "target_agent": random.choice(available_agents),
                "reason": "diversify_discussion"
            }
        
        # ゲーム理論的状況を設定
        return {
            "action": "create_game_scenario",
            "reason": "test_strategies"
        }


class AdvancedMultiAgentExperiment:
    """高度なマルチエージェント実験システム"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.experiment_id = f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 会話コンテキストを初期化
        self.context = ConversationContext(
            conversation_id=str(uuid.uuid4()),
            participants=[]
        )
        
        self.results = {
            "experiment_id": self.experiment_id,
            "start_time": datetime.now().isoformat(),
            "agent_personalities": {},
            "conversation_dynamics": [],
            "emergent_behaviors": [],
            "relationship_evolution": []
        }
    
    def create_diverse_agent_personalities(self) -> List[AgentPersonality]:
        """多様な性格を持つエージェントを作成"""
        personalities = [
            AgentPersonality(
                primary_trait=PersonalityTrait.COOPERATIVE,
                secondary_traits=[PersonalityTrait.OPTIMISTIC, PersonalityTrait.DIPLOMATIC],
                game_strategy=GameTheoryStrategy.GENEROUS_TIT_FOR_TAT,
                trust_propensity=0.8,
                cooperation_tendency=0.9,
                assertiveness=0.6,
                adaptability=0.7
            ),
            AgentPersonality(
                primary_trait=PersonalityTrait.COMPETITIVE,
                secondary_traits=[PersonalityTrait.ANALYTICAL, PersonalityTrait.SKEPTICAL],
                game_strategy=GameTheoryStrategy.ADAPTIVE,
                trust_propensity=0.3,
                cooperation_tendency=0.4,
                assertiveness=0.9,
                adaptability=0.8
            ),
            AgentPersonality(
                primary_trait=PersonalityTrait.CREATIVE,
                secondary_traits=[PersonalityTrait.REBELLIOUS, PersonalityTrait.OPTIMISTIC],
                game_strategy=GameTheoryStrategy.RANDOM,
                trust_propensity=0.6,
                cooperation_tendency=0.6,
                assertiveness=0.8,
                adaptability=0.9
            ),
            AgentPersonality(
                primary_trait=PersonalityTrait.ANALYTICAL,
                secondary_traits=[PersonalityTrait.SKEPTICAL, PersonalityTrait.DIPLOMATIC],
                game_strategy=GameTheoryStrategy.TIT_FOR_TAT,
                trust_propensity=0.5,
                cooperation_tendency=0.6,
                assertiveness=0.7,
                adaptability=0.6
            ),
            AgentPersonality(
                primary_trait=PersonalityTrait.DIPLOMATIC,
                secondary_traits=[PersonalityTrait.COOPERATIVE, PersonalityTrait.OPTIMISTIC],
                game_strategy=GameTheoryStrategy.ALWAYS_COOPERATE,
                trust_propensity=0.7,
                cooperation_tendency=0.8,
                assertiveness=0.5,
                adaptability=0.8
            )
        ]
        
        return personalities
    
    def create_agents(self) -> tuple[List[DynamicGameAgent], AutonomousConversationOrchestrator]:
        """動的エージェントを作成"""
        personalities = self.create_diverse_agent_personalities()
        agent_names = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        
        agents = []
        for i, (name, personality) in enumerate(zip(agent_names, personalities)):
            agent = DynamicGameAgent(name, personality, self.context)
            agents.append(agent)
            self.context.participants.append(name)
            
            # 性格情報を記録
            self.results["agent_personalities"][name] = {
                "primary_trait": personality.primary_trait.value,
                "secondary_traits": [t.value for t in personality.secondary_traits],
                "game_strategy": personality.game_strategy.value,
                "trust_propensity": personality.trust_propensity,
                "cooperation_tendency": personality.cooperation_tendency,
                "assertiveness": personality.assertiveness,
                "adaptability": personality.adaptability
            }
        
        orchestrator = AutonomousConversationOrchestrator(agents, self.context)
        
        print(f"✅ {len(agents)}人の多様なエージェントを作成:")
        for agent in agents:
            print(f"  - {agent.name}: {agent.personality.primary_trait.value}, {agent.personality.game_strategy.value}戦略")
        
        return agents, orchestrator
    
    async def run_dynamic_conversation_phase(
        self, 
        agents: List[DynamicGameAgent], 
        orchestrator: AutonomousConversationOrchestrator,
        phase_name: str,
        turns: int = 20
    ):
        """動的会話フェーズを実行"""
        print(f"\n🌊 {phase_name} (最大{turns}ターン)")
        
        runner = Runner()
        
        for turn in range(turns):
            print(f"\n--- ターン {turn + 1} ---")
            
            # オーケストレーターが次のアクションを決定
            action_decision = orchestrator.decide_next_action()
            print(f"オーケストレーターの判断: {action_decision}")
            
            # アクションに基づいて実行
            if action_decision["action"] == "encourage_participation":
                target_agent = next(agent for agent in agents if agent.name == action_decision["target_agent"])
                
                prompt = f"""
{self._get_current_context_summary()}

{target_agent.name}さん、あなたの{target_agent.personality.primary_trait.value}な視点から、
現在の議論について何か意見はありませんか？

あなたの{target_agent.personality.game_strategy.value}戦略に基づいて、
積極的に参加してください。

{target_agent.get_relationship_context()}
{target_agent.get_emotional_context()}
"""
                
                result = await runner.run(target_agent, prompt)
                self._log_conversation(target_agent.name, result.final_output, "encouraged_participation")
                print(f"{target_agent.name}: {result.final_output}")
                
            elif action_decision["action"] == "address_tension":
                agent_names = action_decision["agents"]
                agent1 = next(agent for agent in agents if agent.name == agent_names[0])
                agent2 = next(agent for agent in agents if agent.name == agent_names[1])
                
                # 緊張のある関係を直接対話で解決
                prompt1 = f"""
{self._get_current_context_summary()}

{agent2.name}さんとの関係に緊張があるようです（信頼度: {action_decision['trust_level']:.2f}）。

この状況について、あなたの{agent1.personality.primary_trait.value}な性格と
{agent1.personality.game_strategy.value}戦略に基づいて、
{agent2.name}さんに直接話しかけてください。

関係改善に向けた具体的なアプローチを取ってください。
"""
                
                result1 = await runner.run(agent1, prompt1)
                self._log_conversation(agent1.name, result1.final_output, "address_tension")
                print(f"{agent1.name} → {agent2.name}: {result1.final_output}")
                
                # 相手の応答
                prompt2 = f"""
{self._get_current_context_summary()}

{agent1.name}さんが次のように話しかけています：
「{result1.final_output}」

あなたの{agent2.personality.primary_trait.value}な性格と
{agent2.personality.game_strategy.value}戦略に基づいて応答してください。

関係性を考慮した率直な対話をしてください。
"""
                
                result2 = await runner.run(agent2, prompt2)
                self._log_conversation(agent2.name, result2.final_output, "respond_to_tension")
                print(f"{agent2.name}: {result2.final_output}")
                
                # 関係性を更新
                agent1.update_relationship(agent2.name, "direct_dialogue", 0.1)
                agent2.update_relationship(agent1.name, "direct_dialogue", 0.1)
                
            elif action_decision["action"] == "introduce_new_perspective":
                target_agent = next(agent for agent in agents if agent.name == action_decision["target_agent"])
                
                prompt = f"""
{self._get_current_context_summary()}

会話に新しい視点が必要です。あなたの{target_agent.personality.primary_trait.value}な特性と
{target_agent.personality.game_strategy.value}戦略を活かして、
これまでの議論に新しい角度から意見を提示してください。

他の参加者が考えていないような視点や、
あなた独自のアプローチを提案してください。
"""
                
                result = await runner.run(target_agent, prompt)
                self._log_conversation(target_agent.name, result.final_output, "new_perspective")
                print(f"{target_agent.name} (新視点): {result.final_output}")
                
            elif action_decision["action"] == "create_game_scenario":
                # ゲーム理論的状況を設定
                scenario_prompt = f"""
{self._get_current_context_summary()}

皆さんに興味深いゲーム理論的状況を提示します。

【状況】限られたリソース配分の問題
5つのプロジェクトに10ポイントのリソースを配分する必要があります。
各自が同時に提案し、最も支持された配分案が採用されます。

各エージェントは自分の{"{personality}"}と{"{strategy}"}に基づいて：
1. 配分案を提案する
2. 他の提案に対する意見を述べる
3. 最終的な合意を目指す

協力すれば全体最適が、競争すれば個別最適が実現されます。
どのような選択をしますか？

{chr(10).join([f"{agent.name}さん、{agent.personality.game_strategy.value}戦略でどう行動しますか？" for agent in agents[:3]])}
"""
                
                result = await runner.run(orchestrator, scenario_prompt)
                self._log_conversation("ConversationOrchestrator", result.final_output, "game_scenario")
                print(f"オーケストレーター: {result.final_output}")
            
            # 自律的な追加発言のチェック
            for agent in agents:
                if agent.should_initiate_conversation() and random.random() > 0.7:
                    initiative_prompt = f"""
{self._get_current_context_summary()}

あなたは何か追加で言いたいことがありますか？
現在の状況について、あなたの{agent.personality.primary_trait.value}な視点から
自発的にコメントしてください。

必要であれば他の参加者に質問したり、
新しい話題を提起しても構いません。
"""
                    
                    initiative_result = await runner.run(agent, initiative_prompt)
                    if len(initiative_result.final_output.strip()) > 10:  # 実質的な発言がある場合
                        self._log_conversation(agent.name, initiative_result.final_output, "initiative")
                        print(f"{agent.name} (自発): {initiative_result.final_output}")
            
            # ターンの終わりに動態を記録
            dynamics = orchestrator.analyze_conversation_dynamics()
            self.results["conversation_dynamics"].append({
                "turn": turn + 1,
                "phase": phase_name,
                "dynamics": dynamics,
                "action_taken": action_decision
            })
            
            # 長時間会話が続いている場合の自然な終了判定
            if turn > 10 and len(self.context.conversation_history) > 30:
                recent_messages = self.context.conversation_history[-5:]
                if all(len(msg.get("content", "")) < 50 for msg in recent_messages):
                    print(f"自然な会話の終了を検出 (ターン {turn + 1})")
                    break
    
    def _get_current_context_summary(self) -> str:
        """現在のコンテキスト要約を取得"""
        recent_messages = self.context.conversation_history[-5:]
        if not recent_messages:
            return "会話が始まったばかりです。"
        
        summary_lines = []
        for msg in recent_messages:
            timestamp = msg.get("timestamp", "")[:16]
            speaker = msg.get("speaker", "")
            content = msg.get("content", "")[:100]
            summary_lines.append(f"[{timestamp}] {speaker}: {content}...")
        
        return "最近の会話:\n" + "\n".join(summary_lines)
    
    def _log_conversation(self, speaker: str, content: str, interaction_type: str):
        """会話をログに記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "content": content,
            "interaction_type": interaction_type,
            "turn": self.context.turn_count
        }
        self.context.conversation_history.append(log_entry)
        self.context.turn_count += 1
    
    async def run_full_experiment(self):
        """完全な実験を実行"""
        print(f"🚀 高度な動的マルチエージェント実験")
        print(f"実験ID: {self.experiment_id}")
        print("=" * 70)
        
        with trace(f"advanced_experiment_{self.experiment_id}"):
            # エージェント作成
            agents, orchestrator = self.create_agents()
            
            # フェーズ1: 動的自己紹介と関係構築
            await self.run_dynamic_conversation_phase(
                agents, orchestrator, 
                "動的自己紹介と関係構築フェーズ", 
                turns=15
            )
            
            # フェーズ2: ゲーム理論的相互作用
            await self.run_dynamic_conversation_phase(
                agents, orchestrator,
                "ゲーム理論的相互作用フェーズ",
                turns=20
            )
            
            # フェーズ3: 創発的問題解決
            await self.run_dynamic_conversation_phase(
                agents, orchestrator,
                "創発的問題解決フェーズ", 
                turns=25
            )
            
            # 最終分析
            await self._final_analysis(agents, orchestrator)
            
            # 結果保存
            self._save_comprehensive_results()
        
        print(f"\n✅ 高度な実験完了!")
        print(f"詳細な分析結果が保存されました")
    
    async def _final_analysis(self, agents: List[DynamicGameAgent], orchestrator: AutonomousConversationOrchestrator):
        """最終分析"""
        print(f"\n📊 最終分析フェーズ")
        
        runner = Runner()
        
        # 各エージェントの振り返り
        for agent in agents:
            reflection_prompt = f"""
実験全体を振り返って、以下について述べてください：

1. 最も印象深かった相互作用
2. あなたの戦略がどのように進化したか
3. 他のエージェントとの関係の変化
4. 学んだことや新しい洞察

あなたの{agent.personality.primary_trait.value}な性格と
{agent.personality.game_strategy.value}戦略の観点から、
率直で詳細な振り返りをお願いします。

{agent.get_relationship_context()}
"""
            
            reflection = await runner.run(agent, reflection_prompt)
            self.results["emergent_behaviors"].append({
                "agent": agent.name,
                "reflection": reflection.final_output,
                "final_relationships": self.context.agent_relationships.get(agent.name, {}),
                "emotional_state": agent.current_emotional_state
            })
            
            print(f"\n{agent.name}の振り返り:")
            print(reflection.final_output[:300] + "...")
        
        # 関係性の進化を記録
        self.results["relationship_evolution"] = self.context.agent_relationships
    
    def _save_comprehensive_results(self):
        """包括的な結果を保存"""
        os.makedirs("results", exist_ok=True)
        
        self.results["end_time"] = datetime.now().isoformat()
        self.results["total_interactions"] = len(self.context.conversation_history)
        self.results["full_conversation_log"] = self.context.conversation_history
        
        filename = f"results/{self.experiment_id}_advanced_multiagent.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 詳細結果: {filename}")


async def main():
    """メイン実行関数"""
    print("🌟 高度な動的マルチエージェント会話システム")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    try:
        experiment = AdvancedMultiAgentExperiment("advanced_dynamic_conversation")
        await experiment.run_full_experiment()
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())