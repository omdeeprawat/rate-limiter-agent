from fastapi import FastAPI
from app.routes import router
from .rate_limit_middleware import RateLimitMiddleware

app = FastAPI(title="Demo App")
app.add_middleware(RateLimitMiddleware)
app.include_router(router)