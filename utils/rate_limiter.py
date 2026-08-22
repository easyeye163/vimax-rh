import asyncio
import logging
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """Token-bucket / sliding-window rate limiter for async API calls.

    Supports per-minute and per-day limits.  When either bucket is empty
    the caller blocks until a token becomes available.
    """

    def __init__(
        self,
        max_requests_per_minute: Optional[int] = None,
        max_requests_per_day: Optional[int] = None,
    ):
        self._rpm = max_requests_per_minute
        self._rpd = max_requests_per_day

        # sliding windows
        self._minute_window: deque = deque()
        self._day_window: deque = deque()

        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Block until a request token is available."""
        while True:
            async with self._lock:
                now = time.monotonic()

                # prune old entries
                if self._rpm is not None:
                    while self._minute_window and self._minute_window[0] < now - 60:
                        self._minute_window.popleft()
                if self._rpd is not None:
                    while self._day_window and self._day_window[0] < now - 86400:
                        self._day_window.popleft()

                rpm_ok = self._rpm is None or len(self._minute_window) < self._rpm
                rpd_ok = self._rpd is None or len(self._day_window) < self._rpd

                if rpm_ok and rpd_ok:
                    if self._rpm is not None:
                        self._minute_window.append(now)
                    if self._rpd is not None:
                        self._day_window.append(now)
                    return

                # calculate sleep time
                sleep_time = 1.0
                if self._rpm is not None and len(self._minute_window) >= self._rpm:
                    oldest = self._minute_window[0]
                    sleep_time = max(sleep_time, 60 - (now - oldest) + 0.1)
                if self._rpd is not None and len(self._day_window) >= self._rpd:
                    oldest = self._day_window[0]
                    sleep_time = max(sleep_time, 86400 - (now - oldest) + 0.1)

            logging.debug(f"Rate limit reached, sleeping {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)
