"""
Test Web Integration with HTML Memory Game

Simulates browser requests to validate REST API.
"""

import logging
import time

from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule
from adaptrehab.comms.rest_server import create_rest_server
from adaptrehab.utils import setup_logging


logger = logging.getLogger(__name__)


def test_web_integration():
    """Test complete web game integration."""
    
    setup_logging("INFO")
    
    logger.info("="*60)
    logger.info("WEB INTEGRATION TEST - HTML Memory Game")
    logger.info("="*60)
    
    # Initialize engine and REST server
    config_manager = ConfigManager()
    engine = AdaptationEngine(config_manager.to_dict())
    engine.register_module('rule_based', RuleBasedModule)
    
    app = create_rest_server(engine)
    
    # Use TestClient from starlette instead of AsyncClient
    from starlette.testclient import TestClient
    
    with TestClient(app) as client:
        session_id = "test_web_session"
        
        # 1. Initialize Session
        logger.info("\n1️⃣  Initializing web session...")
        response = client.post("/session/init", json={
            "session_id": session_id,
            "module_name": "rule_based",
            "patient_profile": {
                "patient_id": "web_user_001",
                "condition": "cognitive",
                "baseline_performance": 0.5
            },
            "task_config": {
                "task_type": "memory",
                "safety_bounds": {
                    "difficulty": {"min": 0.3, "max": 0.9}
                }
            }
        })
        
        assert response.status_code == 200
        init_data = response.json()
        logger.info(f"   ✓ Session initialized: {init_data['session_id']}")
        
        # 2. Simulate multiple game rounds
        logger.info("\n2️⃣  Simulating game rounds...")
        
        rounds = [
            # Round 1: Poor performance (accuracy 0.4)
            {
                "accuracy": 0.40,
                "success_rate": 0.40,
                "reaction_time": 3.5,
                "error_rate": 0.60,
                "consistency": 0.35
            },
            # Round 2: Improved (accuracy 0.6)
            {
                "accuracy": 0.60,
                "success_rate": 0.60,
                "reaction_time": 2.8,
                "error_rate": 0.40,
                "consistency": 0.55
            },
            # Round 3: Good (accuracy 0.75)
            {
                "accuracy": 0.75,
                "success_rate": 0.75,
                "reaction_time": 2.2,
                "error_rate": 0.25,
                "consistency": 0.70
            },
            # Round 4: Excellent (accuracy 0.90)
            {
                "accuracy": 0.90,
                "success_rate": 0.90,
                "reaction_time": 1.8,
                "error_rate": 0.10,
                "consistency": 0.85
            },
        ]
        
        difficulties = []
        
        for i, metrics in enumerate(rounds, 1):
            logger.info(f"\n   Round {i}:")
            logger.info(f"   Player accuracy: {metrics['accuracy']:.2f}")
            
            # Request adaptation
            adapt_response = client.post("/adapt", json={
                "session_id": session_id,
                "performance_metrics": metrics,
                "sensor_data": {},
                "task_state": {
                    "difficulty": difficulties[-1] if difficulties else 0.5,
                    "round": i
                }
            })
            
            assert adapt_response.status_code == 200
            decision = adapt_response.json()
            
            new_difficulty = decision['parameters']['difficulty']
            difficulties.append(new_difficulty)
            
            logger.info(f"   AI Decision: {decision['action'].upper()}")
            logger.info(f"   New difficulty: {new_difficulty:.2f}")
            logger.info(f"   Confidence: {decision['confidence']:.2f}")
            logger.info(f"   📝 {decision['explanation']}")
            
            # Send reward feedback
            reward = (metrics['accuracy'] - 0.5) * 2
            feedback_response = client.post("/feedback", json={
                "session_id": session_id,
                "reward": reward
            })
            
            assert feedback_response.status_code == 200
        
        # 3. Get system status
        logger.info("\n3️⃣  Checking system status...")
        status_response = client.get("/status")
        assert status_response.status_code == 200
        status = status_response.json()
        
        logger.info(f"   Active sessions: {status['active_sessions']}")
        logger.info(f"   Total adaptations: {status['total_adaptations']}")
        logger.info(f"   Avg latency: {status['avg_latency_ms']:.2f}ms")
        
        # 4. End session
        logger.info("\n4️⃣  Ending session...")
        end_response = client.post(f"/session/end?session_id={session_id}")
        assert end_response.status_code == 200
        logger.info("  sion ended")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Rounds completed: {len(rounds)}")
        logger.info(f"Difficulty progression: {difficulties[0]:.2f} → {difficulties[-1]:.2f}")
        logger.info(f"Difficulty change: {(difficulties[-1] - difficulties[0])*100:+.1f}%")
        logger.info(f"Performance: {rounds[0]['accuracy']:.2f} → {rounds[-1]['accuracy']:.2f}")
        logger.info("\n✅ All web integration tests passed!")
        logger.info("\n💡 Next step: Start REST server and open memory-game.html in browser")
        logger.info("   Run: python run_rest_server.py")


if __name__ == "__main__":
    test_web_integration()