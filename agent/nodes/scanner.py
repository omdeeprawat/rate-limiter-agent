from agent.graph.state import AgentState, ProjectContext
from agent.tools.health import check_rate_limiter_running
from agent.tools.filesystem import list_directory, read_file, write_file
import os
from agent.config import agent_settings
from langchain_groq import ChatGroq
from agent.prompts.scanner import SCANNER_HUMAN, SCANNER_SYSTEM

def scanner_node(state: AgentState) -> dict:
  target_path = state['target_path']
  health  = check_rate_limiter_running.invoke({})
  if health.startswith('ERROR'):
    return {"error":health}

  directory_listing = list_directory.invoke({'path': target_path})
  file_sections = []

  main_path = os.path.join(target_path, 'main.py')
  if not os.path.exists(main_path):
    return {'error': f'main.py not found in the {target_path}'}

  main_content = read_file.invoke({"path": main_path})
  file_sections.append(f"=== main.py ===\n{main_content}")

  routes_path = os.path.join(target_path, 'routes.py')
  if os.path.exists(routes_path):
    routes_content = read_file.invoke({"path": routes_path})
    file_sections.append(f"=== routes.py ===\n{routes_content}")

  combined = "\n\n".join(file_sections)

  llm = ChatGroq(
    model=agent_settings.groq_model,
    api_key=agent_settings.groq_api_key,
    temperature=0,
  )

  context: ProjectContext = llm.with_structured_output(ProjectContext).invoke([
    {'role': 'system', 'content': SCANNER_SYSTEM},
    {'role': 'user', 'content': SCANNER_HUMAN.format(
      target_path=target_path,
      directory_listing=directory_listing,
      file_contents=combined,
    )},
  ])

  print(f"✓ Scanner: {context.framework} · {len(context.route_summary)} routes · "
    f"middleware={'yes' if context.has_existing_middleware else 'no'}")

  return {
    "project_context": context,
    "main_file_content": main_content,
  }