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

---

### Coordinator Agent

**Purpose**: Classify the problem type and explain the reasoning transparently to the user.

**Location**: `src/pm_agents/coordinator.py`

#### System Prompt

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

#### Classification Logic

The coordinator distinguishes between two problem types based on signal patterns:

| Classification | Signal Words/Patterns | Core Question |
|----------------|----------------------|---------------|
| **Prioritization** | "decide", "choose", "rank", "prioritize", "trade-off", "limited resources", "what to build first", "which one", "compare" | "What should we do?" |
| **Discovery** | "understand", "discover", "research", "map", "identify", "surface", "learn", "explore", "new to", "unfamiliar" | "What do we need to know?" |

#### Detailed Classification Criteria

**Route to Prioritization when:**
- User has multiple concrete options and needs to choose or rank them
- Resource constraints (time, money, people) force trade-offs
- Stakeholders disagree on what to do first
- User needs a structured framework to justify a decision
- The options are known, but the decision criteria are unclear

**Route to Discovery when:**
- User needs to understand a problem space before making decisions
- User is exploring stakeholders, constraints, or unknowns
- User is new to a domain and needs to map it
- The problem itself is unclear or poorly defined
- User needs to surface hidden information or assumptions

#### Example Classifications

| User Input | Classification | Reasoning |
|------------|----------------|-----------|
| "We have Feature A, B, and C. Limited eng time. What should we build?" | prioritization | Multiple options, resource constraint, needs ranking |
| "I'm new to the payments domain. What should I learn first?" | discovery | New domain, needs to understand before deciding |
| "Should we build for enterprise or SMB first?" | prioritization | Two options, needs trade-off analysis |
| "Who are the stakeholders for our checkout flow?" | discovery | Mapping stakeholders, surfacing information |
| "CEO wants X, customer wants Y, data shows Z. Help me decide." | prioritization | Multiple competing options, needs framework |
| "What questions should I ask in user interviews?" | discovery | Research phase, generating investigation questions |

#### Response Parsing

The coordinator's response is parsed using simple string matching:

```python
def parse_response(response_text: str) -> tuple[str, str]:
    classification = "discovery"  # default fallback
    reasoning = ""

    lines = response_text.strip().split("\n")
    for line in lines:
        if line.upper().startswith("CLASSIFICATION:"):
            value = line.split(":", 1)[1].strip().lower()
            if "prioritization" in value:
                classification = "prioritization"
            else:
                classification = "discovery"
        elif line.upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    # Handle multi-line reasoning
    if not reasoning:
        for i, line in enumerate(lines):
            if line.upper().startswith("REASONING:"):
                reasoning = " ".join(lines[i:]).replace("REASONING:", "").strip()
                break

    return classification, reasoning
```

**Why "discovery" is the default**: If parsing fails or the classification is ambiguous, discovery is safer—it encourages exploration before commitment, whereas jumping to prioritization with incomplete information can lead to poor decisions.

---

### Prioritization Agent

**Purpose**: Help users make trade-off decisions using structured frameworks, producing actionable recommendations with clear reasoning.

**Location**: `src/pm_agents/agents/prioritization.py`

#### System Prompt

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

#### Available Frameworks

##### 1. RICE Framework
**Best for**: Comparing features or initiatives when you have rough data on reach and effort.

| Component | Description | Scale |
|-----------|-------------|-------|
| **Reach** | How many users/customers will this affect in a given time period? | Number (e.g., 1000 users/quarter) |
| **Impact** | How much will this affect each user? | 0.25 (minimal) to 3 (massive) |
| **Confidence** | How sure are you about these estimates? | 0-100% |
| **Effort** | How many person-months will this take? | Number (e.g., 2 person-months) |

**Formula**: `RICE Score = (Reach × Impact × Confidence) / Effort`

**Example Table Output**:
```markdown
| Feature | Reach | Impact | Confidence | Effort | RICE Score |
|---------|-------|--------|------------|--------|------------|
| Feature A | 5000 | 2 | 80% | 3 | 2,667 |
| Feature B | 2000 | 3 | 90% | 2 | 2,700 |
| Feature C | 10000 | 1 | 70% | 4 | 1,750 |
```

##### 2. MoSCoW Method
**Best for**: Release planning, MVP scoping, or when stakeholders need to agree on what's essential vs. nice-to-have.

| Category | Definition | Implication |
|----------|------------|-------------|
| **Must Have** | Non-negotiable for launch | Without these, the product fails |
| **Should Have** | Important but not critical | Can launch without, but should add soon |
| **Could Have** | Nice to have | Only if time/resources permit |
| **Won't Have** | Explicitly out of scope | Deferred to future releases |

**Example Table Output**:
```markdown
| Feature | Category | Rationale |
|---------|----------|-----------|
| User authentication | Must Have | Legal/security requirement |
| Password reset | Must Have | Basic usability expectation |
| Social login | Should Have | Reduces friction but not blocking |
| Dark mode | Could Have | User request but low impact |
| AI recommendations | Won't Have | Requires ML infrastructure we don't have |
```

##### 3. Value vs. Effort Matrix
**Best for**: Quick visual prioritization, especially in workshops or when explaining to non-technical stakeholders.

```
                    HIGH VALUE
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     │   Quick Wins     │   Big Bets       │
     │   (Do First)     │   (Plan These)   │
     │                  │                  │
LOW ─┼──────────────────┼──────────────────┼─ HIGH
EFFORT                  │                  EFFORT
     │                  │                  │
     │   Fill-Ins       │   Money Pits     │
     │   (Do If Time)   │   (Avoid)        │
     │                  │                  │
     └──────────────────┼──────────────────┘
                        │
                    LOW VALUE
```

**Example Table Output**:
```markdown
| Feature | Value | Effort | Quadrant |
|---------|-------|--------|----------|
| Feature A | High | Low | Quick Win ✅ |
| Feature B | High | High | Big Bet |
| Feature C | Low | Low | Fill-In |
| Feature D | Low | High | Money Pit ❌ |
```

##### 4. Weighted Scoring
**Best for**: Complex decisions with multiple criteria, or when you need to make the decision-making process transparent and auditable.

**Process**:
1. Define criteria (e.g., revenue impact, user satisfaction, strategic alignment)
2. Assign weights to each criterion (must sum to 100%)
3. Score each option on each criterion (typically 1-5 or 1-10)
4. Calculate weighted score

**Example Table Output**:
```markdown
| Criteria | Weight | Feature A | Feature B | Feature C |
|----------|--------|-----------|-----------|-----------|
| Revenue Impact | 30% | 4 | 3 | 5 |
| User Satisfaction | 25% | 5 | 4 | 3 |
| Strategic Fit | 25% | 3 | 5 | 4 |
| Eng Complexity | 20% | 4 | 2 | 3 |
| **Weighted Score** | | **4.0** | **3.6** | **3.9** |
```

#### Framework Selection Guide

| Situation | Recommended Framework | Why |
|-----------|----------------------|-----|
| Comparing 3+ features with some usage data | RICE | Quantitative, handles uncertainty |
| Scoping an MVP or release | MoSCoW | Clear categories, stakeholder alignment |
| Quick workshop prioritization | Value vs Effort | Visual, fast, intuitive |
| Executive decision with multiple criteria | Weighted Scoring | Transparent, auditable |
| Stakeholder conflict on priorities | Weighted Scoring | Makes criteria explicit, reduces politics |

#### Expected Output Structure

1. **Context Restatement** (1-2 sentences)
   - Shows understanding of the specific situation
   - Identifies the core trade-off

2. **Framework Selection** (1 paragraph)
   - Which framework and why it fits this situation
   - Acknowledges limitations if any

3. **Analysis Table** (Markdown)
   - Framework-appropriate columns
   - Scores/ratings for each option
   - Final ranking or categorization

4. **Recommendation** (1-2 paragraphs)
   - Clear "do this" statement
   - Reasoning that connects to the analysis
   - Sequencing if multiple items

5. **Assumptions & Validation** (Bullet list)
   - What was assumed to make the analysis
   - What the user should validate before acting
   - Risks if assumptions are wrong

---

### Discovery Agent

**Purpose**: Help users explore and map unfamiliar problem spaces, generating specific investigation questions and a structured approach to learning.

**Location**: `src/pm_agents/agents/discovery.py`

#### System Prompt

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

#### Discovery Dimensions

The agent identifies 3-5 dimensions relevant to the user's specific situation. Common dimensions include:

