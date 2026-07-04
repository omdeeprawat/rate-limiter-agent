import time
import redis.asyncio as aioredis
from dataclasses import dataclass
from rate_limiter.redis.scripts import RATE_LIMIT_SCRIPT

@dataclass
class BucketResult:
    allowed: bool
    remaining: int
    next_refill_at: int  


class RedisTokenBucket:
    """
    one instance handles all clients via Redis keys.
    """

    def __init__(
        self,
        redis_client,
        max_tokens: int,
        refill_rate: int,
        interval: float,
        ttl: int = 3600,
    ):
        self._redis = redis_client
        self.max_tokens  = max_tokens
        self.refill_rate = refill_rate
        self.interval    = interval
        self.ttl         = ttl
        self._script     = redis_client.register_script(RATE_LIMIT_SCRIPT)

    async def allow_request(self, client_id: str, tokens: int = 1) -> BucketResult:
        """same signature as TokenBucket.allow_request()"""
        key = f"rate_limit:{client_id}"
        now = time.time()

        result = await self._script(
            keys=[key],
            args=[
                self.max_tokens,
                self.refill_rate,
                self.interval,
                now,
                tokens,
                self.ttl,
            ],
        )

        allowed, remaining, next_refill_at = result
        return BucketResult(
            allowed=bool(allowed),
            remaining=int(remaining),
            next_refill_at=int(next_refill_at),
        )

    async def reset(self, client_id: str) -> None:
        await self._redis.delete(f"rate_limit:{client_id}")