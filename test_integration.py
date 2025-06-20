#!/usr/bin/env python3
"""
Simple integration test for the research-grade experiment system.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.coordinator import GameCoordinator, ExperimentConfig
from game_theory.games import GameType
from utils.conversation_tracker import conversation_tracker
from utils.experiment_logger import ExperimentLogger


async def test_basic_integration():
    """Test basic integration of conversation tracking and experiment logging."""
    
    print("🧪 Testing Basic Integration...")
    
    # Create coordinator
    coordinator = GameCoordinator(
        logger_name="integration_test",
        results_dir="test_results"
    )
    
    # Create a few test agents
    coordinator.create_agent("cooperative", "TestCoop")
    coordinator.create_agent("competitive", "TestComp")
    coordinator.create_agent("tit_for_tat", "TestTFT")
    
    print(f"✅ Created {len(coordinator.agents)} test agents")
    
    # Create test experiment config
    config = ExperimentConfig(
        game_types=[GameType.PRISONERS_DILEMMA],
        agent_types=["cooperative", "competitive", "tit_for_tat"],
        num_rounds=5,  # Short test
        num_repetitions=1,
        save_results=True,
        results_dir="test_results",
        enable_conversation_tracking=True,
        enable_detailed_logging=True,
        experiment_description="Integration test experiment"
    )
    
    print("✅ Created experiment configuration")
    
    # Run experiment
    try:
        result = await coordinator.run_experiment(config)
        print(f"✅ Experiment completed: {result['experiment_id']}")
        
        # Check conversation tracking
        sessions = conversation_tracker.get_session_history()
        print(f"✅ Conversation sessions recorded: {len(sessions)}")
        
        # Verify results structure
        assert "results" in result
        assert "experiment_id" in result
        assert "config" in result
        
        print("✅ Result structure validation passed")
        
        # Test conversation analysis
        if sessions:
            sample_session = sessions[0]
            analysis = conversation_tracker.analyze_session(sample_session['session_id'])
            print(f"✅ Conversation analysis completed for session {sample_session['session_id']}")
            
            # Verify analysis structure
            assert "session_summary" in analysis
            assert "agent_statistics" in analysis
            assert "conversation_flow" in analysis
            
            print("✅ Conversation analysis structure validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


async def test_experiment_logger():
    """Test experiment logger functionality."""
    
    print("\n🧪 Testing Experiment Logger...")
    
    # Create experiment logger
    logger = ExperimentLogger("test_logger", "test_results")
    
    # Test basic logging
    logger.start_phase("test_phase", "Testing phase functionality")
    logger.log_performance_metric("test_metric", 0.5, "units", "test context")
    logger.log_agent_interaction(
        "agent1", "agent2", "test_game", 1,
        {"agent1": "cooperate", "agent2": "defect"},
        {"agent1": 1.0, "agent2": 2.0}
    )
    logger.end_phase("test_phase", {"test": "result"})
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.log_error(e, "test error context")
    
    logger.log_warning("Test warning", "test warning context")
    
    # Save results
    test_results = {"test": "data"}
    logger.save_detailed_results(test_results)
    logger.finalize_experiment()
    
    print("✅ Experiment logger test completed")
    return True


async def test_conversation_tracker():
    """Test conversation tracker functionality."""
    
    print("\n🧪 Testing Conversation Tracker...")
    
    from agents.types import AgentAction, GameDecision
    
    # Start a test session
    session_id = "test_session_001"
    conversation_tracker.start_session(
        session_id=session_id,
        participants=["agent1", "agent2"],
        game_type="test_game",
        metadata={"test": True}
    )
    
    # Record some turns
    decision1 = GameDecision(
        action=AgentAction.COOPERATE,
        reasoning="Test reasoning for cooperation",
        confidence=0.8
    )
    
    decision2 = GameDecision(
        action=AgentAction.DEFECT,
        reasoning="Test reasoning for defection",
        confidence=0.6
    )
    
    conversation_tracker.record_turn(
        session_id=session_id,
        agent_name="agent1",
        round_number=1,
        context={"game": "test"},
        decision=decision1,
        reasoning_process="Detailed reasoning process 1",
        response_time_ms=100.0,
        trust_level=0.7
    )
    
    conversation_tracker.record_turn(
        session_id=session_id,
        agent_name="agent2",
        round_number=1,
        context={"game": "test"},
        decision=decision2,
        reasoning_process="Detailed reasoning process 2",
        response_time_ms=150.0,
        opponent_last_action=AgentAction.COOPERATE,
        trust_level=0.5
    )
    
    # End session
    final_outcomes = {"winner": "agent2", "total_payoff": 10.0}
    session = conversation_tracker.end_session(session_id, final_outcomes)
    
    # Analyze session
    analysis = conversation_tracker.analyze_session(session_id)
    
    # Verify analysis
    assert analysis["session_summary"]["session_id"] == session_id
    assert len(analysis["conversation_flow"]) == 2
    assert "agent1" in analysis["agent_statistics"]["cooperation_rates"]
    assert "agent2" in analysis["agent_statistics"]["cooperation_rates"]
    
    print("✅ Conversation tracker test completed")
    return True


async def main():
    """Run all integration tests."""
    
    print("🚀 Running Integration Tests for Research System")
    print("=" * 50)
    
    tests = [
        test_conversation_tracker,
        test_experiment_logger,
        test_basic_integration
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Integration Test Results:")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All integration tests passed! Research system is ready.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)