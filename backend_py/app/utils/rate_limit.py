import asyncio
import random
import time


class RateLimiter:
    def __init__(self, min_interval_ms: int = 1200, jitter_ms: int = 400):
        self._min = min_interval_ms / 1000.0
        self._jitter = jitter_ms / 1000.0
        self._last = 0.0

    async def wait(self) -> None:
        now = time.time()
        elapsed = now - self._last
        delay = self._min - elapsed
        if delay > 0:
            delay += random.random() * self._jitter
            await asyncio.sleep(delay)
        self._last = time.time()
