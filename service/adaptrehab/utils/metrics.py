"""
Performance metrics and monitoring utilities.
"""

import time
from typing import Dict, Any
from contextlib import contextmanager


class PerformanceMonitor:
    """Simple performance monitoring for latency tracking."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    @contextmanager
    def measure(self, operation: str):
        """
        Context manager for measuring operation latency.
        
        Usage:
            with monitor.measure('adaptation'):
                # code to measure
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000  # ms
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(elapsed)
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        values = self.metrics[operation]
        return {
            'count': len(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'p50': sorted(values)[len(values) // 2],
            'p95': sorted(values)[int(len(values) * 0.95)],
            'p99': sorted(values)[int(len(values) * 0.99)]
        }
    
    def reset(self):
        """Clear all metrics."""
        self.metrics.clear()
