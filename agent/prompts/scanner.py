SCANNER_SYSTEM = """You are a code analysis expert specializing in Python FastAPI projects.
Analyze the given project structure and file contents to extract accurate metadata.
Only report information explicitly present in the files. Do not infer or assume."""

SCANNER_HUMAN = """Analyze this FastAPI project and extract its structure.

Project root: {target_path}

Directory listing:
{directory_listing}

File contents:
{file_contents}

Extract:
- framework: the web framework used (should be "fastapi")
- main_file: relative path to the file that creates the FastAPI() instance
- routes_files: list of relative paths to files containing route definitions
- has_existing_middleware: true only if app.add_middleware() already exists
- route_summary: each route as "METHOD /path" e.g. ["GET /weather", "GET /news"]"""