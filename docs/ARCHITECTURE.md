# PM Agents - Architecture & System Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [System Flow](#system-flow)
4. [State Management](#state-management)
5. [Agent System Prompts](#agent-system-prompts)
6. [Project Structure](#project-structure)
7. [Module Reference](#module-reference)
8. [Adding New Agents](#adding-new-agents)

---

## Project Overview

**PM Agents** is a multi-agent AI system designed to help Product Managers think through problems using specialized AI agents. The system uses LangGraph for orchestration and Claude (via LangChain) as the underlying LLM.

### Core Concept

Product Managers face two fundamentally different types of challenges:

| Problem Type | Description | Example |
|--------------|-------------|---------|
| **Prioritization** | Choosing between options, ranking, trade-offs, resource allocation | "Which of these 3 features should we build first?" |
| **Discovery** | Exploring unknowns, mapping stakeholders, surfacing hidden constraints | "I'm new to this domain, what should I learn first?" |

The system automatically detects which type of problem the user is facing and routes them to a specialized agent.

### Key Features

- **Automatic Classification**: Coordinator analyzes the problem and explains its reasoning
- **Specialized Agents**: Each agent has domain-specific prompts and frameworks
- **Streaming Support**: Real-time token streaming for responsive UI
- **Transparent Reasoning**: Users see why the system chose a particular path

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Streamlit Chat UI (app.py)                       │   │
│  │  - Chat input for problem statements                                 │   │
│  │  - Displays coordinator classification in info box                   │   │
│  │  - Streams specialist agent response in real-time                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LANGGRAPH WORKFLOW                                 │
│                          (src/pm_agents/workflow.py)                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                              STATE                                   │   │
│  │  {                                                                   │   │
│  │    user_input: str,              # Original problem                  │   │
│  │    classification: str,          # "prioritization" | "discovery"    │   │
│  │    classification_reasoning: str, # Why this classification          │   │
│  │    agent_output: str             # Final specialist response         │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      COORDINATOR NODE                                │   │
│  │                   (src/pm_agents/coordinator.py)                     │   │
│  │                                                                      │   │
│  │  - Receives user_input                                               │   │
│  │  - Calls LLM with COORDINATOR_PROMPT                                 │   │
│  │  - Parses response to extract classification + reasoning             │   │
│  │  - Updates state with classification info                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                          ┌───────────┴───────────┐                          │
│                          │   CONDITIONAL ROUTER   │                          │
│                          │  route_to_specialist() │                          │
│                          └───────────┬───────────┘                          │
│                                      │                                      │
│              ┌───────────────────────┼───────────────────────┐              │
│              │                       │                       │              │
│              ▼                       │                       ▼              │
│  ┌───────────────────────┐           │           ┌───────────────────────┐  │
│  │  PRIORITIZATION AGENT │           │           │    DISCOVERY AGENT    │  │
│  │                       │           │           │                       │  │
│  │  - RICE framework     │           │           │  - Discovery dims     │  │
│  │  - MoSCoW method      │           │           │  - Specific questions │  │
│  │  - Value vs Effort    │           │           │  - Sequence plan      │  │
│  │  - Weighted scoring   │           │           │  - Blindspot warnings │  │
│  │  - Markdown tables    │           │           │                       │  │
│  └───────────────────────┘           │           └───────────────────────┘  │
│              │                       │                       │              │
│              └───────────────────────┼───────────────────────┘              │
│                                      │                                      │
│                                      ▼                                      │
│                               ┌─────────────┐                               │
│                               │     END     │                               │
│                               └─────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM LAYER                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Claude (claude-sonnet-4-20250514)                 │   │
│  │                        via LangChain Anthropic                       │   │
│  │                                                                      │   │
│  │  Two instances:                                                      │   │
│  │  - llm: Regular calls (coordinator, non-streaming specialist)        │   │
│  │  - llm_streaming: Token-by-token streaming for UI                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System Flow

### Standard Flow (Non-Streaming)

```
1. User Input
   └── "Help me decide between Feature A, B, and C..."

2. Coordinator Agent
   ├── Receives: user_input
   ├── Calls: LLM with COORDINATOR_PROMPT
   ├── Parses: CLASSIFICATION + REASONING from response
   └── Returns: classification="prioritization", reasoning="..."

3. Router
   └── Routes to: prioritization_agent (based on classification)

4. Prioritization Agent
   ├── Receives: user_input
   ├── Calls: LLM with PRIORITIZATION_PROMPT
   └── Returns: Structured analysis with RICE table + recommendation

5. Final State
   └── {
         user_input: "Help me decide...",
         classification: "prioritization",
         classification_reasoning: "This involves choosing between...",
         agent_output: "## Core Trade-off\n\n..."
       }
```

### Streaming Flow (For UI)

```
1. User Input → run_streaming(user_input)

2. Coordinator runs (non-streaming)
   └── YIELDS: ("coordinator", {classification, reasoning})

3. UI displays classification in info box

4. Specialist agent streams
   └── YIELDS: ("token", "Each") → ("token", " token") → ...

5. UI updates in real-time with each token

6. Streaming complete
   └── YIELDS: ("done", full_output)
```

---

## State Management

The workflow uses a TypedDict to pass state between nodes:

```python
# src/pm_agents/state.py

class State(TypedDict):
    user_input: str                  # Original problem statement from user
    classification: str              # "prioritization" or "discovery"
    classification_reasoning: str    # 2-3 sentence explanation
    agent_output: str                # Full response from specialist agent
```

### State Flow Through Nodes

| Node | Reads | Writes |
|------|-------|--------|
| coordinator_node | user_input | classification, classification_reasoning |
| prioritization_agent_node | user_input | agent_output |
| discovery_agent_node | user_input | agent_output |

---

## Agent System Prompts

### Coordinator Agent

**Purpose**: Classify the problem type and explain the reasoning.

**Location**: `src/pm_agents/coordinator.py`

```
You are a PM coach coordinator. Your job is to:
1. Read the user's problem statement
2. Classify it as either "prioritization" or "discovery"
3. Explain your classification in 2-3 sentences

Prioritization problems involve choosing between options, ranking, trade-offs,
or resource allocation.

Discovery problems involve understanding, researching, mapping stakeholders,
or surfacing hidden information.

Respond in this exact format:
CLASSIFICATION: [prioritization or discovery]
REASONING: [2-3 sentences explaining why]
```

**Output Parsing**:
- Looks for `CLASSIFICATION:` line to extract type
- Looks for `REASONING:` line to extract explanation
- Defaults to "discovery" if parsing fails

---

### Prioritization Agent

**Purpose**: Help users make trade-off decisions using structured frameworks.

**Location**: `src/pm_agents/agents/prioritization.py`

```
You are a senior PM helping with prioritization decisions.

When given a problem:
1. Restate the core trade-off in 1-2 sentences
2. Select the most appropriate framework (RICE, MoSCoW, Value vs Effort,
   or weighted scoring) and explain why
3. Apply the framework with a markdown table
4. Give a clear recommendation with reasoning
5. Note your assumptions and what you'd validate

Be specific to their situation. Don't give generic framework explanations—apply
it to their actual problem.

If you need more information to score accurately, state your assumptions
explicitly rather than asking questions.
```

**Frameworks Available**:
- **RICE**: Reach, Impact, Confidence, Effort
- **MoSCoW**: Must have, Should have, Could have, Won't have
- **Value vs Effort**: 2x2 matrix prioritization
- **Weighted Scoring**: Custom criteria with weights

**Expected Output Structure**:
1. Context restatement (1-2 sentences)
2. Framework selection with justification
3. Markdown table with analysis
4. Clear recommendation
5. Assumptions and validation needs

---

### Discovery Agent

**Purpose**: Help users explore and map unfamiliar problem spaces.

**Location**: `src/pm_agents/agents/discovery.py`

```
You are a senior PM helping with discovery and research.

When given a problem:
1. Frame what the user is actually trying to discover (the underlying question)
2. Identify 3-5 discovery dimensions relevant to their situation
3. Generate 5-10 specific, concrete questions they should investigate
4. Recommend a sequence for discovery with reasoning
5. Warn about common blindspots for this type of discovery

Be specific to their situation. Don't give generic discovery advice—tailor to
their actual domain and context.

Assume they're smart but new to this specific problem. Give them a roadmap,
not a lecture.
```

**Discovery Dimensions** (examples):
- Stakeholder landscape
- Technical constraints
- Business context
- User needs
- Competitive landscape

**Expected Output Structure**:
1. Problem framing (underlying question)
2. 3-5 discovery dimensions
3. 5-10 specific investigation questions
4. Recommended sequence with reasoning
5. Blindspot warnings

---

## Project Structure

```
master-pm-agents/
├── src/
│   └── pm_agents/
│       ├── __init__.py              # Public API: run, run_streaming, State
│       ├── workflow.py              # LangGraph orchestration
│       ├── coordinator.py           # Coordinator agent logic
│       ├── state.py                 # State TypedDict definition
│       └── agents/
│           ├── __init__.py          # Agent exports
│           ├── prioritization.py    # Prioritization specialist
│           └── discovery.py         # Discovery specialist
├── docs/
│   └── ARCHITECTURE.md              # This file
├── app.py                           # Streamlit chat UI
├── pyproject.toml                   # Package configuration
├── README.md                        # User-facing documentation
├── CLAUDE.md                        # AI coding guidelines
├── spec.md                          # Original specifications
└── .env                             # API keys (gitignored)
```

---

## Module Reference

### Public API (`pm_agents`)

```python
from pm_agents import run, run_streaming, State

# Run with full response
result: State = run("Your PM problem...")
print(result["classification"])      # "prioritization" or "discovery"
print(result["agent_output"])        # Full specialist response

# Run with streaming (for UIs)
for event_type, data in run_streaming("Your PM problem..."):
    if event_type == "coordinator":
        print(f"Classified as: {data['classification']}")
        print(f"Because: {data['reasoning']}")
    elif event_type == "token":
        print(data, end="", flush=True)
    elif event_type == "done":
        print("\n--- Complete ---")
```

### Coordinator Module

```python
from pm_agents.coordinator import run_coordinator, parse_response, PROMPT

# Run coordinator
classification, reasoning = run_coordinator(user_input, llm)

# Parse raw LLM response
classification, reasoning = parse_response(response_text)
```

### Agent Modules

```python
from pm_agents.agents import (
    run_prioritization,    # (user_input, llm) -> str
    stream_prioritization, # (user_input, llm_streaming) -> Generator[str]
    run_discovery,         # (user_input, llm) -> str
    stream_discovery,      # (user_input, llm_streaming) -> Generator[str]
    PRIORITIZATION_PROMPT,
    DISCOVERY_PROMPT,
)
```

---

## Adding New Agents

To add a new specialist agent (e.g., "stakeholder_mapping"):

### 1. Create the Agent Module

```python
# src/pm_agents/agents/stakeholder_mapping.py

"""
Stakeholder Mapping Agent
Helps identify and analyze stakeholders for a product or initiative.
"""

PROMPT = """You are a senior PM helping with stakeholder analysis.

When given a problem:
1. Identify all relevant stakeholders
2. Create a power/interest grid
3. Recommend engagement strategies for each quadrant
4. Flag potential conflicts or dependencies
5. Suggest a communication plan

Be specific to their situation..."""


def run_agent(user_input: str, llm) -> str:
    """Run the stakeholder mapping agent."""
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_input}
    ]
    response = llm.invoke(messages)
    return response.content


def stream_agent(user_input: str, llm_streaming):
    """Stream the agent's response token by token."""
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_input}
    ]
    for chunk in llm_streaming.stream(messages):
        if chunk.content:
            yield chunk.content
```

### 2. Export from agents/__init__.py

```python
# src/pm_agents/agents/__init__.py

from .stakeholder_mapping import PROMPT as STAKEHOLDER_PROMPT
from .stakeholder_mapping import run_agent as run_stakeholder
from .stakeholder_mapping import stream_agent as stream_stakeholder

__all__ = [
    # ... existing exports ...
    "STAKEHOLDER_PROMPT",
    "run_stakeholder",
    "stream_stakeholder",
]
```

### 3. Update Coordinator Prompt

Add the new classification option to the coordinator's prompt in `coordinator.py`.

### 4. Add Node and Routing

In `workflow.py`:

```python
from .agents import run_stakeholder, stream_stakeholder

def stakeholder_agent_node(state: State) -> State:
    output = run_stakeholder(state["user_input"], llm)
    return {**state, "agent_output": output}

# In build_graph():
graph.add_node("stakeholder_agent", stakeholder_agent_node)
graph.add_edge("stakeholder_agent", END)

# Update conditional edges mapping
```

### 5. Update Streaming Logic

In `run_streaming()`, add the new branch:

```python
elif classification == "stakeholder":
    for token in stream_stakeholder(user_input, llm_streaming):
        full_output += token
        yield ("token", token)
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Yes |

### LLM Configuration

Located in `src/pm_agents/workflow.py`:

```python
llm = ChatAnthropic(model="claude-sonnet-4-20250514")
llm_streaming = ChatAnthropic(model="claude-sonnet-4-20250514", streaming=True)
```

To change the model, update both instances.

---

## Running the System

### Streamlit UI

```bash
uv run streamlit run app.py
```

Opens at http://localhost:8501

### Python API

```python
from pm_agents import run

result = run("Your problem statement here...")
```

### Development

```bash
# Install in editable mode
uv sync

# Test imports
uv run python -c "from pm_agents import run; print('OK')"
```

---

*Last updated: February 2026*
