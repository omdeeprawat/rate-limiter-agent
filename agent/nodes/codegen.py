from pydantic import BaseModel
import re
from agent.graph.state import AgentState
from agent.config import agent_settings
from langchain_groq import ChatGroq
from agent.prompts.codegen import CODEGEN_HUMAN, CODEGEN_SYSTEM


# class CodeGenOutput(BaseModel):
#   middleware_code : str
#   test_code:str
#   modified_main: str

def _extract_tag(text: str, tag:str)->str:
  """extract content between <tag>...</tag>, stripping any markdown fences inside"""
  pattern = rf"<{tag}>(.*?)</{tag}>"
  match = re.search(pattern, text, re.DOTALL)
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

  revision_context = ""
  if revision_count > 0 and feedback:
    revision_context = (
      f"REVISION #{revision_count} — fix these issues from the previous attempt:\n"
      f"{feedback}\n\n"
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
    {"role": "system", "content": CODEGEN_SYSTEM.format(
      max_tokens=10,
      max_tokens_plus_one=11,
    )},
    {"role": "user", "content": CODEGEN_HUMAN.format(
      rate_limiter_url=agent_settings.rate_limiter_url,
      max_tokens=10,
      max_tokens_plus_one=11,
      main_file=context.main_file,
      routes_files=", ".join(context.routes_files),
      route_summary=", ".join(context.route_summary),
      has_existing_middleware=context.has_existing_middleware,
      main_file_content=state.get("main_file_content", ""),
      revision_context=revision_context,
    )},
  ])

  raw = response.content

  # middleware = _strip_fences(result.middleware_code)
  # tests = _strip_fences(result.test_code)
  # modified = _strip_fences(result.modified_main)
  middleware = _extract_tag(raw, "middleware_code")
  tests  = _extract_tag(raw, "test_code")
  modified = _extract_tag(raw, "modified_main")

  # surface missing sections early so validator can catch and retry
  missing = [
    name for name, val in [

      ("middleware_code", middleware),
      ("test_code", tests),
      ("modified_main", modified),
     ]
    if not val
    ]
  if missing:
    print(f"⚠ CodeGen: missing sections {missing} — Validator will request revision")


  print(f"✓ CodeGen: middleware {len(middleware)} chars · "
    f"tests {len(tests)} chars · "
    f"attempt {revision_count + 1}")

  return {
    "generated_middleware": middleware,
    "generated_tests": tests,
    "modified_main": modified,
    "revision_count": revision_count + 1,
}