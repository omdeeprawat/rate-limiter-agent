import httpx
from langchain_core.tools import tool
from agent.config import agent_settings

@tool
def check_rate_limiter_running() -> str:
  """
  Ping the Rate Limiter Service to verify it is running.
  Returns OK if reachable, ERROR if not.
  """
  try:
    response = httpx.get(
      f"{agent_settings.rate_limiter_url}/check_limit",
      params={"client_id": "agent-health-check"},
      timeout=3.0,
    )
    if response.status_code in (200, 429):
      return f"OK: Rate Limiter running at {agent_settings.rate_limiter_url}"
    return f"WARN: unexpected status {response.status_code}"
  except httpx.ConnectError:
    return (
      f"ERROR: cannot reach Rate Limiter at {agent_settings.rate_limiter_url}. "
      "Run: docker compose up"
    )
  except Exception as e:
    return f"ERROR: {e}"