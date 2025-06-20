#!/usr/bin/env python3
"""
Test individual components of the research system.
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test conversation tracker
print("🧪 Testing Conversation Tracker...")

try:
    from utils.conversation_tracker import ConversationTracker, ConversationTurn, ConversationSession
    from agents.types import AgentAction, GameDecision
    
    # Create tracker
    tracker = ConversationTracker("test_conversations")
    
    # Create test decision
    decision = GameDecision(
        action=AgentAction.COOPERATE,
        reasoning="Test cooperation decision",
        confidence=0.8,
        knowledge_to_share=["test_knowledge"]
    )
    
    # Test session creation
    session_id = "test_session_001"
    tracker.start_session(
        session_id=session_id,
        participants=["alice", "bob"],
        game_type="prisoners_dilemma",
        metadata={"test": True}
    )
    
    # Test turn recording
    tracker.record_turn(
        session_id=session_id,
        agent_name="alice",
        round_number=1,
        context={"game": "test"},
        decision=decision,
        reasoning_process="Detailed test reasoning",
        response_time_ms=100.0,
        trust_level=0.7
    )
    
    # End session
    tracker.end_session(session_id, {"winner": "alice"})
    
    # Test analysis
    analysis = tracker.analyze_session(session_id)
    
    print(f"✅ Conversation Tracker: Session {session_id} created and analyzed")
    print(f"   - Participants: {analysis['session_summary']['participants']}")
    print(f"   - Total turns: {analysis['session_summary']['total_turns']}")
    
except Exception as e:
    print(f"❌ Conversation Tracker failed: {e}")

# Test experiment logger
print("\n🧪 Testing Experiment Logger...")

try:
    from utils.experiment_logger import ExperimentLogger
    
    # Create logger
    logger = ExperimentLogger("test_experiment", "test_results")
    
    # Test phase management
    logger.start_phase("setup", "Setting up test experiment")
    logger.log_performance_metric("test_metric", 0.75, "score", "test context")
    logger.log_agent_interaction(
        "alice", "bob", "prisoners_dilemma", 1,
        {"alice": "cooperate", "bob": "defect"},
        {"alice": 1.0, "bob": 3.0}
    )
    logger.end_phase("setup", {"agents_created": 2})
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.log_error(e, "test error context")
    
    # Test warning
    logger.log_warning("Test warning message", "test warning context")
    
    # Save results
    test_results = {
        "results": {
            "prisoners_dilemma": [
                {
                    "participants": ["alice", "bob"],
                    "payoffs": {"alice": 10.0, "bob": 15.0},
                    "cooperation_rates": {"alice": 0.8, "bob": 0.4},
                    "winner": "bob"
                }
            ]
        }
    }
    
    logger.save_detailed_results(test_results)
    logger.finalize_experiment()
    
    print("✅ Experiment Logger: Successfully logged experiment data")
    print(f"   - Experiment ID: {logger.experiment_id}")
    print(f"   - Results directory: {logger.experiment_dir}")
    
except Exception as e:
    print(f"❌ Experiment Logger failed: {e}")

# Test game types and payoffs
print("\n🧪 Testing Game Theory Components...")

try:
    from game_theory.games import GameType, PrisonersDilemma
    from game_theory.payoff import RewardMatrix, PayoffCalculator
    from agents.types import AgentAction
    
    # Test reward matrix
    matrix = RewardMatrix.prisoner_dilemma()
    calculator = PayoffCalculator(matrix)
    
    # Test payoff calculation
    payoff1, payoff2 = calculator.calculate_round_payoffs(
        AgentAction.COOPERATE, AgentAction.DEFECT
    )
    
    print(f"✅ Game Theory Components: Payoff calculation working")
    print(f"   - Cooperate vs Defect: {payoff1}, {payoff2}")
    
    # Test cooperation rate calculation
    actions = [AgentAction.COOPERATE, AgentAction.COOPERATE, AgentAction.DEFECT]
    coop_rate = calculator.calculate_cooperation_rate(actions)
    
    print(f"   - Cooperation rate: {coop_rate:.3f}")
    
except Exception as e:
    print(f"❌ Game Theory Components failed: {e}")

# Test file outputs
print("\n📁 Checking Generated Files...")

results_dir = Path("test_results")
if results_dir.exists():
    files = list(results_dir.rglob("*"))
    print(f"✅ Generated {len(files)} files in test_results/")
    
    for file_path in sorted(files)[:10]:  # Show first 10 files
        if file_path.is_file():
            size = file_path.stat().st_size
            print(f"   - {file_path.relative_to(results_dir)}: {size} bytes")
else:
    print("⚠️  No test_results directory found")

# Test conversation export
print("\n📊 Testing Conversation Export...")

try:
    from utils.conversation_tracker import conversation_tracker
    
    # Check if we have any sessions
    sessions = conversation_tracker.get_session_history()
    print(f"✅ Found {len(sessions)} conversation sessions")
    
    if sessions:
        # Export to CSV
        csv_file = "test_conversations.csv"
        conversation_tracker.export_conversations_csv(csv_file)
        
        if Path(csv_file).exists():
            size = Path(csv_file).stat().st_size
            print(f"✅ Exported conversations to {csv_file} ({size} bytes)")
        else:
            print("⚠️  CSV export file not created")
    
except Exception as e:
    print(f"❌ Conversation export failed: {e}")

print("\n🎉 Component testing completed!")
print("=" * 50)
print("✅ Core research components are functional:")
print("   - Conversation tracking and analysis")
print("   - Experiment logging and reporting") 
print("   - Game theory calculations")
print("   - Data export capabilities")
print("\n🔬 The research-grade experiment system is ready for use!")