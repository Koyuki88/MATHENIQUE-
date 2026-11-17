import os
import time
from collections import deque
from threading import Lock
from fastapi import HTTPException, Request, status


_TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"


def get_client_ip(request: Request) -> str:
    """Return the client IP, honoring X-Forwarded-For only when behind a trusted proxy."""
    if _TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # First IP in X-Forwarded-For is the originating client as seen by the edge proxy
            client_ip = forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter with bounded bucket growth."""

    def __init__(self, max_buckets: int = 10000) -> None:
        self._buckets: dict[str, deque[float]] = {}
        self._lock = Lock()
        self._max_buckets = max_buckets

    def _evict_stale(self, now: float, max_window: int) -> None:
        cutoff = now - max_window
        stale_keys = [
            key
            for key, timestamps in self._buckets.items()
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for key in stale_keys:
            del self._buckets[key]

        # Hard cap fallback in case of high-cardinality flood
        while len(self._buckets) >= self._max_buckets:
            oldest_key = next(iter(self._buckets))
            del self._buckets[oldest_key]

    def hit(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds

        with self._lock:
            if len(self._buckets) >= self._max_buckets and key not in self._buckets:
                self._evict_stale(now, window_seconds)

            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = deque()
                self._buckets[key] = bucket

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= max_requests:
                retry_after = max(1, int(bucket[0] + window_seconds - now) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please slow down and try again shortly.",
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)


rate_limiter = SlidingWindowRateLimiter()


def rate_limit(scope: str, max_requests: int, window_seconds: int):
    """FastAPI dependency enforcing a per-IP sliding-window rate limit."""

    def _dependency(request: Request) -> None:
        client_ip = get_client_ip(request)
        rate_limiter.hit(f"{scope}:ip:{client_ip}", max_requests, window_seconds)

    return _dependency
