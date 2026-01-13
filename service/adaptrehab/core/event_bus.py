"""
Event Bus - Asynchronous pub-sub messaging system.

Decouples communication between layers for low-latency performance.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any
from collections import defaultdict


logger = logging.getLogger(__name__)


class EventBus:
    """
    Lightweight async event bus using pub-sub pattern.
    
    Enables decoupled communication between components
    without direct dependencies.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._is_running = False
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'errors': 0
        }
        
        logger.info("EventBus initialized")
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event identifier (e.g., 'adaptation.computed')
            callback: Async function to call when event occurs
        """
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Callback must be an async function")
        
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event: {event_type}")
            except ValueError:
                pass
    
    async def publish(self, event_type: str, data: Any = None) -> None:
        """
        Publish an event.
        
        Args:
            event_type: Event identifier
            data: Event payload
        """
        event = {
            'type': event_type,
            'data': data,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await self._event_queue.put(event)
        self._stats['events_published'] += 1
        
        logger.debug(f"Event published: {event_type}")
    
    async def start_processing(self) -> None:
        """Start processing events from queue."""
        self._is_running = True
        logger.info("EventBus started processing")
        
        while self._is_running:
            try:
                # Wait for event with timeout to allow checking _is_running
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1
                )
                
                await self._process_event(event)
                self._stats['events_processed'] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                self._stats['errors'] += 1
        
        logger.info("EventBus stopped processing")
    
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a single event by notifying all subscribers."""
        event_type = event['type']
        data = event['data']
        
        if event_type in self._subscribers:
            # Call all subscribers concurrently
            tasks = [
                callback(data) 
                for callback in self._subscribers[event_type]
            ]
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}", exc_info=True)
    
    def stop(self) -> None:
        """Stop event processing."""
        self._is_running = False
    
    def get_stats(self) -> Dict[str, int]:
        """Get event bus statistics."""
        return self._stats.copy()
    
    def clear_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'errors': 0
        }
