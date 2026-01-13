"""
Adaptation Engine - Core orchestrator for the adaptation system.

Manages module lifecycle, event routing, and safety validation.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from adaptrehab.modules.base_module import (
    AdaptationModule,
    StateVector,
    AdaptationDecision
)
from adaptrehab.core.safety_wrapper import SafetyWrapper
from adaptrehab.core.event_bus import EventBus
from adaptrehab.core.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class AdaptationEngine:
    """
    Main adaptation engine that coordinates all components.
    
    Responsibilities:
    - Load and manage adaptation modules
    - Route sensor data through safety wrapper
    - Publish adaptation decisions
    - Handle hot-swapping of modules
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.event_bus = EventBus()
        self.safety_wrapper = SafetyWrapper(config.get('safety', {}))
        self.config_manager = ConfigManager(config)
        
        self.active_module: Optional[AdaptationModule] = None
        self.module_registry: Dict[str, type] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        self.is_running = False
        self.stats = {
            'total_adaptations': 0,
            'safety_interventions': 0,
            'average_latency_ms': 0.0,
            'module_swaps': 0
        }
        
        logger.info("AdaptationEngine initialized")
    
    def register_module(self, module_name: str, module_class: type) -> None:
        """
        Register an adaptation module type.
        
        Args:
            module_name: Identifier for the module (e.g., 'rule_based', 'fuzzy', 'rl_ppo')
            module_class: Class that implements AdaptationModule interface
        """
        if not issubclass(module_class, AdaptationModule):
            raise TypeError(f"{module_class} must inherit from AdaptationModule")
        
        self.module_registry[module_name] = module_class
        logger.info(f"Registered module: {module_name}")
    
    async def initialize_session(
        self,
        session_id: str,
        module_type: str,
        patient_profile: Dict[str, Any],
        task_config: Dict[str, Any]
    ) -> bool:
        """
        Initialize a new adaptation session.
        
        Args:
            session_id: Unique session identifier
            module_type: Type of adaptation module to use
            patient_profile: Patient information
            task_config: Task configuration and safety bounds
            
        Returns:
            True if initialization successful
        """
        try:
            # Get module class
            if module_type not in self.module_registry:
                logger.error(f"Unknown module type: {module_type}")
                return False
            
            module_class = self.module_registry[module_type]
            
            # Create and initialize module
            module = module_class(module_id=f"{session_id}_{module_type}")
            module_config = self.config.get('module_configs', {}).get(module_type, {})
            
            success = await module.initialize(module_config, patient_profile)
            if not success:
                logger.error(f"Failed to initialize module: {module_type}")
                return False
            
            # Set as active module (for now, single session)
            self.active_module = module
            
            # Configure safety wrapper
            self.safety_wrapper.set_bounds(task_config.get('safety_bounds', {}))
            
            # Store session info
            self.sessions[session_id] = {
                'module_type': module_type,
                'patient_profile': patient_profile,
                'task_config': task_config,
                'start_time': datetime.now(),
                'adaptation_count': 0
            }
            
            self.is_running = True
            logger.info(f"Session {session_id} initialized with {module_type}")
            
            # Publish initialization event
            await self.event_bus.publish('session.initialized', {
                'session_id': session_id,
                'module_type': module_type
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing session: {e}", exc_info=True)
            return False
    
    async def compute_adaptation(
        self,
        session_id: str,
        state: StateVector
    ) -> Optional[AdaptationDecision]:
        """
        Compute adaptation decision for given state.
        
        This is the main adaptation loop entry point.
        
        Args:
            session_id: Session identifier
            state: Current state vector from Unity
            
        Returns:
            Validated adaptation decision, or None if error
        """
        if not self.is_running or self.active_module is None:
            logger.warning("Engine not running or no active module")
            return None
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. Validate state
            if not self.active_module.validate_state(state):
                logger.error("Invalid state vector")
                return None
            
            # 2. Compute adaptation from AI module
            decision = await self.active_module.compute_adaptation(state)
            
            # 3. Safety validation
            safe_decision, was_modified = await self.safety_wrapper.validate_decision(
                decision,
                state
            )
            
            if was_modified:
                self.stats['safety_interventions'] += 1
                logger.warning(f"Safety intervention applied: {safe_decision.explanation}")
            
            # 4. Update statistics
            latency = (asyncio.get_event_loop().time() - start_time) * 1000  # ms
            self._update_stats(latency)
            
            # 5. Update session
            if session_id in self.sessions:
                self.sessions[session_id]['adaptation_count'] += 1
            
            # 6. Publish decision event
            await self.event_bus.publish('adaptation.computed', {
                'session_id': session_id,
                'decision': safe_decision,
                'latency_ms': latency,
                'safety_modified': was_modified
            })
            
            return safe_decision
            
        except Exception as e:
            logger.error(f"Error computing adaptation: {e}", exc_info=True)
            return None
    
    async def update_feedback(self, session_id: str, reward: float) -> bool:
        """
        Send feedback signal to learning modules.
        
        Args:
            session_id: Session identifier
            reward: Reward signal (-1.0 to 1.0)
            
        Returns:
            True if update successful
        """
        if self.active_module is None:
            return False
        
        try:
            await self.active_module.update(reward)
            
            await self.event_bus.publish('feedback.received', {
                'session_id': session_id,
                'reward': reward
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating feedback: {e}", exc_info=True)
            return False
    
    async def swap_module(
        self,
        session_id: str,
        new_module_type: str,
        new_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Hot-swap the active adaptation module.
        
        Critical feature for A/B testing and gradual rollout.
        
        Args:
            session_id: Session identifier
            new_module_type: Type of new module to load
            new_config: Optional new configuration
            
        Returns:
            True if swap successful
        """
        if session_id not in self.sessions:
            logger.error(f"Unknown session: {session_id}")
            return False
        
        try:
            logger.info(f"Hot-swapping to module: {new_module_type}")
            
            # Save current module state if needed
            if self.active_module:
                old_type = self.sessions[session_id]['module_type']
                checkpoint_path = f"checkpoints/{session_id}_{old_type}.ckpt"
                await self.active_module.save_checkpoint(checkpoint_path)
            
            # Create new module
            if new_module_type not in self.module_registry:
                logger.error(f"Unknown module type: {new_module_type}")
                return False
            
            module_class = self.module_registry[new_module_type]
            new_module = module_class(module_id=f"{session_id}_{new_module_type}")
            
            # Initialize with existing session config
            session_info = self.sessions[session_id]
            config = new_config or self.config.get('module_configs', {}).get(new_module_type, {})
            
            success = await new_module.initialize(config, session_info['patient_profile'])
            if not success:
                logger.error("Failed to initialize new module")
                return False
            
            # Swap
            old_module = self.active_module
            self.active_module = new_module
            
            # Cleanup old module
            if old_module:
                await old_module.reset()
            
            # Update session
            self.sessions[session_id]['module_type'] = new_module_type
            self.stats['module_swaps'] += 1
            
            logger.info(f"Module swap successful: {new_module_type}")
            
            await self.event_bus.publish('module.swapped', {
                'session_id': session_id,
                'new_module': new_module_type
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error swapping module: {e}", exc_info=True)
            return False
    
    async def end_session(self, session_id: str) -> bool:
        """End adaptation session and cleanup."""
        if session_id not in self.sessions:
            return False
        
        try:
            # Save final checkpoint
            if self.active_module:
                module_type = self.sessions[session_id]['module_type']
                checkpoint_path = f"checkpoints/{session_id}_{module_type}_final.ckpt"
                await self.active_module.save_checkpoint(checkpoint_path)
                await self.active_module.reset()
            
            # Remove session
            session_info = self.sessions.pop(session_id)
            
            logger.info(f"Session {session_id} ended. Total adaptations: "
                       f"{session_info['adaptation_count']}")
            
            await self.event_bus.publish('session.ended', {
                'session_id': session_id,
                'stats': session_info
            })
            
            # If no more sessions, stop engine
            if not self.sessions:
                self.is_running = False
                self.active_module = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error ending session: {e}", exc_info=True)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        return {
            'is_running': self.is_running,
            'active_module': self.active_module.get_metadata() if self.active_module else None,
            'active_sessions': len(self.sessions),
            'statistics': self.stats,
            'registered_modules': list(self.module_registry.keys())
        }
    
    def _update_stats(self, latency_ms: float) -> None:
        """Update running statistics."""
        total = self.stats['total_adaptations']
        avg = self.stats['average_latency_ms']
        
        # Running average
        self.stats['average_latency_ms'] = (avg * total + latency_ms) / (total + 1)
        self.stats['total_adaptations'] += 1
    
    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down AdaptationEngine")
        
        # End all sessions
        for session_id in list(self.sessions.keys()):
            await self.end_session(session_id)
        
        self.is_running = False
        logger.info("AdaptationEngine shutdown complete")
