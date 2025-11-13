import asyncio
import time

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int, per_seconds: int = 60):
        """
        Args:
            rate: Number of requests allowed
            per_seconds: Time window in seconds
        """
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self.lock:
            while self.tokens <= 0:
                self._add_tokens()
                if self.tokens <= 0:
                    sleep_time = self.per_seconds / self.rate
                    await asyncio.sleep(sleep_time)
            
            self.tokens -= 1
    
    def _add_tokens(self):
        """Add tokens based on elapsed time"""
        now = time.monotonic()
        elapsed = now - self.updated_at
        new_tokens = elapsed * (self.rate / self.per_seconds)
        
        self.tokens = min(self.rate, self.tokens + new_tokens)
        self.updated_at = now