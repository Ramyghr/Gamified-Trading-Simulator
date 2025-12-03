"""
Async API client with rate limiting
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AsyncAPIClient:
    """Async HTTP client with rate limiting"""
    
    def __init__(self, base_url: str, rate_limit: int = 60):
        """
        Args:
            base_url: Base URL for API
            rate_limit: Max requests per minute
        """
        self.base_url = base_url.rstrip('/')
        self.rate_limit = rate_limit
        self.request_times = []
        self.lock = asyncio.Lock()
    
    async def _wait_for_rate_limit(self):
        """Wait if rate limit would be exceeded"""
        async with self.lock:
            now = datetime.now()
            
            # Remove requests older than 1 minute
            self.request_times = [
                t for t in self.request_times 
                if now - t < timedelta(minutes=1)
            ]
            
            # If at limit, wait until oldest request is > 1 min old
            if len(self.request_times) >= self.rate_limit:
                oldest = self.request_times[0]
                wait_time = 60 - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            
            self.request_times.append(now)
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ) -> Dict:
        """Make GET request with rate limiting"""
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise
    
    async def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ) -> Dict:
        """Make POST request with rate limiting"""
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url, 
                    data=data, 
                    json=json, 
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise