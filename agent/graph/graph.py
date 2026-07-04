from langgraph.graph import StateGraph, END
from agent.graph.state import AgentState
from agent.nodes.scanner import scanner_node
from agent.nodes.codegen import codegen_node
from agent.nodes.validator import validator_node, route_on_validation


def _route_after_scanner(state: AgentState) -> str:
  return "error" if state.get("error") else "codegen"


def build_graph():
  g = StateGraph(AgentState)

  g.add_node("scanner", scanner_node)
  g.add_node("codegen", codegen_node)
  g.add_node("validator", validator_node)

  g.set_entry_point("scanner")

  g.add_conditional_edges(
    "scanner",
    _route_after_scanner,
    {"codegen": "codegen", "error": END},
  )
  g.add_edge("codegen", "validator")
  g.add_conditional_edges(
    "validator",
    route_on_validation,
    {"approved": END, "needs_revision": "codegen"}
  )

  return g.compile()


compiled_graph = build_graph()