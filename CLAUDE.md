# CLAUDE.md

## Project Context
Building a multi-agent PM brainstorming system using LangGraph. I'm a data scientist learning agentic systems—NOT a backend engineer. Code must be simple enough for me to understand and modify.

## Code Philosophy: Simplicity Over "Proper"

### DO
- Write procedural, script-like code (like a Jupyter notebook converted to .py)
- Keep everything in as few files as possible—start with ONE file until I ask to split
- Simple classes are fine—one class with a few methods, clear __init__
- Inline code rather than abstracting into helpers prematurely
- Add comments explaining WHY, not just what
- Use print statements liberally for debugging—I want to see what's happening
- Hardcode values first, parameterize later when I ask

### DON'T
- Create abstract base classes, factories, inheritance hierarchies, or design patterns
- Build "scalable" folder structures with /src, /core, /utils, /services, etc.
- Add typing beyond basic type hints (no Generics, Protocols, TypeVars)
- Create config files, environment management, or dependency injection
- Build error handling infrastructure—simple try/except with print is fine
- Add logging frameworks—print() is fine for now
- Separate concerns into multiple files until I explicitly request it

### OOP Guidance
- ✅ A class with __init__, 2-3 methods, clear purpose → great
- ✅ Dataclass or TypedDict to hold structured data → great
- ❌ Abstract base class that other classes inherit from → too much
- ❌ Multiple levels of inheritance → too much
- ❌ Metaclasses, decorators that modify class behavior → too much
- ❌ "Manager", "Factory", "Handler", "Service" suffix classes → usually a sign of over-engineering

## File Structure (Keep It Flat)
```
pm-agents/
├── main.py          # Everything lives here to start
├── prompts.py       # Only when main.py gets crowded (300+ lines)
├── requirements.txt
├── claude.md
└── .env             # API keys only
```

## LangGraph Specific
- Use the simplest LangGraph patterns—StateGraph with typed dict
- No subgraphs, no complex routing logic, no persistence/checkpointing yet
- One agent = one function that takes state, calls LLM, returns updated state
- If I ask "how does X work?"—show me by adding print statements, not by explaining architecture

## When I Ask to Add Features
1. First: add it inline in main.py, even if messy
2. Only extract to separate file when I say "this is getting hard to read"
3. Never preemptively "clean up" or "refactor for scale"

## How to Explain Code to Me
- Use data science analogies (DataFrames, pipelines, transformations)
- "State" = like a dict you pass through a pandas pipeline
- "Node" = like a function in df.pipe()
- "Edge" = the order functions run in your pipeline

## My Background
- Comfortable: Python, functional programming, APIs, data pipelines, basic OOP
- Uncomfortable: OOP design patterns, backend architecture, async, deployment
- Learning: LangGraph, agentic systems, prompt engineering