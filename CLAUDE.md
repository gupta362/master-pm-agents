# CLAUDE.md

## Project Context
Building a multi-agent PM brainstorming system using LangGraph. I'm a data scientist comfortable with Python who is learning agentic systems and software engineering best practices.

## Code Philosophy: Clarity and Maintainability

### Guiding Principles
- Write clear, readable code that's easy to understand and modify
- Use standard Python packaging conventions
- Keep functions focused—one function, one job
- Add comments explaining WHY, not just what
- Use print statements for debugging during development
- Prefer explicit over implicit

### DO
- Use `src/` layout for Python packages
- Organize related code into modules and subpackages
- Use type hints for function signatures
- Write docstrings for modules, classes, and public functions
- Use dataclasses or TypedDict for structured data
- Keep business logic separate from I/O (LLM calls, file operations)

### DON'T
- Over-engineer with abstract base classes or design patterns unless genuinely needed
- Add frameworks (logging, config management) before they're necessary
- Create deep inheritance hierarchies
- Use "Manager", "Factory", "Handler" suffix classes prematurely
- Add async unless there's a clear performance need

## Project Structure

```
project-name/
├── src/
│   └── package_name/
│       ├── __init__.py       # Public API exports
│       ├── workflow.py       # Main orchestration logic
│       ├── state.py          # State/data definitions
│       └── agents/           # Subpackage for agents
│           ├── __init__.py
│           └── agent_name.py
├── app.py                    # UI/CLI entry point (root level)
├── pyproject.toml            # Package config and dependencies
├── README.md
├── CLAUDE.md
└── .env                      # API keys (gitignored)
```

## Package Configuration

Use modern Python packaging with `pyproject.toml`:

```toml
[project]
name = "package-name"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [...]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/package_name"]
```

## Development Workflow

```bash
# Install dependencies and package in editable mode
uv sync

# Run the Streamlit app
uv run streamlit run app.py

# Run tests (when added)
uv run pytest

# Import from the package
from package_name import run, run_streaming
```

## LangGraph Patterns

- Use `StateGraph` with a typed State (TypedDict)
- One agent = one module with:
  - `PROMPT`: The system prompt
  - `run_agent(input, llm)`: Returns full response
  - `stream_agent(input, llm)`: Yields tokens for streaming
- Keep coordinator logic separate from specialist agents
- Use conditional edges for routing decisions

## When Adding Features

1. Determine if it's a new agent or modification to existing
2. For new agents: create a new file in `agents/`, export in `__init__.py`
3. For workflow changes: modify `workflow.py`
4. For UI changes: modify `app.py`
5. Update `__init__.py` exports if adding public API

## How to Explain Code to Me
- Use data science analogies where helpful
- "State" = like a dict passed through a pipeline
- "Node" = like a function in df.pipe()
- "Edge" = the order functions run in your pipeline
- Show me with code examples, not just descriptions

## My Background
- Comfortable: Python, functional programming, APIs, data pipelines, basic OOP
- Learning: Software engineering practices, LangGraph, agentic systems, prompt engineering
- Prefer: Practical examples over theoretical explanations
