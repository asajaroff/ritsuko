"""
Rate limiter implementation using token bucket algorithm.

This module provides a thread-safe rate limiter to prevent API quota exhaustion
and manage concurrent requests to external APIs like Claude.
"""

import logging
import threading
import time
from collections import deque
from typing import Deque


class RateLimiter:
    """
    Token bucket rate limiter for controlling API request rates.

    This implementation uses the token bucket algorithm to allow bursts
    while maintaining a steady average rate.
    """

    def __init__(self, requests_per_minute: int = 50, burst_size: int = 10):
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum number of requests allowed per minute
            burst_size: Maximum number of requests that can be made in a burst
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size

        # Token bucket state
        self.tokens = float(burst_size)
        self.max_tokens = float(burst_size)
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.last_refill = time.time()

        # Thread safety
        self.lock = threading.Lock()

        # Queue for waiting requests
        self.queue: Deque[float] = deque()
        self.queue_max_size = 100  # Prevent unbounded queue growth

        # Metrics
        self.total_requests = 0
        self.total_queued = 0
        self.total_rejected = 0

        logging.info(
            f"RateLimiter initialized: {requests_per_minute} requests/min, "
            f"burst size: {burst_size}"
        )

    def _refill_tokens(self):
        """Refill tokens based on elapsed time since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now

    def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire permission to make a request.

        This method blocks until a token is available or the timeout expires.

        Args:
            timeout: Maximum time to wait in seconds (default: 30s)

        Returns:
            True if permission granted, False if timeout or queue full
        """
        start_time = time.time()

        with self.lock:
            # Check if queue is full
            if len(self.queue) >= self.queue_max_size:
                self.total_rejected += 1
                logging.warning(
                    f"Rate limiter queue full ({self.queue_max_size}), "
                    "rejecting request"
                )
                return False

            self._refill_tokens()

            # If we have tokens, grant immediately
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                self.total_requests += 1
                return True

            # Otherwise, we need to wait
            self.total_queued += 1
            logging.debug(f"Request queued, current queue size: {len(self.queue) + 1}")

        # Wait for tokens to become available (with timeout)
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logging.warning(
                    f"Request timed out after {timeout}s waiting for rate limit"
                )
                return False

            # Sleep for a short time then check again
            time.sleep(0.1)

            with self.lock:
                self._refill_tokens()
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    self.total_requests += 1
                    return True

    def try_acquire(self) -> bool:
        """
        Try to acquire permission without waiting.

        Returns:
            True if permission granted immediately, False otherwise
        """
        with self.lock:
            self._refill_tokens()

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                self.total_requests += 1
                return True

            return False

    def get_metrics(self) -> dict:
        """
        Get current rate limiter metrics.

        Returns:
            Dictionary with metrics:
            - available_tokens: Current number of available tokens
            - total_requests: Total requests processed
            - total_queued: Total requests that had to wait
            - total_rejected: Total requests rejected due to queue full
            - queue_size: Current queue size
        """
        with self.lock:
            self._refill_tokens()
            return {
                "available_tokens": round(self.tokens, 2),
                "total_requests": self.total_requests,
                "total_queued": self.total_queued,
                "total_rejected": self.total_rejected,
                "queue_size": len(self.queue),
                "requests_per_minute": self.requests_per_minute,
                "burst_size": self.burst_size,
            }

    def reset_metrics(self):
        """Reset metrics counters (but keep rate limiting state)."""
        with self.lock:
            self.total_requests = 0
            self.total_queued = 0
            self.total_rejected = 0
            logging.info("Rate limiter metrics reset")


# Global rate limiter instance for Claude API
# Anthropic recommends 50 requests per minute for production use
claude_rate_limiter = RateLimiter(requests_per_minute=50, burst_size=10)
