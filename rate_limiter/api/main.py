from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi import FastAPI

from rate_limiter.config import settings
from rate_limiter.redis.bucket import RedisTokenBucket
from rate_limiter.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    app.state.bucket = RedisTokenBucket(
        redis_client=redis_client,
        max_tokens=settings.max_tokens,
        refill_rate=settings.refill_rate,
        interval=settings.interval,
        ttl=settings.key_ttl,
    )
    yield
    await redis_client.aclose()


app = FastAPI(title="Token Bucket Rate Limiter", lifespan=lifespan)
app.include_router(router)