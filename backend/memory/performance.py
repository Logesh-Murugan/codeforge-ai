"""
PerformanceMonitor — Phase 3.6 Production Hardening

Lightweight instrumentation for the memory subsystem.

Features
--------
- ``@timed`` decorator — records latency for any callable
- ``record()`` — manually push a timing sample
- ``slow_queries()`` — list operations that exceeded a threshold
- ``throughput()`` — operations per second for a given operation name
- ``summary()`` — aggregated stats dict (count, min, max, mean, p95)
- ``reset()`` — clear all collected samples

Usage
-----
    monitor = PerformanceMonitor(slow_threshold_ms=200)

    # Decorate a function:
    @monitor.timed("embed_query")
    def my_embed(text):
        ...

    # Or wrap a call manually:
    with monitor.measure("retrieve_memory"):
        results = svc.retrieve_memory(...)

    # Inspect:
    print(monitor.summary("retrieve_memory"))
    slow = monitor.slow_queries(threshold_ms=500)
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_SLOW_THRESHOLD_MS = 200.0


class PerformanceMonitor:
    """
    Collects timing samples and reports performance metrics.

    Args:
        slow_threshold_ms: Samples above this value (in ms) are flagged
                           as slow queries.
    """

    def __init__(self, slow_threshold_ms: float = _DEFAULT_SLOW_THRESHOLD_MS) -> None:
        self.slow_threshold_ms = slow_threshold_ms
        # operation_name → list of durations in milliseconds
        self._samples: Dict[str, List[float]] = defaultdict(list)
        # Slow query log: list of {operation, duration_ms, timestamp}
        self._slow_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Manual instrumentation
    # ------------------------------------------------------------------

    def record(self, operation: str, duration_ms: float) -> None:
        """Push a single timing sample (in milliseconds)."""
        self._samples[operation].append(duration_ms)
        if duration_ms >= self.slow_threshold_ms:
            entry = {
                "operation": operation,
                "duration_ms": round(duration_ms, 3),
                "timestamp": time.time(),
            }
            self._slow_log.append(entry)
            logger.warning(
                "[PERF] Slow operation '%s': %.1f ms (threshold: %.1f ms)",
                operation, duration_ms, self.slow_threshold_ms,
            )

    @contextmanager
    def measure(self, operation: str) -> Generator[None, None, None]:
        """
        Context manager that records the wall-clock time of the block.

        Example::

            with monitor.measure("store_memory"):
                svc.store_memory(...)
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.record(operation, elapsed_ms)

    def timed(self, operation: str) -> Callable:
        """
        Decorator that records the latency of the wrapped function.

        Example::

            @monitor.timed("embed_query")
            def embed(text):
                ...
        """
        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    return fn(*args, **kwargs)
                finally:
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    self.record(operation, elapsed_ms)
            return wrapper
        return decorator

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def summary(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Return aggregated stats for *operation* (or all operations).

        Stats per operation: count, min_ms, max_ms, mean_ms, p95_ms.

        Returns:
            If ``operation`` is given: a single stats dict.
            Otherwise: a dict keyed by operation name.
        """
        if operation:
            return self._op_stats(operation, self._samples.get(operation, []))

        return {
            op: self._op_stats(op, samples)
            for op, samples in self._samples.items()
        }

    @staticmethod
    def _op_stats(operation: str, samples: List[float]) -> Dict[str, Any]:
        if not samples:
            return {
                "operation": operation,
                "count": 0,
                "min_ms": None,
                "max_ms": None,
                "mean_ms": None,
                "p95_ms": None,
            }
        sorted_s = sorted(samples)
        n = len(sorted_s)
        p95_idx = max(0, int(n * 0.95) - 1)
        return {
            "operation": operation,
            "count": n,
            "min_ms": round(sorted_s[0], 3),
            "max_ms": round(sorted_s[-1], 3),
            "mean_ms": round(sum(sorted_s) / n, 3),
            "p95_ms": round(sorted_s[p95_idx], 3),
        }

    def slow_queries(
        self,
        threshold_ms: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Return slow operations, optionally filtered by a custom threshold.

        Returns:
            Most recent *limit* slow operations, newest first.
        """
        effective = threshold_ms if threshold_ms is not None else self.slow_threshold_ms
        filtered = [e for e in self._slow_log if e["duration_ms"] >= effective]
        # newest first
        return sorted(filtered, key=lambda e: e["timestamp"], reverse=True)[:limit]

    def throughput(self, operation: str, window_seconds: float = 60.0) -> float:
        """
        Estimate operations-per-second for *operation* over a time window.

        Args:
            operation:      The operation name to measure.
            window_seconds: How many seconds of history to consider.

        Returns:
            Approximate ops/sec (float).
        """
        samples = self._samples.get(operation, [])
        if not samples:
            return 0.0
        # Throughput = number of ops / total elapsed time (seconds)
        # Use mean duration as a proxy for total time
        mean_ms = sum(samples) / len(samples)
        if mean_ms <= 0:
            return 0.0
        # ops per second if each op took mean_ms
        return 1000.0 / mean_ms

    def operation_names(self) -> List[str]:
        """Return a sorted list of all recorded operation names."""
        return sorted(self._samples.keys())

    def reset(self, operation: Optional[str] = None) -> None:
        """
        Clear collected samples.

        Args:
            operation: If given, clear only that operation's samples.
                       Otherwise, clear everything.
        """
        if operation:
            self._samples.pop(operation, None)
            self._slow_log = [e for e in self._slow_log if e["operation"] != operation]
        else:
            self._samples.clear()
            self._slow_log.clear()