| Dimension | What It Covers | Example Questions |
|-----------|---------------|-------------------|
| **Stakeholder Landscape** | Who has power, interest, or influence | "Who can block this?" "Who benefits?" |
| **User Needs** | What users actually want vs. what they say | "What job are they hiring this for?" |
| **Technical Constraints** | What's possible, what's hard, what's impossible | "What are the system dependencies?" |
| **Business Context** | Revenue model, metrics, strategic priorities | "How does this align with company goals?" |
| **Competitive Landscape** | What alternatives exist, what's table stakes | "What do competitors do here?" |
| **Regulatory/Legal** | Compliance requirements, legal constraints | "What regulations apply?" |
| **Historical Context** | What's been tried before, why it failed/succeeded | "Has this been attempted before?" |
| **Organizational Dynamics** | Politics, culture, decision-making patterns | "Who needs to approve this?" |

#### Question Generation Approach

The agent generates 5-10 **specific, concrete questions** rather than generic prompts. Good discovery questions are:

| Quality | Bad Example | Good Example |
|---------|-------------|--------------|
| Specific | "What do users want?" | "What's the #1 complaint from users who churned in the last 90 days?" |
| Actionable | "Research the market" | "Which 3 competitors should I demo this week?" |
| Falsifiable | "Is this a good idea?" | "What would make us kill this project?" |
| Concrete | "Talk to stakeholders" | "What does [specific person] need to say yes?" |

#### Discovery Sequence Logic

The agent recommends an order for investigation based on:

1. **Dependencies**: Some information unlocks other questions
2. **Risk Reduction**: Address highest-uncertainty items first
3. **Stakeholder Access**: Some people are harder to reach
4. **Time Sensitivity**: Some information has expiration dates

**Typical Sequence Pattern**:
```
Week 1: Foundational Understanding
├── Internal docs and past decisions
├── Key stakeholder 1:1s
└── Competitive landscape scan

Week 2: User/Customer Deep Dive
├── User interviews or data analysis
├── Support ticket review
└── Sales/CS team insights

Week 3: Synthesis & Validation
├── Cross-reference findings
├── Identify contradictions
└── Validate assumptions with experts
```

#### Common Blindspots

The agent warns about blindspots based on the type of discovery:

| Discovery Type | Common Blindspots |
|----------------|-------------------|
| **New Domain** | Assuming vocabulary means the same thing; missing tribal knowledge |
| **User Research** | Confirmation bias; talking to fans not churned users |
| **Technical Discovery** | Underestimating dependencies; ignoring tech debt |
| **Stakeholder Mapping** | Missing informal influencers; assuming org chart = power |
| **Competitive Analysis** | Focusing only on features; missing business model differences |
| **Problem Definition** | Solving symptoms not causes; accepting problem framing uncritically |

#### Expected Output Structure

1. **Problem Framing** (1-2 paragraphs)
   - The underlying question the user is trying to answer
   - Why this framing matters
   - What success looks like

2. **Discovery Dimensions** (3-5 items)
   - Each dimension named and explained
   - Why it's relevant to this specific situation
   - What kind of information lives here

3. **Specific Questions** (5-10 items)
   - Numbered, concrete, actionable
   - Grouped by dimension or theme
   - Includes who to ask or where to look

4. **Recommended Sequence** (Ordered list or timeline)
   - What to investigate first and why
   - Dependencies between questions
   - Suggested timeline if appropriate

5. **Blindspot Warnings** (Bullet list)
   - What's easy to miss in this type of discovery
   - Cognitive biases to watch for
   - Questions the user might not think to ask

#### Example Output Excerpt

```markdown
## Problem Framing

You're trying to understand the "Total Category Optimization" domain well enough
to have credible conversations with stakeholders in 2 weeks. The underlying
question isn't "what is TCO?" but "what do I need to know to be useful in my
first stakeholder meeting?"

## Discovery Dimensions

### 1. Domain Vocabulary & Mental Models
The TCO space likely has specific terminology that insiders use...

### 2. Stakeholder Landscape
Before the meeting, you need to know who will be in the room...

## Specific Questions to Investigate

1. **What are the 5 key metrics that define success in TCO?** (Ask: your manager,
   look: internal dashboards)
2. **Who are the 3 most influential stakeholders and what do they care about?**
   (Ask: your skip-level, look: recent decision docs)
3. ...

## Recommended Sequence

**Days 1-3**: Foundation
- Read the last 3 quarterly reviews mentioning TCO
- Schedule 1:1s with your manager and one domain expert

**Days 4-7**: Stakeholder mapping
...

## Blindspot Warnings

- ⚠️ **Vocabulary trap**: Words like "optimization" may mean something specific
  in this domain. Don't assume.
- ⚠️ **Past failures**: Ask "what's been tried before?" early—there may be
  political landmines.
```

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
