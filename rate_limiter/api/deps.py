from fastapi import Request
from rate_limiter.redis.bucket import RedisTokenBucket

def get_bucket(request: Request) -> RedisTokenBucket:
    return request.app.state.bucket