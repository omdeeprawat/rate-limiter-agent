import os
from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
  """read the full contents of a file and returns the file content as string"""
  try:
    with open(path, "r", encoding="utf-8") as f:
      return f.read()
  except FileNotFoundError:
    return f"ERROR: file not found: {path}"
  except Exception as e:
    return f"ERROR: {e}"


@tool
def write_file(path: str, content: str) -> str:
  """write content to a file and creates parent directories if they do not exist"""
  try:
    parent = os.path.dirname(path)
    if parent:
      os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
      f.write(content)
    return f"OK: wrote {len(content)} chars to {path}"
  except Exception as e:
    return f"ERROR: {e}"


@tool
def list_directory(path: str) -> str:
  """recursively list all files under a directory, skipping hidden files and __pycache__"""
  try:
    result = []
    for root, dirs, files in os.walk(path):
      dirs[:] = [
        d for d in dirs
        if not d.startswith(".") and d != "__pycache__"
      ]
      level = root.replace(path, "").count(os.sep)
      indent = "  " * level
      result.append(f"{indent}{os.path.basename(root)}/")
      subindent = "  " * (level + 1)
      for file in files:
        if not file.startswith(".") and not file.endswith(".pyc"):
          result.append(f"{subindent}{file}")
    return "\n".join(result)
  except Exception as e:
    return f"ERROR: {e}"