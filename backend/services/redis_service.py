import redis
import time
from typing import Optional
from config import settings

class RedisService:
    def __init__(self):
        self.enabled = False
        self.client = None
        self._local_cache = {}  # In-memory cache fallback
        self._rate_limits = {}  # In-memory rate-limiter fallback
        
        redis_url = settings.REDIS_URL
        if redis_url:
            try:
                self.client = redis.from_url(redis_url, decode_responses=True)
                # Test connection via ping
                self.client.ping()
                self.enabled = True
                print("[REDIS] Connected to Redis server successfully.")
            except Exception as e:
                print(f"[REDIS WARNING] Failed to connect to Redis: {e}. Running with in-memory fallbacks.")
        else:
            print("[REDIS] REDIS_URL not configured. Running with in-memory fallbacks.")
                
    def get(self, key: str) -> Optional[str]:
        if self.enabled and self.client:
            try:
                return self.client.get(key)
            except Exception as e:
                print(f"[REDIS ERROR] get failed: {e}")
        return self._local_cache.get(key)

    def set(self, key: str, value: str, ex_seconds: int = 3600):
        if self.enabled and self.client:
            try:
                self.client.set(key, value, ex=ex_seconds)
                return
            except Exception as e:
                print(f"[REDIS ERROR] set failed: {e}")
        self._local_cache[key] = value

    def check_rate_limit(self, client_ip: str, limit: int = 10, window_seconds: int = 60) -> bool:
        """
        Check if a client IP is within rate limits. 
        Returns True if within limits, False if rate-limited.
        """
        key = f"ratelimit:{client_ip}"
        if self.enabled and self.client:
            try:
                pipeline = self.client.pipeline()
                pipeline.incr(key)
                # Set TTL only if count is 1 (first request in window)
                pipeline.expire(key, window_seconds)
                results = pipeline.execute()
                current_count = results[0]
                return current_count <= limit
            except Exception as e:
                print(f"[REDIS ERROR] Rate limit logic failed: {e}")
                
        # In-memory rate limiting fallback
        now = time.time()
        timestamps = self._rate_limits.get(client_ip, [])
        
        # Keep only timestamps within the current window
        timestamps = [t for t in timestamps if now - t < window_seconds]
        
        if len(timestamps) >= limit:
            return False
            
        timestamps.append(now)
        self._rate_limits[client_ip] = timestamps
        return True

redis_service = RedisService()
