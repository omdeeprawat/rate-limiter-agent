from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi import FastAPI

from rate_limiter.config import settings
from rate_limiter.redis.bucket import RedisTokenBucket
from rate_limiter.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("REDIS_URL =", settings.redis_url)
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=30,
        socket_timeout=30,
        health_check_interval=30,
    )
    await redis_client.ping()
    print("Redis connection successful")
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