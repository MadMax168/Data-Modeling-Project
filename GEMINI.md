# Workspace Mandates

## Python Execution
- **Main Runner:** Always use `uv` as the primary Python runner.
- **Commands:** Execute Python scripts using either `uv run <script>` or the absolute path to the project's virtual environment: `c:\Users\Gunte\Workspace\Workspace\fork\Data-Modeling-Project\.venv\Scripts\python.exe`.
- **Dependency Management:** Dependency updates, installations, and `pyproject.toml`/`uv.lock` modifications are strictly **user tasks**. Gemini CLI must not attempt to update or manage project dependencies unless explicitly directed by the user for a specific task.
