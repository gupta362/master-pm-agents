# PM Brainstorming Assistant

A multi-agent system that helps Product Managers think through problems using AI-powered specialist agents.

## What This Does

As a PM, you face different types of challenges that require different thinking approaches:

| Category | When to Use | Example |
|----------|-------------|---------|
| **Prioritization** | Choosing between options, ranking, trade-offs | "Should we build A or B first?" |
| **Problem Space** | Validating if a problem exists and matters | "I think users struggle with X, but not sure if it's real" |
| **Context Mapping** | Learning new domains, stakeholders, organizations | "Just joined the team, need to learn this space" |
| **Constraints** | Surfacing hidden blockers and limitations | "Engineering says 'won't work' but I don't know why" |
| **Solution Validation** | Validating if a solution idea is viable | "Want to build X. Is this a good idea?" |

This tool automatically detects which type of problem you're facing and routes you to a specialist agent:

```
Your Problem → Coordinator (classifies) → Prioritization Agent
                                        → Problem Space Agent
                                        → Context Mapping Agent
                                        → Constraints Agent
                                        → Solution Validation Agent
```

The **Coordinator** explains its reasoning, so you understand why it chose a particular path. Then the **Specialist Agent** gives you a structured, actionable response tailored to your specific situation.

## Features

- **Automatic problem classification** with transparent reasoning (5 categories)
- **Prioritization Agent**: Applies frameworks like RICE, MoSCoW, Value vs Effort with markdown tables
- **Problem Space Agent**: Validates if problems exist and matter, with soft guesses marked ⚠️
- **Context Mapping Agent**: Maps domains, stakeholders, and organizational dynamics
- **Constraints Agent**: Surfaces hidden technical, organizational, and external limitations
- **Solution Validation Agent**: Validates solutions against 4 risks (value, usability, feasibility, viability)
- **Generative behavior**: Agents make educated guesses and proceed with analysis instead of blocking
- **Validation questions**: Every agent ends with "Questions for Your Next Stakeholder Meeting"
- **Streamlit chat UI** with real-time streaming responses
- **Terminal logging** for debugging (all print statements go to terminal, not UI)

## Setup

### Prerequisites
- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- Anthropic API key

### Installation

```bash
# Clone the repo
git clone https://github.com/gupta362/master-pm-agents.git
cd master-pm-agents

# Install dependencies and package
uv sync

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

## How to Run

### Streamlit UI (Recommended)

```bash
uv run streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Python API

```python
from pm_agents import run, run_streaming

# Run with full response
result = run("Help me prioritize these three features...")

# Run with streaming (for UIs)
for event_type, data in run_streaming("Help me prioritize..."):
    if event_type == "coordinator":
        print(f"Classification: {data['classification']}")
    elif event_type == "token":
        print(data, end="")
```

## Example Usage

**Prioritization problem:**
> "You're building a new feature with limited engineering resources. Your CEO wants Feature A (high visibility), your biggest customer wants Feature B (threatens churn), and your data shows Feature C has the highest usage potential. Walk me through how you'd decide."

→ Routes to **Prioritization Agent** (RICE framework, comparison table, recommendation)

**Problem space validation:**
> "I think our users struggle with onboarding, but I'm not sure if it's actually a problem or just my assumption. Should we invest in improving it?"

→ Routes to **Problem Space Agent** (evidence analysis, soft guesses with ⚠️, validation questions)

**Context mapping:**
> "I just joined the team as PM for the payments domain. I have 2 weeks before my first stakeholder meeting. What do I need to learn?"

→ Routes to **Context Mapping Agent** (stakeholder map, domain concepts, learning roadmap)

**Constraints discovery:**
> "Engineering keeps pushing back on my feature requests saying 'it's not that simple' but they can't explain why. Help me understand what's blocking us."

→ Routes to **Constraints Agent** (technical/org/external constraints, severity matrix)

**Solution validation:**
> "I want to build an AI-powered search feature for our app. Is this a good idea?"

→ Routes to **Solution Validation Agent** (4-risks analysis: value, usability, feasibility, viability)

## Project Structure

```
master-pm-agents/
├── src/
│   └── pm_agents/
│       ├── __init__.py              # Public API exports
│       ├── workflow.py              # LangGraph orchestration
│       ├── coordinator.py           # Problem classification (5 categories)
│       ├── state.py                 # State definitions
│       └── agents/
│           ├── __init__.py
│           ├── prioritization.py    # Trade-offs and ranking
│           ├── problem_space.py     # Problem validation
│           ├── context_mapping.py   # Domain/stakeholder mapping
│           ├── constraints.py       # Hidden limitations
│           └── solution_validation.py  # 4-risks validation
├── docs/
│   └── ARCHITECTURE.md              # Detailed system documentation
├── app.py                           # Streamlit chat UI
├── pyproject.toml                   # Package config
├── spec.md                          # Detailed specifications
└── .env                             # Your ANTHROPIC_API_KEY
```

## Tech Stack

- **LangGraph** - Agent orchestration and state management
- **LangChain + Anthropic** - LLM calls to Claude
- **Streamlit** - Chat UI with streaming support
- **uv** - Fast Python package manager
- **Hatch** - Python build backend
