import os
import argparse
from agent.graph.graph import compiled_graph


def main():
  parser = argparse.ArgumentParser(
    description="Autonomously injects rate limiting middleware into a FastAPI project"
  )
  parser.add_argument("--target", required=True, help="Path to target FastAPI project")
  args = parser.parse_args()

  target_path = os.path.abspath(args.target)

  if not os.path.isdir(target_path):
    print(f"❌ Not a directory: {target_path}")
    return

  print(f"🚀 Agent starting — target: {target_path}")
  print("─" * 60)

  result = compiled_graph.invoke({
    "target_path": target_path,
    "project_context": None,
    "main_file_content": None,
    "generated_middleware": None,
    "generated_tests": None,
    "modified_main": None,
    "validation_result": None,
    "validation_feedback": None,
    "revision_count": 0,
    "error": None,
  })

  print("─" * 60)

  if result.get("error"):
    print(f"❌ {result['error']}")
    return

  print(f"✅ Done — {result.get('revision_count', 1)} LLM pass(es)")
  print(f"\nNext steps:")
  print(f"  uvicorn app.main:app --port 8001 --reload")
  print(f"  pytest {target_path}/test_rate_limit.py -v")


if __name__ == "__main__":
    main()