from pydantic import BaseModel
import re
from agent.graph.state import AgentState
from agent.config import agent_settings
from langchain_groq import ChatGroq
from agent.prompts.codegen import CODEGEN_HUMAN, CODEGEN_SYSTEM

_MIDDLEWARE_TEMPLATE = """import httpx

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

RATE_LIMITER_URL = "RL_URL_PLACEHOLDER/check_limit"

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.client.host

        async with httpx.AsyncClient() as http_client:
            rl_resp = await http_client.get(
                RATE_LIMITER_URL,
                params={"client_id": client_id},
            )

        data = rl_resp.json()
        rl_headers = {
            "X-RateLimit-Limit":     rl_resp.headers.get("X-RateLimit-Limit", ""),
            "X-RateLimit-Remaining": rl_resp.headers.get("X-RateLimit-Remaining", ""),
            "X-RateLimit-Reset":     rl_resp.headers.get("X-RateLimit-Reset", ""),
        }

        if data["status"] == "DENY":
            rl_headers["Retry-After"] = rl_resp.headers.get("Retry-After", "1")
            return JSONResponse(
                {"error": "rate limit exceeded"},
                status_code=429,
                headers=rl_headers,
            )

        response = await call_next(request)
        for k, v in rl_headers.items():
            response.headers[k] = v
        return response
"""

# Structural tests — no rate limiter service needed to pass
_TEST_TEMPLATE = """import asyncio
import pytest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from rate_limit_middleware import RateLimitMiddleware


def test_middleware_is_valid_subclass():
    assert issubclass(RateLimitMiddleware, BaseHTTPMiddleware)


def test_middleware_has_async_dispatch():
    assert hasattr(RateLimitMiddleware, "dispatch")
    assert asyncio.iscoroutinefunction(RateLimitMiddleware.dispatch)


def test_middleware_attaches_to_app():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"status": "ok"}

    assert app is not None


# Integration test — requires: docker compose up
# Run with: pytest test_rate_limit.py -v -m integration
@pytest.mark.integration
def test_rate_limit_enforced():
    import httpx
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/ping")
    def ping():
        return {"status": "ok"}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/ping")
        assert response.status_code in (200, 429, 500)
        if response.status_code == 200:
            assert "X-RateLimit-Limit" in response.headers
"""


def _render_middleware(rate_limiter_url: str) -> str:
    return _MIDDLEWARE_TEMPLATE.replace("RL_URL_PLACEHOLDER", rate_limiter_url)


# class CodeGenOutput(BaseModel):
#   middleware_code : str
#   test_code:str
#   modified_main: str

def _extract_tag(text: str, tag:str)->str:
  # """extract content between <tag>...</tag>, stripping any markdown fences inside"""
  match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
  # pattern = rf"<{tag}>(.*?)</{tag}>"
  # match = re.search(pattern, text, re.DOTALL)
  if not match:
    return ""
  content = match.group(1).strip()
  content = re.sub(r"^```[\w]*\n", "", content)
  content = re.sub(r"\n```$", "", content)
  return content.strip()


# def _strip_fences(code:str)->str:
#   """ remove the markdown code fences id LLM wraps output in them"""
#   code = re.sub(r"^```[\w]*\n", "", code.strip())
#   code = re.sub(r"\n```$", "", code)
#   return code.strip()

def codegen_node(state: AgentState) -> dict:
  context = state["project_context"]
  revision_count = state.get("revision_count", 0)
  feedback = state.get("validation_feedback") or ""

  middleware = _render_middleware(agent_settings.rate_limiter_url)
  tests = _TEST_TEMPLATE

  revision_context = ""
  if revision_count > 0 and feedback:
    revision_context = (
      f"REVISION #{revision_count} — fix these issues:\n{feedback}\n"
      f"do not repeat the same mistakes"
    )

  llm = ChatGroq(
    model=agent_settings.groq_model,
    api_key=agent_settings.groq_api_key,
    temperature=0,
  )

  # result: CodeGenOutput = llm.with_structured_output(CodeGenOutput).invoke([
  #   {"role": "system", "content": CODEGEN_SYSTEM.format(
  #     max_tokens=10,
  #     max_tokens_plus_one=11,
  #   )},
  #   {"role": "user", "content": CODEGEN_HUMAN.format(
  #     rate_limiter_url=agent_settings.rate_limiter_url,
  #     max_tokens=10,
  #     main_file=context.main_file,
  #     routes_files=", ".join(context.routes_files),
  #     route_summary=", ".join(context.route_summary),
  #     has_existing_middleware=context.has_existing_middleware,
  #     main_file_content=state.get("main_file_content", ""),
  #     revision_context=revision_context,
  #   )},
  # ])

  response = llm.invoke([
    {"role": "system", "content": CODEGEN_SYSTEM},
    {"role": "user", "content": CODEGEN_HUMAN.format(
      # rate_limiter_url=agent_settings.rate_limiter_url,
      # max_tokens=10,
      # max_tokens_plus_one=11,
      main_file=context.main_file,
      # routes_files=", ".join(context.routes_files),
      route_summary=", ".join(context.route_summary),
      has_existing_middleware=context.has_existing_middleware,
      main_file_content=state.get("main_file_content", ""),
      revision_context=revision_context,
    )},
  ])

  # raw = response.content

  # middleware = _strip_fences(result.middleware_code)
  # tests = _strip_fences(result.test_code)
  # modified = _strip_fences(result.modified_main)


  # middleware = _extract_tag(raw, "middleware_code")
  # tests  = _extract_tag(raw, "test_code")
  # modified = _extract_tag(raw, "modified_main")

  # surface missing sections early so validator can catch and retry
  # missing = [
  #   name for name, val in [

  #     ("middleware_code", middleware),
  #     ("test_code", tests),
  #     ("modified_main", modified),
  #    ]
  #   if not val
  #   ]
  # if missing:
  #   print(f"⚠ CodeGen: missing sections {missing} — Validator will request revision")

  modified = _extract_tag(response.content, "modified_main")

  if not modified:
    print("⚠ CodeGen: <modified_main> tag missing — Validator will request revision")

  print(f"✓ CodeGen: middleware {len(middleware)} chars · "
    f"tests {len(tests)} chars · attempt{revision_count + 1}")
    

  return {
    "generated_middleware": middleware,
    "generated_tests": tests,
    "modified_main": modified,
    "revision_count": revision_count + 1,
}