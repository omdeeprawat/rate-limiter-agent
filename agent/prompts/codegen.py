CODEGEN_SYSTEM = """You are a backend code generation expert specializing in FastAPI middleware.

The Rate Limiter Service runs separately and exposes:
  GET /check_limit?client_id=<string>
  Returns: {{"status": "ALLOW"}} or {{"status": "DENY"}}
  Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After

Generate exactly three sections wrapped in XML tags:

<middleware_code>  
full contents of rate_limit_middleware.py:
  - Class RateLimitMiddleware extending BaseHTTPMiddleware
  - Extract client_id from request.client.host
  - Call rate limiter with httpx.AsyncClient (async, inside async with block)
  - On DENY: return 429 JSONResponse with all X-RateLimit-* and Retry-After headers
  - On ALLOW: call await call_next(request), forward X-RateLimit-* headers onto response
  - Full imports, type hints, no placeholders
</middleware_code>

<test_code>  
full contents of test_rate_limit.py:
  - Build a minimal FastAPI test app with RateLimitMiddleware attached
  - Use pytest and httpx.AsyncClient with anyio backend
  - Test: first {max_tokens} requests return 200
  - Test: request {max_tokens_plus_one} returns 429
  - Test: X-RateLimit-Remaining decrements correctly
  - Test: X-RateLimit-Limit header is present on every response
  - All tests must pass with: pytest test_rate_limit.py -v
</test_code>

<modified_main> 
the complete modified contents of main.py:
  - Add: from rate_limit_middleware import RateLimitMiddleware
  - Add: app.add_middleware(RateLimitMiddleware) immediately after app = FastAPI(...)
  - Keep every other line exactly as it was
  - Do not add comments or change formatting

</modified_main>
Output ONLY the three tagged sections. No explanation, no prose, no markdown outside the tags."""

CODEGEN_HUMAN = """Generate rate limiting integration for this FastAPI project.

Rate Limiter URL: {rate_limiter_url}
Bucket capacity: {max_tokens}

Project context:
  main_file         : {main_file}
  routes_files      : {routes_files}
  routes            : {route_summary}
  existing middleware: {has_existing_middleware}

Current main.py contents:
{main_file_content}

{revision_context}"""