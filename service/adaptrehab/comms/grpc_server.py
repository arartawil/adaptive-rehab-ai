"""
gRPC Server Implementation

Provides the communication interface between Unity and the adaptation engine.
"""

import asyncio
import logging
from concurrent import futures
from typing import Dict, Any

import grpc
from adaptrehab.comms import adaptation_pb2, adaptation_pb2_grpc
from adaptrehab.core import AdaptationEngine
from adaptrehab.modules import StateVector, AdaptationAction


logger = logging.getLogger(__name__)


class AdaptationServicer(adaptation_pb2_grpc.AdaptationServiceServicer):
    """
    gRPC service implementation for adaptation requests.
    
    Handles requests from Unity clients and routes them to the adaptation engine.
    """
    
    def __init__(self, engine: AdaptationEngine):
        self.engine = engine
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        logger.info("AdaptationServicer initialized")
    
    def Initialize(self, request, context):
        """Initialize a new adaptation session."""
        try:
            logger.info(f"Initialize request from session: {request.session_id}")
            
            # Convert protobuf to dict
            patient_profile = {
                'patient_id': request.patient_profile.patient_id,
                'condition': request.patient_profile.condition,
                'baseline_performance': request.patient_profile.baseline_performance,
                'metadata': dict(request.patient_profile.metadata)
            }
            
            task_config = {
                'task_type': request.task_config.task_type,
                'initial_difficulty': dict(request.task_config.initial_difficulty),
                'safety_bounds': self._parse_safety_bounds(request.task_config.safety_bounds)
            }
            
            # Run async initialization
            success = self.loop.run_until_complete(
                self.engine.initialize_session(
                    request.session_id,
                    request.module_type,
                    patient_profile,
                    task_config
                )
            )
            
            if success and self.engine.active_module:
                metadata = self.engine.active_module.get_metadata()
                return adaptation_pb2.InitResponse(
                    success=True,
                    message="Session initialized successfully",
                    module_name=metadata['name'],
                    module_version=metadata['version']
                )
            else:
                return adaptation_pb2.InitResponse(
                    success=False,
                    message="Failed to initialize session",
                    module_name="",
                    module_version=""
                )
                
        except Exception as e:
            logger.error(f"Error in Initialize: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return adaptation_pb2.InitResponse(
                success=False,
                message=f"Error: {str(e)}",
                module_name="",
                module_version=""
            )
    
    def GetAdaptation(self, request, context):
        """Get adaptation decision based on current state."""
        try:
            # Convert protobuf to StateVector
            state = StateVector(
                performance_metrics=dict(request.performance_metrics),
                sensor_data=dict(request.raw_sensors),
                task_state=dict(request.task_state),
                timestamp=float(request.timestamp),
                session_id=request.session_id
            )
            
            # Compute adaptation
            decision = self.loop.run_until_complete(
                self.engine.compute_adaptation(request.session_id, state)
            )
            
            if decision is None:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to compute adaptation")
                return adaptation_pb2.AdaptationDecision()
            
            # Convert to protobuf
            return adaptation_pb2.AdaptationDecision(
                action=decision.action.value,
                magnitude=decision.magnitude,
                parameters=decision.parameters,
                confidence=decision.confidence,
                explanation=decision.explanation,
                timestamp=int(state.timestamp * 1000)
            )
            
        except Exception as e:
            logger.error(f"Error in GetAdaptation: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return adaptation_pb2.AdaptationDecision()
    
    def UpdateFeedback(self, request, context):
        """Receive feedback/reward signal."""
        try:
            success = self.loop.run_until_complete(
                self.engine.update_feedback(request.session_id, request.reward)
            )
            
            return adaptation_pb2.AckResponse(
                success=success,
                message="Feedback received" if success else "Failed to process feedback"
            )
            
        except Exception as e:
            logger.error(f"Error in UpdateFeedback: {e}", exc_info=True)
            return adaptation_pb2.AckResponse(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    def SwapModule(self, request, context):
        """Hot-swap the active adaptation module."""
        try:
            logger.info(f"Module swap request: {request.module_type}")
            
            config = dict(request.config) if request.config else None
            
            success = self.loop.run_until_complete(
                self.engine.swap_module(
                    request.session_id,
                    request.module_type,
                    config
                )
            )
            
            return adaptation_pb2.AckResponse(
                success=success,
                message=f"Module swapped to {request.module_type}" if success 
                       else "Failed to swap module"
            )
            
        except Exception as e:
            logger.error(f"Error in SwapModule: {e}", exc_info=True)
            return adaptation_pb2.AckResponse(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    def GetStatus(self, request, context):
        """Get current service status."""
        try:
            status = self.engine.get_status()
            
            active_module = ""
            if status['active_module']:
                active_module = status['active_module']['name']
            
            return adaptation_pb2.StatusResponse(
                is_running=status['is_running'],
                active_module=active_module,
                active_sessions=status['active_sessions'],
                average_latency_ms=status['statistics']['average_latency_ms'],
                system_info={
                    'total_adaptations': str(status['statistics']['total_adaptations']),
                    'safety_interventions': str(status['statistics']['safety_interventions']),
                    'module_swaps': str(status['statistics']['module_swaps'])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in GetStatus: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return adaptation_pb2.StatusResponse()
    
    def EndSession(self, request, context):
        """End an adaptation session."""
        try:
            success = self.loop.run_until_complete(
                self.engine.end_session(request.session_id)
            )
            
            return adaptation_pb2.AckResponse(
                success=success,
                message="Session ended" if success else "Failed to end session"
            )
            
        except Exception as e:
            logger.error(f"Error in EndSession: {e}", exc_info=True)
            return adaptation_pb2.AckResponse(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    def _parse_safety_bounds(self, bounds_pb) -> Dict[str, Any]:
        """Parse protobuf safety bounds to dict."""
        bounds = {
            'difficulty': {
                'min': bounds_pb.difficulty_min,
                'max': bounds_pb.difficulty_max
            },
            'max_change_rate': bounds_pb.max_change_rate
        }
        
        # Parse parameter bounds
        for param_name, range_pb in bounds_pb.parameter_bounds.items():
            bounds[param_name] = {
                'min': range_pb.min,
                'max': range_pb.max
            }
        
        return bounds


def serve(engine: AdaptationEngine, port: int = 50051, max_workers: int = 10):
    """
    Start the gRPC server.
    
    Args:
        engine: AdaptationEngine instance
        port: Port to listen on
        max_workers: Maximum thread pool workers
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    adaptation_pb2_grpc.add_AdaptationServiceServicer_to_server(
        AdaptationServicer(engine),
        server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    logger.info(f"gRPC server started on port {port}")
    logger.info(f"Listening for Unity connections...")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(grace=5)
