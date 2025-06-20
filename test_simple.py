#!/usr/bin/env python3
"""Simple test to verify OpenAI Agents SDK functionality."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from agents import Agent
    print("✅ Successfully imported Agent from openai-agents")
    
    # Test basic agent creation
    agent = Agent(
        name="TestAgent",
        instructions="You are a test agent."
    )
    
    print(f"✅ Created agent with name: {getattr(agent, 'name', 'UNKNOWN')}")
    print(f"✅ Agent attributes: {[attr for attr in dir(agent) if not attr.startswith('_')]}")
    
    # Test our custom agent
    import sys
    sys.path.append('src')
    
    from src.agents.base_agent import BaseGameAgent
    from src.agents.types import AgentAction, GameDecision
    
    class SimpleTestAgent(BaseGameAgent):
        async def make_decision(self, game_context, opponent_history=None):
            return GameDecision(
                action=AgentAction.COOPERATE,
                reasoning="Test decision",
                confidence=1.0
            )
    
    test_agent = SimpleTestAgent("MyTestAgent", "test")
    print(f"✅ Created custom agent: {test_agent.name}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()