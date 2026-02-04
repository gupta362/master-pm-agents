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
master-pm-agents/
├── src/
│   └── pm_agents/
│       ├── __init__.py       # Public API exports
│       ├── workflow.py       # Main orchestration + staged workflow functions
│       ├── coordinator.py    # Classification, refinement, soft guesses
│       ├── state.py          # State/data definitions
│       └── agents/           # Specialist agents
│           ├── __init__.py
│           ├── prioritization.py
│           ├── problem_space.py
│           ├── context_mapping.py
│           ├── constraints.py
│           └── solution_validation.py
├── docs/
│   └── ARCHITECTURE.md       # Detailed system documentation
├── app.py                    # Streamlit UI with staged workflow
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
```

```python
# Import from the package - staged workflow (recommended)
from pm_agents import (
    run_stage1_refinement,
    run_stage2_classification,
    run_stage3_soft_guesses,
    run_stage4_specialist,
)

# Import from the package - legacy (no checkpoints)
from pm_agents import run, run_streaming
```

## LangGraph Patterns

- Use `StateGraph` with a typed State (TypedDict)
- One agent = one module with:
  - `PROMPT`: The system prompt
  - `run_agent(input, llm)`: Returns full response
  - `stream_agent(input, llm)`: Yields tokens for streaming
- Keep coordinator logic separate from specialist agents
- Use conditional edges for routing decisions

## Human-in-the-Loop Workflow

The system uses a 4-stage workflow with user checkpoints:

```
Stage 1: Refinement     → User reviews/edits refined problem
Stage 2: Classification → User confirms or overrides agent routing
Stage 3: Soft Guesses   → User validates key assumptions
Stage 4: Specialist     → Stream analysis with confirmed context
```

Each stage is a generator function that yields results for the UI to display.
The workflow state persists across stages, allowing users to go back.

## Streamlit UI Patterns

- **View routing**: `current_view` controls chat vs documentation pages
- **Workflow stages**: `workflow_stage` tracks progress through checkpoints
- **Session state**: All workflow data stored in `st.session_state`
- **Documentation pages**: Full-page docs for each agent (not just tooltips)

## When Adding Features

1. Determine if it's a new agent or modification to existing
2. For new agents: create a new file in `agents/`, export in `__init__.py`
3. For workflow changes: modify `workflow.py`
4. For coordinator changes (refinement, classification, soft guesses): modify `coordinator.py`
5. For UI changes: modify `app.py`
6. For new documentation pages: add `show_doc_<agent>()` function in `app.py`
7. Update `__init__.py` exports if adding public API
8. Update `docs/ARCHITECTURE.md` for significant changes

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
