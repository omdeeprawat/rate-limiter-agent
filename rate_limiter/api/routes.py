import time
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from rate_limiter.redis.bucket import RedisTokenBucket
from rate_limiter.api.deps import get_bucket

router = APIRouter()

@router.get("/check_limit")
async def check_limit(
    client_id: str,
    bucket: RedisTokenBucket = Depends(get_bucket),
):
    result = await bucket.allow_request(client_id)

    headers = {
        "X-RateLimit-Limit":     str(bucket.max_tokens),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset":     str(result.next_refill_at),
    }

    if result.allowed:
        return JSONResponse({"status": "ALLOW"}, headers=headers)

    return JSONResponse(
        {"status": "DENY"},
        status_code=429,
        headers={
            **headers,
            "Retry-After": str(max(0, result.next_refill_at - int(time.time()))),
        },
    )

@router.post("/reset")
async def reset(
    client_id: str,
    bucket: RedisTokenBucket = Depends(get_bucket),
):
    await bucket.reset(client_id)
    return {"status": "reset", "client_id": client_id}