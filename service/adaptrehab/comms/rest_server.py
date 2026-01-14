"""
REST API Server for Web Clients

Provides HTTP endpoints for browser-based games using JSON.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import time

from adaptrehab.core import AdaptationEngine
from adaptrehab.modules import StateVector

logger = logging.getLogger(__name__)


# Request/Response Models
class InitSessionRequest(BaseModel):
    session_id: str
    module_name: str = "rule_based"
    patient_profile: Dict[str, Any] = Field(default_factory=lambda: {
        'patient_id': 'web_patient',
        'condition': 'cognitive',
        'baseline_performance': 0.5
    })
    task_config: Dict[str, Any] = Field(default_factory=lambda: {
        'task_type': 'memory',
        'safety_bounds': {
            'difficulty': {'min': 0.0, 'max': 1.0}
        }
    })


class AdaptationRequest(BaseModel):
    session_id: str
    performance_metrics: Dict[str, float]
    sensor_data: Optional[Dict[str, float]] = Field(default_factory=dict)
    task_state: Dict[str, Any]


class FeedbackRequest(BaseModel):
    session_id: str
    reward: float


class AdaptationResponse(BaseModel):
    action: str
    magnitude: float
    parameters: Dict[str, Any]
    confidence: float
    explanation: str


class StatusResponse(BaseModel):
    active_sessions: int
    total_adaptations: int
    avg_latency_ms: float


class RESTServer:
    """REST API wrapper for AdaptationEngine."""
    
    def __init__(self, engine: AdaptationEngine):
        self.engine = engine
        self.app = FastAPI(
            title="Adaptive Rehab AI - REST API",
            description="REST endpoints for web-based rehabilitation games",
            version="1.0.0"
        )
        
        # Enable CORS for browser access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "Adaptive Rehab AI",
                "version": "1.0.0",
                "endpoints": {
                    "POST /session/init": "Initialize session",
                    "POST /adapt": "Get adaptation decision",
                    "POST /feedback": "Send reward feedback",
                    "GET /status": "Get system status",
                    "POST /session/end": "End session"
                }
            }
        
        @self.app.post("/session/init")
        async def init_session(request: InitSessionRequest):
            """Initialize a new adaptation session."""
            try:
                success = await self.engine.initialize_session(
                    request.session_id,
                    request.module_name,
                    request.patient_profile,
                    request.task_config
                )
                
                if not success:
                    raise HTTPException(status_code=400, detail="Session initialization failed")
                
                return {
                    "success": True,
                    "session_id": request.session_id,
                    "module": request.module_name
                }
                
            except Exception as e:
                logger.error(f"Init session error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/adapt", response_model=AdaptationResponse)
        async def get_adaptation(request: AdaptationRequest):
            """Get adaptation decision based on current state."""
            try:
                # Create state vector
                state = StateVector(
                    performance_metrics=request.performance_metrics,
                    sensor_data=request.sensor_data or {},
                    task_state=request.task_state,
                    timestamp=time.time(),
                    session_id=request.session_id
                )
                
                # Get adaptation
                decision = await self.engine.compute_adaptation(
                    request.session_id,
                    state
                )
                
                if not decision:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                return AdaptationResponse(
                    action=decision.action.value,
                    magnitude=decision.magnitude,
                    parameters=decision.parameters,
                    confidence=decision.confidence,
                    explanation=decision.explanation
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Adaptation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/feedback")
        async def send_feedback(request: FeedbackRequest):
            """Send reward feedback to adaptation engine."""
            try:
                await self.engine.update_feedback(
                    request.session_id,
                    request.reward
                )
                
                return {"success": True}
                
            except Exception as e:
                logger.error(f"Feedback error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status", response_model=StatusResponse)
        async def get_status():
            """Get system status."""
            try:
                status = self.engine.get_status()
                stats = status.get('statistics', {})
                sessions = status.get('sessions', {})
                
                return StatusResponse(
                    active_sessions=len(sessions),
                    total_adaptations=stats.get('total_adaptations', 0),
                    avg_latency_ms=stats.get('avg_latency_ms', 0.0)
                )
                
            except Exception as e:
                logger.error(f"Status error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/session/end")
        async def end_session(session_id: str):
            """End an adaptation session."""
            try:
                await self.engine.end_session(session_id)
                return {"success": True}
                
            except Exception as e:
                logger.error(f"End session error: {e}")
                raise HTTPException(status_code=500, detail=str(e))


def create_rest_server(engine: AdaptationEngine) -> FastAPI:
    """Factory function to create REST server."""
    server = RESTServer(engine)
    return server.app
