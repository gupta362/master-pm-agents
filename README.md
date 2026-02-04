# PM Brainstorming Assistant

A multi-agent system that helps Product Managers think through problems using AI-powered specialist agents with human-in-the-loop validation.

## What This Does

As a PM, you face different types of challenges that require different thinking approaches:

| Category | When to Use | Example |
|----------|-------------|---------|
| **Prioritization** | Choosing between options, ranking, trade-offs | "Should we build A or B first?" |
| **Problem Space** | Validating if a problem exists and matters | "I think users struggle with X, but not sure if it's real" |
| **Context Mapping** | Learning new domains, stakeholders, organizations | "Just joined the team, need to learn this space" |
| **Constraints** | Surfacing hidden blockers and limitations | "Engineering says 'won't work' but I don't know why" |
| **Solution Validation** | Validating if a solution idea is viable | "Want to build X. Is this a good idea?" |

## How It Works

The system uses a **4-stage workflow with checkpoints** that keeps you in control:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   STAGE 1   │     │   STAGE 2   │     │   STAGE 3   │     │   STAGE 4   │
│ Refinement  │────▶│Classification│────▶│Soft Guesses │────▶│ Specialist  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  [Checkpoint]        [Checkpoint]        [Checkpoint]
  Review & edit       Confirm or          Validate
  refined problem     override routing    assumptions
```

1. **Refinement** - Makes your vague input specific and concrete. You can edit it.
2. **Classification** - Picks the best agent. You can override if you know better.
3. **Soft Guesses** - Surfaces assumptions. You validate what's correct/incorrect.
4. **Specialist** - Runs analysis with your confirmed context baked in.

## Features

### Human-in-the-Loop Workflow
- **3 checkpoints** where you review and validate before proceeding
- **Editable refinement** - fix the problem statement if the AI misunderstood
- **Override routing** - pick a different agent if you know better
- **Assumption validation** - confirm or correct what the AI guessed about your situation

### 5 Specialist Agents
- **Prioritization**: RICE scoring, MoSCoW, Value vs Effort matrices, weighted scoring
- **Problem Space**: Evidence analysis, severity assessment, validation experiments
- **Context Mapping**: Stakeholder maps, domain glossaries, learning roadmaps
- **Constraints**: Technical/org/external blockers, negotiability analysis
- **Solution Validation**: 4-risks framework (value, usability, feasibility, viability)

### In-App Documentation
- **Full-page documentation** for each agent (click agent name in sidebar)
- **Framework explanations** with examples, tables, and diagrams
- **Methodology breakdowns** so you understand what the agent does

### Developer Experience
- **Streamlit chat UI** with real-time streaming
- **Staged Python API** for building custom UIs
- **Terminal logging** for debugging

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
# Staged workflow (recommended) - gives you control at each step
from pm_agents import (
    run_stage1_refinement,
    run_stage2_classification,
    run_stage3_soft_guesses,
    run_stage4_specialist,
)

# Stage 1: Refine the problem
for event_type, data in run_stage1_refinement("I think users struggle with X"):
    if event_type == "refinement":
        refined = data["refined_statement"]  # User can edit this

# Stage 2: Classify
for event_type, data in run_stage2_classification(refined):
    if event_type == "classification":
        classification = data["classification"]
        alternatives = data["alternatives"]  # Other options user could pick

# Stage 3: Extract assumptions
for event_type, data in run_stage3_soft_guesses(refined, classification):
    if event_type == "soft_guesses":
        guesses = data  # User validates each one

# Stage 4: Run specialist with confirmed context
for event_type, data in run_stage4_specialist(refined, classification, confirmed_guesses):
    if event_type == "token":
        print(data, end="")  # Streaming output
```

```python
# Legacy API (no checkpoints) - for simple integrations
from pm_agents import run, run_streaming

result = run("Help me prioritize these three features...")
print(result["classification"])
print(result["agent_output"])
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
│       ├── workflow.py              # Staged workflow + LangGraph orchestration
│       ├── coordinator.py           # Refinement, classification, soft guesses
│       ├── state.py                 # State definitions
│       └── agents/
│           ├── __init__.py
│           ├── prioritization.py    # RICE, MoSCoW, weighted scoring
│           ├── problem_space.py     # Problem validation + experiments
│           ├── context_mapping.py   # Stakeholder maps + learning roadmaps
│           ├── constraints.py       # Constraint analysis + negotiability
│           └── solution_validation.py  # 4-risks framework
├── docs/
│   └── ARCHITECTURE.md              # Detailed system documentation
├── app.py                           # Streamlit UI with checkpoints + docs pages
├── pyproject.toml                   # Package config
└── .env                             # Your ANTHROPIC_API_KEY
```

## Tech Stack

- **LangGraph** - Agent orchestration and state management
- **LangChain + Anthropic** - LLM calls to Claude
- **Streamlit** - Chat UI with streaming support
- **uv** - Fast Python package manager
- **Hatch** - Python build backend
