from pydantic import BaseModel
from typing import Literal
from agent.graph.state import AgentState
from agent.config import agent_settings
from langchain_groq import ChatGroq
from agent.prompts.validator import VALIDATOR_HUMAN, VALIDATOR_SYSTEM
import os

class ValidatorOutput(BaseModel):
  result: Literal['approved', 'needs_revision']
  feedback:str
  issues: list[str]


def validator_node(state: AgentState ) -> dict:
  middleware_code = state.get('generated_middleware', "")
  test_code = state.get('generated_tests', "")

  if not middleware_code or not test_code:
    return {
      "validation_result": "needs_revision",
      "validation_feedback": "One or more sections (middleware_code, test_code) were empty. Regenerate all three sections with proper XML tags.",
    }
    
  llm = ChatGroq(
    model=agent_settings.groq_model,
    api_key=agent_settings.groq_api_key,
    temperature=0,
  )

  review: ValidatorOutput = llm.with_structured_output(ValidatorOutput).invoke([
    {'role': 'system', 'content': VALIDATOR_SYSTEM},
    {'role': 'user', 'content': VALIDATOR_HUMAN.format(
      middleware_code=middleware_code,
      test_code=test_code,
    )},
  ])

  print(f"✓ Validator: {review.result}")
  for issue in review.issues:
    print(f"  ✗ {issue}")

  if review.result == "approved":
    _write_files(state, middleware_code, test_code)

  return {
    'validation_result': review.result,
    'validation_feedback': review.feedback if review.result == 'needs_revision' else '',
  }


def _write_files(state: AgentState, middleware_code: str, test_code: str) -> None:
  target = state['target_path']
  context = state['project_context']
  modified_main = state.get('modified_main', '')

  write_file.invoke({
    "path": os.path.join(target, 'rate_limit_middleware.py'),
    "content": middleware_code
  })
  write_file.invoke({
    'path': os.path.join(target, 'test_rate_limit.py'),
    'content': test_code
  })
  if modified_main:
    write_file.invoke({
      'path': os.path.join(target, context.main_file),
      'content': modified_main
    })

  print(f"  → rate_limit_middleware.py")
  print(f"  → test_rate_limit.py")
  print(f"  → {context.main_file} (modified)")


def route_on_validation(state: AgentState) -> str:
  if state['validation_result'] == 'approved':
    return 'approved'
  if state.get('revision_count', 0) >= agent_settings.max_revisions:
    print(f"⚠ Max revisions reached — forcing exit")
    return 'approved'
  return 'needs_revision'