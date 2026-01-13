"""
Test gRPC communication with a mock Unity client.

Tests the full communication stack: Unity client → gRPC → Engine → AI Module
"""

import asyncio
import logging
from concurrent import futures
import time

import grpc
from adaptrehab.comms import adaptation_pb2, adaptation_pb2_grpc
from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule
from adaptrehab.utils import setup_logging
from adaptrehab.comms.grpc_server import serve, AdaptationServicer


logger = logging.getLogger(__name__)


class MockUnityClient:
    """Simulates a Unity client connecting via gRPC."""
    
    def __init__(self, server_address: str = 'localhost:50051'):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = adaptation_pb2_grpc.AdaptationServiceStub(self.channel)
        logger.info(f"Mock Unity client connected to {server_address}")
    
    def initialize_session(self, session_id: str):
        """Initialize adaptation session."""
        patient_profile = adaptation_pb2.PatientProfile(
            patient_id='TEST_P001',
            condition='stroke',
            baseline_performance=0.5,
            metadata={'test': 'true'}
        )
        
        safety_bounds = adaptation_pb2.SafetyBounds(
            difficulty_min=0.0,
            difficulty_max=1.0,
            max_change_rate=0.2
        )
        
        task_config = adaptation_pb2.TaskConfig(
            task_type='memory',
            initial_difficulty={'difficulty': 0.5},
            safety_bounds=safety_bounds
        )
        
        request = adaptation_pb2.InitRequest(
            session_id=session_id,
            patient_profile=patient_profile,
            task_config=task_config,
            module_type='rule_based'
        )
        
        response = self.stub.Initialize(request)
        return response
    
    def get_adaptation(self, session_id: str, performance: float, difficulty: float, round_num: int):
        """Request adaptation decision."""
        request = adaptation_pb2.SensorData(
            session_id=session_id,
            timestamp=int(time.time() * 1000),
            performance_metrics={
                'accuracy': performance,
                'success_rate': performance,
                'reaction_time': 2.0
            },
            raw_sensors={
                'hand_velocity': 0.5,
                'head_rotation': 0.1
            },
            task_state={
                'difficulty': str(difficulty),
                'round': str(round_num)
            }
        )
        
        response = self.stub.GetAdaptation(request)
        return response
    
    def send_feedback(self, session_id: str, reward: float):
        """Send reward signal."""
        request = adaptation_pb2.RewardSignal(
            session_id=session_id,
            reward=reward,
            outcome_metrics={'success': 1.0 if reward > 0 else 0.0}
        )
        
        response = self.stub.UpdateFeedback(request)
        return response
    
    def get_status(self):
        """Get server status."""
        request = adaptation_pb2.Empty()
        response = self.stub.GetStatus(request)
        return response
    
    def end_session(self, session_id: str):
        """End session."""
        request = adaptation_pb2.SessionRequest(session_id=session_id)
        response = self.stub.EndSession(request)
        return response
    
    def close(self):
        """Close connection."""
        self.channel.close()


async def start_server_async(engine):
    """Start gRPC server in background."""
    import threading
    
    def run_server():
        serve(engine, port=50051, max_workers=10)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    return server_thread


async def test_grpc_communication():
    """Test full gRPC communication stack."""
    
    setup_logging("INFO")
    logger.info("=== Testing gRPC Communication ===\n")
    
    # 1. Setup server
    logger.info("Starting gRPC server...")
    config_manager = ConfigManager()
    config = config_manager.to_dict()
    engine = AdaptationEngine(config)
    engine.register_module('rule_based', RuleBasedModule)
    
    server_thread = await start_server_async(engine)
    logger.info("✓ Server started\n")
    
    # 2. Create Unity client
    logger.info("Creating mock Unity client...")
    client = MockUnityClient('localhost:50051')
    logger.info("✓ Client connected\n")
    
    # 3. Initialize session
    logger.info("Initializing session...")
    session_id = "grpc_test_session"
    init_response = client.initialize_session(session_id)
    
    if init_response.success:
        logger.info(f"✓ Session initialized")
        logger.info(f"  Module: {init_response.module_name} v{init_response.module_version}\n")
    else:
        logger.error(f"✗ Initialization failed: {init_response.message}")
        return
    
    # 4. Run adaptation loop
    logger.info("=== Running Adaptation Loop ===\n")
    
    latencies = []
    
    for round_num in range(1, 11):
        performance = 0.3 + (round_num * 0.07)  # Improving performance
        difficulty = 0.5
        
        # Measure latency
        start_time = time.perf_counter()
        
        decision = client.get_adaptation(session_id, performance, difficulty, round_num)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        latencies.append(latency_ms)
        
        logger.info(f"Round {round_num}:")
        logger.info(f"  Performance: {performance:.2f}")
        logger.info(f"  Decision: {decision.action}")
        logger.info(f"  New Difficulty: {decision.parameters.get('difficulty', 0):.2f}")
        logger.info(f"  Confidence: {decision.confidence:.2f}")
        logger.info(f"  Latency: {latency_ms:.2f}ms")
        logger.info(f"  Explanation: {decision.explanation}\n")
        
        # Send feedback
        reward = (performance - 0.5) * 2
        feedback_response = client.send_feedback(session_id, reward)
        
        await asyncio.sleep(0.1)  # Simulate time between rounds
    
    # 5. Get status
    logger.info("=== Server Status ===")
    status = client.get_status()
    logger.info(f"Running: {status.is_running}")
    logger.info(f"Active Module: {status.active_module}")
    logger.info(f"Active Sessions: {status.active_sessions}")
    logger.info(f"Average Latency: {status.average_latency_ms:.2f}ms\n")
    
    # 6. Latency analysis
    logger.info("=== Latency Analysis ===")
    logger.info(f"Mean: {sum(latencies)/len(latencies):.2f}ms")
    logger.info(f"Min: {min(latencies):.2f}ms")
    logger.info(f"Max: {max(latencies):.2f}ms")
    logger.info(f"P95: {sorted(latencies)[int(len(latencies)*0.95)]:.2f}ms")
    logger.info(f"P99: {sorted(latencies)[int(len(latencies)*0.99)]:.2f}ms")
    
    target_latency = 50
    if max(latencies) < target_latency:
        logger.info(f"✓ All latencies under {target_latency}ms target!\n")
    else:
        logger.warning(f"✗ Some latencies exceed {target_latency}ms target\n")
    
    # 7. End session
    logger.info("Ending session...")
    end_response = client.end_session(session_id)
    if end_response.success:
        logger.info("✓ Session ended\n")
    
    # 8. Cleanup
    client.close()
    logger.info("=== Test Complete! ===")
    logger.info("✓ gRPC communication working correctly")
    logger.info("✓ Full Unity ↔ Python stack validated")


if __name__ == "__main__":
    asyncio.run(test_grpc_communication())
