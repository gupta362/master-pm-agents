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

## LLM Configuration (Critical)

**Always set `max_tokens` explicitly when initializing LLM clients:**

```python
# BAD - will truncate agent outputs at ~1024 tokens
llm = ChatAnthropic(model="claude-sonnet-4-20250514")

# GOOD - allows complete multi-section responses (agents need 4,000-7,000 tokens)
llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=8192)
```

This was a real bug: agent outputs were being cut off mid-response because the default was too low.

## Agent Design: Generative Behavior

Agents should be **generative** (make progress) rather than **blocking** (asking questions without providing value):

**Blocking (bad):**
> "I need more information about your users before I can help."

**Generative (good):**
> "Based on your description, I'm assuming B2B enterprise users (⚠️ soft guess). Here's my analysis... **Must Validate:** Is this actually B2B enterprise or B2C?"

Pattern:
1. Make soft guesses where info is missing (mark with ⚠️)
2. Proceed with analysis using those guesses
3. Include "Must Validate" section listing assumptions to verify

## Extending State

When adding new fields to the workflow state:

```python
# state.py - add new fields with defaults
class State(TypedDict, total=False):
    user_input: str
    classification: str
    agent_output: str
    # New fields - use total=False so they're optional
    soft_guesses: list[str]          # Assumptions agent made
    validation_questions: list[str]   # Questions to verify assumptions
```

Always use `total=False` for new fields to avoid breaking existing code.

## Common Pitfalls (Learned the Hard Way)

| Issue | Symptom | Fix |
|-------|---------|-----|
| Output truncation | Response ends mid-sentence | Set `max_tokens=8192` on LLM |
| Agent too vague | "It depends..." responses | Add specific frameworks and required output sections to prompt |
| Wrong classification | Coordinator misroutes queries | Add classification alternatives, let user override |
| Missing context | Agent guesses wrong | Add human-in-the-loop checkpoints for assumption validation |
| Monolithic agent | Inconsistent quality | Split into specialized sub-agents with focused prompts |

## When Adding Features

1. Determine if it's a new agent or modification to existing
2. For new agents: create a new file in `agents/`, export in `__init__.py`
3. For workflow changes: modify `workflow.py`
4. For UI changes: modify `app.py`
5. Update `__init__.py` exports if adding public API
6. For new state fields: add to `state.py` with `total=False`

## Output Validation

Add validation to catch quality issues early:

```python
def validate_agent_output(output: str) -> bool:
    """Check agent output meets quality requirements."""
    issues = []

    # Check required sections exist
    required = ["Questions for Your Next Stakeholder Meeting", "Must Validate"]
    missing = [s for s in required if s not in output]
    if missing:
        issues.append(f"Missing sections: {missing}")

    # Check for vague language
    vague = ["it depends", "proceed with caution", "may or may not"]
    found = [p for p in vague if p in output.lower()]
    if found:
        issues.append(f"Vague language: {found}")

    if issues:
        print(f"OUTPUT WARNINGS: {issues}")
    return len(issues) == 0
```

Call this after agent runs to surface prompt issues early.

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
