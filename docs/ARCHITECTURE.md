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

Product Managers face different types of challenges that require different thinking approaches:

| Problem Type | Description | Example |
|--------------|-------------|---------|
| **Prioritization** | Choosing between options, ranking, trade-offs, resource allocation | "Which of these 3 features should we build first?" |
| **Problem Space** | Validating if a problem actually exists and matters | "I think users struggle with X, but is it real?" |
| **Context Mapping** | Learning new domains, stakeholders, organizations | "I'm new to this team, what should I learn?" |
| **Constraints** | Surfacing hidden technical, organizational, external limitations | "Why does engineering keep saying 'won't work'?" |
| **Solution Validation** | Validating solutions against 4 risks (value, usability, feasibility, viability) | "Is this solution idea viable?" |

The system automatically detects which type of problem the user is facing and routes them to a specialized agent.

### Key Features

- **Automatic Classification**: Coordinator analyzes the problem and explains its reasoning
- **5 Specialized Agents**: Each agent has domain-specific prompts and frameworks
- **Generative Behavior**: Agents make soft guesses (marked with ⚠️) instead of blocking for input
- **Validation Questions**: Every agent ends with "Questions for Your Next Stakeholder Meeting"
- **Streaming Support**: Real-time token streaming for responsive UI
- **Transparent Reasoning**: Users see why the system chose a particular path

---

## Architecture Diagram

### Human-in-the-Loop Staged Workflow

The system implements a 4-stage workflow with user checkpoints, allowing validation at each step:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                            Streamlit Chat UI (app.py)                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         VIEW ROUTING                                 │   │
│  │                                                                      │   │
│  │   current_view = "chat"              → Main workflow (below)         │   │
│  │                 | "doc_prioritization" → Agent documentation page    │   │
│  │                 | "doc_problem_space"  → Agent documentation page    │   │
│  │                 | "doc_context_mapping"→ Agent documentation page    │   │
│  │                 | "doc_constraints"    → Agent documentation page    │   │
│  │                 | "doc_solution_validation" → Agent documentation    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                              (when view = "chat")                           │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      WORKFLOW STAGES                                 │   │
│  │                                                                      │   │
│  │   workflow_stage = "input"         → Chat input collection           │   │
│  │                  | "refinement"    → Checkpoint 1: Review refinement │   │
│  │                  | "classification"→ Checkpoint 2: Confirm routing   │   │
│  │                  | "soft_guesses"  → Checkpoint 3: Validate guesses  │   │
│  │                  | "streaming"     → Stream specialist output        │   │
│  │                  | "complete"      → Show results + start new        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        4-STAGE WORKFLOW FLOW                                 │
│                                                                             │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│   │   STAGE 1   │    │   STAGE 2   │    │   STAGE 3   │    │   STAGE 4   │  │
│   │ REFINEMENT  │───▶│CLASSIFICATION│───▶│SOFT GUESSES │───▶│ SPECIALIST  │  │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐   │
│   │CHECKPOINT │      │CHECKPOINT │      │CHECKPOINT │      │  STREAM   │   │
│   │  User     │      │  User     │      │  User     │      │  Output   │   │
│   │  reviews  │      │  confirms │      │  validates│      │  with     │   │
│   │  & edits  │      │  or       │      │  assump-  │      │  context  │   │
│   │  refined  │      │  overrides│      │  tions    │      │           │   │
│   │  problem  │      │  routing  │      │           │      │           │   │
│   └───────────┘      └───────────┘      └───────────┘      └───────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND WORKFLOW                                   │
│                          (src/pm_agents/workflow.py)                         │
│                                                                             │
│  Stage 1: run_stage1_refinement(user_input)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REFINEMENT (coordinator.py)                                        │   │
│  │  - Makes vague inputs specific and concrete                         │   │
│  │  - Surfaces implicit assumptions                                    │   │
│  │  - Returns: refined_statement, improvements, soft_guesses           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  Stage 2: run_stage2_classification(refined_input)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CLASSIFICATION (coordinator.py)                                    │   │
│  │  - Classifies into 1 of 5 categories                                │   │
│  │  - Explains reasoning                                               │   │
│  │  - Suggests alternatives that could also fit                        │   │
│  │  - Returns: classification, reasoning, alternatives                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  Stage 3: run_stage3_soft_guesses(refined_input, classification)            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SOFT GUESSES EXTRACTION (coordinator.py)                           │   │
│  │  - Identifies 3-5 key assumptions                                   │   │
│  │  - Rates confidence (High/Medium/Low)                               │   │
│  │  - Returns: list of {topic, assumption, confidence, reason}         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  Stage 4: run_stage4_specialist(refined_input, classification, guesses)     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SPECIALIST AGENT (agents/*.py)                                     │   │
│  │  - Incorporates confirmed assumptions into context                  │   │
│  │  - Streams analysis token-by-token                                  │   │
│  │  - Yields: ("token", str) → ("done", full_output)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│       ┌──────────┬──────────┬────────┼────────┬──────────┬──────────┐       │
│       ▼          ▼          ▼        │        ▼          ▼          │       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ │ ┌─────────┐ ┌─────────┐      │       │
│  │PRIORITI-│ │PROBLEM  │ │CONTEXT  │ │ │CONSTR-  │ │SOLUTION │      │       │
│  │ZATION   │ │SPACE    │ │MAPPING  │ │ │AINTS    │ │VALID.   │      │       │
│  │         │ │         │ │         │ │ │         │ │         │      │       │
│  │ - RICE  │ │ - Exist?│ │ - Domain│ │ │ - Tech  │ │ - Value │      │       │
│  │ - MoSCoW│ │ - Matter│ │ - Stake-│ │ │ - Org   │ │ - Usab. │      │       │
│  │ - Value │ │ - Soft  │ │   holder│ │ │ - Extern│ │ - Feas. │      │       │
│  │   /Efft │ │   guesses│ │ - Learn │ │ │ - Sever-│ │ - Viab. │      │       │
│  │ - Tables│ │ - ⚠️ flag│ │   road- │ │ │   ity   │ │ - 🔴🟡🟢│      │       │
│  │         │ │         │ │   map   │ │ │   matrix│ │         │      │       │
│  └─────────┘ └─────────┘ └─────────┘ │ └─────────┘ └─────────┘      │       │
│                                      │                              │       │
└──────────────────────────────────────┼──────────────────────────────┘       │
                                       │                                      │
                                       ▼                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM LAYER                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Claude (claude-sonnet-4-20250514)                 │   │
│  │                        via LangChain Anthropic                       │   │
│  │                                                                      │   │
│  │  Two instances:                                                      │   │
│  │  - llm: Regular calls (refinement, classification, soft guesses)     │   │
│  │  - llm_streaming: Token-by-token streaming for specialist output     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System Flow

### Human-in-the-Loop Flow (Recommended)

The staged workflow gives users control at each checkpoint:

```
1. User Input
   └── "I think users struggle with onboarding, but I'm not sure if it's real..."
       │
       ▼
2. STAGE 1: Refinement (run_stage1_refinement)
   ├── Calls: LLM with REFINEMENT_PROMPT
   ├── Returns: {
   │     refined_statement: "Validate whether enterprise users (100+ seats)...",
   │     improvements: ["Made user segment specific", "Added frequency"],
   │     soft_guesses: ["Target User: Enterprise customers — Confidence: Medium"]
   │   }
   │
   ▼ [CHECKPOINT 1: User reviews/edits refined statement]
       │
       ▼
3. STAGE 2: Classification (run_stage2_classification)
   ├── Calls: LLM with COORDINATOR_PROMPT
   ├── Returns: {
   │     classification: "problem_space",
   │     reasoning: "User is uncertain if the problem exists...",
   │     alternatives: ["context_mapping"]  # Other options that could fit
   │   }
   │
   ▼ [CHECKPOINT 2: User confirms or overrides classification]
       │
       ▼
4. STAGE 3: Soft Guesses (run_stage3_soft_guesses)
   ├── Calls: LLM with SOFT_GUESSES_PROMPT
   ├── Returns: [
   │     {topic: "Target User", assumption: "Enterprise customers",
   │      confidence: "Medium", reason: "Not explicitly stated"},
   │     {topic: "Severity", assumption: "Blocking issue",
   │      confidence: "Low", reason: "Could be minor annoyance"},
   │     ...
   │   ]
   │
   ▼ [CHECKPOINT 3: User validates/corrects each assumption]
       │
       ▼
5. STAGE 4: Specialist (run_stage4_specialist)
   ├── Builds context: refined_input + confirmed_guesses
   ├── Streams: problem_space agent output token-by-token
   ├── YIELDS: ("token", "##") → ("token", " Problem") → ...
   └── YIELDS: ("done", full_output)
       │
       ▼
6. Complete
   └── User sees full analysis with their confirmed context baked in
```

### Checkpoint Details

| Checkpoint | What User Can Do | Why It Matters |
|------------|------------------|----------------|
| **1. Refinement** | Edit the refined problem statement | Ensures the system understood correctly |
| **2. Classification** | Confirm or select different agent | User may know better which lens to use |
| **3. Soft Guesses** | Mark assumptions correct/incorrect, provide corrections | Prevents analysis based on wrong assumptions |

### Legacy Flow (Non-Streaming, No Checkpoints)

For programmatic use without user interaction:

```
1. User Input → run(user_input)

2. Coordinator classifies
   └── Returns: classification="problem_space", reasoning="..."

3. Router selects specialist

4. Specialist agent runs
   └── Returns: Full analysis

5. Final State
   └── {
         user_input: "I think users struggle...",
         classification: "problem_space",
         classification_reasoning: "User is uncertain...",
         agent_output: "## Problem Statement Reframe\n\n..."
       }
```

### Streaming Flow (Legacy, No Checkpoints)

```
1. User Input → run_streaming(user_input)

2. Coordinator runs (non-streaming)
   └── YIELDS: ("coordinator", {classification, reasoning, alternatives})

3. UI displays classification

4. Specialist agent streams
   └── YIELDS: ("token", "Each") → ("token", " token") → ...

5. Complete
   └── YIELDS: ("done", full_output)
```

---

## State Management

The workflow uses a TypedDict to pass state between nodes:

```python
# src/pm_agents/state.py

class State(TypedDict):
    # Core fields
    user_input: str                  # Original problem statement from user
    classification: str              # One of: prioritization, problem_space,
                                     #         context_mapping, constraints,
                                     #         solution_validation
    classification_reasoning: str    # 2-3 sentence explanation
    agent_output: str                # Full response from specialist agent

    # Generative behavior fields
    soft_guesses: list               # [{"guess": "...", "confidence": "...",
                                     #   "validation_question": "..."}]
    validation_questions: list       # [{"question": "...", "priority": "...",
                                     #   "context": "..."}]

    # Human-in-the-loop checkpoint fields
    refined_input: str               # Problem after refinement stage
    refinement_suggestions: str      # What coordinator improved
    classification_alternatives: list  # Other categories that could fit
    confirmed_guesses: list          # User-validated assumptions
```

### UI Session State (app.py)

The Streamlit UI maintains additional state for the multi-stage workflow:

```python
# View routing
current_view: str          # "chat" | "doc_<agent_name>"

# Workflow progression
workflow_stage: str        # "input" | "refinement" | "classification" |
                           # "soft_guesses" | "streaming" | "complete"

# Data from each stage
original_input: str        # User's raw input
refinement_data: dict      # {refined_statement, improvements, soft_guesses}
refined_input: str         # Edited refined statement
classification_data: dict  # {classification, reasoning, alternatives}
soft_guesses_data: list    # [{topic, assumption, confidence, reason}, ...]
confirmed_guesses: list    # User-validated version of soft_guesses_data
final_output: str          # Specialist agent's full response
messages: list             # Chat history for display
```

### State Flow Through Stages

| Stage | Function | Input | Output |
|-------|----------|-------|--------|
| 1. Refinement | `run_stage1_refinement` | user_input | refined_statement, improvements, soft_guesses |
| 2. Classification | `run_stage2_classification` | refined_input | classification, reasoning, alternatives |
| 3. Soft Guesses | `run_stage3_soft_guesses` | refined_input, classification | list of assumptions |
| 4. Specialist | `run_stage4_specialist` | refined_input, classification, confirmed_guesses | streaming tokens → full output |

### State Flow Through Nodes (Legacy Graph)

| Node | Reads | Writes |
|------|-------|--------|
| coordinator_node | user_input | classification, classification_reasoning, classification_alternatives |
| prioritization_agent_node | user_input | agent_output |
| problem_space_agent_node | user_input | agent_output |
| context_mapping_agent_node | user_input | agent_output |
| constraints_agent_node | user_input | agent_output |
| solution_validation_agent_node | user_input | agent_output |

---

## Agent System Prompts

---

### Coordinator Agent

**Purpose**: The coordinator handles three key functions:
1. **Refinement** - Make vague problem statements specific and concrete
2. **Classification** - Classify the problem into one of 5 categories
3. **Soft Guesses Extraction** - Surface assumptions for user validation

**Location**: `src/pm_agents/coordinator.py`

#### Refinement Prompt

```
You are a PM coach helping refine problem statements.

Take the user's input and:
1. Make it more specific and concrete
2. Identify vague terms that need clarification
3. Surface implicit assumptions

## Output Format
REFINED_STATEMENT: [2-3 sentence specific version]

IMPROVEMENTS_MADE:
- [What you made more specific]
- [What assumptions you surfaced]

SOFT_GUESSES:
- [Topic]: [What you assumed] — Confidence: [High/Medium/Low]

## Guidelines
- Keep it actionable and testable
- Focus on WHO, WHAT pain, HOW OFTEN
- If already specific, make minimal changes
```

#### Classification Prompt

```
You are a PM coach coordinator. Your job is to:
1. Read the user's problem statement
2. Classify it into ONE of these 5 categories
3. Explain your classification in 2-3 sentences

## Categories

**prioritization**
Use when: Choosing between options, ranking, trade-offs, resource allocation,
deciding what to build first.
Examples: "Should we build A or B?", "How do I prioritize these features?"

**problem_space**
Use when: Validating if a problem actually exists and matters. User is uncertain
if the pain point is real.
Examples: "I think users struggle with X, but not sure if real problem"

**context_mapping**
Use when: User needs to learn/map an unfamiliar domain, organization, or
stakeholder landscape.
Examples: "Just joined team, need to learn the domain", "Who are the stakeholders?"

**constraints**
Use when: User suspects hidden blockers or limitations but can't articulate them.
Examples: "Engineering keeps saying 'won't work' but I don't know why"

**solution_validation**
Use when: User has a solution idea and wants to validate if it's a good idea
(value, usability, feasibility, viability).
Examples: "Want to build X. Is this a good idea?"

## Response Format
CLASSIFICATION: [prioritization, problem_space, context_mapping, constraints,
                 or solution_validation]
REASONING: [2-3 sentences explaining why this category fits]
ALTERNATIVES: [Comma-separated list of other categories that could partially fit]
```

#### Soft Guesses Extraction Prompt

```
Identify 3-5 assumptions that would significantly change the analysis if wrong.

## Output Format
For each assumption, output on a single line:
- [Topic]: [What we're assuming] — Confidence: [High/Medium/Low] — [Brief reason]

## Focus On
- Who experiences this problem
- How severe/frequent it is
- What the current state looks like
- Why they're asking now
- What success looks like
```

#### Classification Logic

| Classification | Signal Words/Patterns | Core Question |
|----------------|----------------------|---------------|
| **prioritization** | "decide", "choose", "rank", "prioritize", "trade-off", "limited resources", "what to build first" | "What should we do first?" |
| **problem_space** | "not sure if real", "think users struggle", "is this actually a problem", "should we invest" | "Does this problem exist?" |
| **context_mapping** | "new to", "just joined", "unfamiliar", "learn the domain", "who are the stakeholders" | "What do I need to know?" |
| **constraints** | "won't work", "can't explain why", "what's blocking", "keeps pushing back", "limitations" | "What's stopping us?" |
| **solution_validation** | "want to build", "is this a good idea", "will this work", "should we proceed" | "Is this solution viable?" |

#### Response Parsing

The coordinator's classification response is parsed to extract classification, reasoning, and alternatives:

```python
def parse_response(response_text: str) -> tuple[str, str, list]:
    valid_classifications = [
        "solution_validation",  # Check longer names first
        "context_mapping",
        "problem_space",
        "prioritization",
        "constraints",
    ]

    classification = "problem_space"  # default fallback
    reasoning = ""
    alternatives = []

    lines = response_text.strip().split("\n")
    for line in lines:
        if line.upper().startswith("CLASSIFICATION:"):
            value = line.split(":", 1)[1].strip().lower()
            for valid in valid_classifications:
                if valid in value:
                    classification = valid
                    break
        elif line.upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
        elif line.upper().startswith("ALTERNATIVES:"):
            alt_text = line.split(":", 1)[1].strip().lower()
            if alt_text and alt_text != "none":
                for alt in alt_text.split(","):
                    for valid in valid_classifications:
                        if valid in alt.strip() and valid != classification:
                            alternatives.append(valid)

    return classification, reasoning, alternatives
```

**Why "problem_space" is the default**: If parsing fails or the classification is ambiguous, problem_space is safer—it encourages validation before commitment.

#### Coordinator Functions

```python
# Classification (returns alternatives for user override)
classification, reasoning, alternatives = run_coordinator(user_input, llm)

# Refinement (makes vague inputs specific)
result = run_refinement(user_input, llm)
# result = {refined_statement, improvements, soft_guesses}

# Soft guesses extraction (surfaces assumptions)
guesses = extract_soft_guesses(refined_input, classification, llm)
# guesses = [{topic, assumption, confidence, reason}, ...]
```

---

### Prioritization Agent

**Purpose**: Help users make trade-off decisions using structured frameworks.

**Location**: `src/pm_agents/agents/prioritization.py`

#### Key Capabilities
- RICE framework
- MoSCoW method
- Value vs Effort matrix
- Weighted scoring

#### Expected Output Structure
1. Context restatement (1-2 sentences)
2. Framework selection with reasoning
3. Analysis table (Markdown)
4. Clear recommendation
5. Assumptions & validation notes

---

### Problem Space Agent

**Purpose**: Validate whether problems actually exist and matter to users.

**Location**: `src/pm_agents/agents/problem_space.py`

#### Generative Behavior

Instead of asking clarifying questions and waiting, this agent:
1. Makes soft guesses based on available context (marked with ⚠️)
2. Proceeds with analysis using those guesses
3. Generates validation questions for stakeholders

#### Expected Output Structure

1. **Problem Statement Reframe** - What the PM is trying to validate
2. **Soft Guesses** (marked with ⚠️) - Educated guesses about who, frequency, workarounds, why it matters
3. **Problem Existence Analysis** - Evidence FOR, AGAINST, and UNKNOWN
4. **Problem Severity Assessment** - Frequency, impact, alternatives
5. **Risk Assessment** - What if real vs fake, recommendation
6. **Questions for Your Next Stakeholder Meeting** - 5-7 specific validation questions

#### Soft Guess Format

```
⚠️ **[Guess]**: [Your assumption] — *Confidence: High/Medium/Low*
```

---

### Context Mapping Agent

**Purpose**: Help PMs map unfamiliar domains, stakeholders, and organizational dynamics.

**Location**: `src/pm_agents/agents/context_mapping.py`

#### Expected Output Structure

1. **Context Summary** - What the agent understands about the situation
2. **Soft Guesses** (marked with ⚠️) - Guesses about stakeholders, terminology, dynamics, history
3. **Stakeholder Map** - Table with Role, Motivation, Influence, Priority
4. **Domain Concepts** - 5-7 key terms and why they matter
5. **Hidden Dynamics to Watch For** - Who really makes decisions, history, unwritten rules
6. **Learning Roadmap** - Week 1, Week 2, Week 3+ priorities
7. **Questions for Your Next Stakeholder Meeting** - Questions for leadership, ICs, and cross-functional partners

---

### Constraints Agent

**Purpose**: Surface hidden limitations, blockers, and technical/organizational constraints.

**Location**: `src/pm_agents/agents/constraints.py`

#### Expected Output Structure

1. **Situation Summary** - What they're trying to accomplish
2. **Soft Guesses About Constraints** (marked with ⚠️) - Technical, resource, organizational, external, historical
3. **Constraint Deep Dive** - Analysis by category
4. **Constraint Severity Matrix** - Table with Type, Severity, Can Be Changed, Workaround
5. **Recommended Actions** - Accept, Negotiate, Escalate, or Pivot for each constraint
6. **Questions for Your Next Stakeholder Meeting** - Questions for Engineering, Leadership, Legal, dependent teams

---

### Solution Validation Agent

**Purpose**: Validate proposed solutions against the 4 product risks (from Marty Cagan).

**Location**: `src/pm_agents/agents/solution_validation.py`

#### The 4 Risks

| Risk | Question | Analysis Points |
|------|----------|-----------------|
| **Value** | Will customers buy/use it? | Current behavior, value proposition, evidence for/against |
| **Usability** | Can users figure it out? | Complexity, learning curve, familiar patterns, edge cases |
| **Feasibility** | Can engineering build it? | Technical complexity, new vs existing, dependencies, timeline |
| **Viability** | Does it work for the business? | Revenue impact, cost structure, strategic fit, stakeholder buy-in |

#### Risk Level Indicators
- 🔴 High risk
- 🟡 Medium risk
- 🟢 Low risk

#### Expected Output Structure

1. **Solution Summary** - What the proposed solution is
2. **Soft Guesses** (marked with ⚠️) - Target users, technical approach, business model, competitive context
3. **Four Risks Analysis** - Each risk with analysis and risk level (🔴/🟡/🟢)
4. **Risk Summary Matrix** - Table with Risk, Level, Confidence, Key Uncertainty
5. **Recommendation** - Overall assessment, biggest risk, suggested next step
6. **Questions for Your Next Stakeholder Meeting** - Questions for Users, Engineering, Business stakeholders

---

## Project Structure

```
master-pm-agents/
├── src/
│   └── pm_agents/
│       ├── __init__.py              # Public API: run, run_streaming, State
│       ├── workflow.py              # LangGraph orchestration
│       ├── coordinator.py           # Coordinator agent (5 categories)
│       ├── state.py                 # State TypedDict definition
│       └── agents/
│           ├── __init__.py          # Agent exports
│           ├── prioritization.py    # Trade-offs and ranking
│           ├── problem_space.py     # Problem validation
│           ├── context_mapping.py   # Domain/stakeholder mapping
│           ├── constraints.py       # Hidden limitations
│           └── solution_validation.py  # 4-risks validation
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
from pm_agents import (
    # Legacy (no checkpoints)
    run,
    run_streaming,
    State,
    # Staged workflow (with checkpoints)
    run_stage1_refinement,
    run_stage2_classification,
    run_stage3_soft_guesses,
    run_stage4_specialist,
)

# ===== STAGED WORKFLOW (Recommended for UIs) =====

# Stage 1: Refinement
for event_type, data in run_stage1_refinement("I think users struggle with X"):
    if event_type == "refinement":
        print(f"Refined: {data['refined_statement']}")
        print(f"Improvements: {data['improvements']}")
        # → User reviews and can edit

# Stage 2: Classification
for event_type, data in run_stage2_classification(refined_input):
    if event_type == "classification":
        print(f"Classification: {data['classification']}")
        print(f"Alternatives: {data['alternatives']}")
        # → User confirms or overrides

# Stage 3: Soft Guesses
for event_type, data in run_stage3_soft_guesses(refined_input, classification):
    if event_type == "soft_guesses":
        for guess in data:
            print(f"- {guess['topic']}: {guess['assumption']} ({guess['confidence']})")
        # → User validates each assumption

# Stage 4: Specialist (streaming)
for event_type, data in run_stage4_specialist(refined_input, classification, confirmed_guesses):
    if event_type == "token":
        print(data, end="", flush=True)
    elif event_type == "done":
        print("\n--- Complete ---")

# ===== LEGACY API (No checkpoints) =====

# Run with full response
result: State = run("Your PM problem...")
print(result["classification"])      # One of 5 categories
print(result["agent_output"])        # Full specialist response

# Run with streaming (for simple UIs)
for event_type, data in run_streaming("Your PM problem..."):
    if event_type == "coordinator":
        print(f"Classified as: {data['classification']}")
        print(f"Alternatives: {data['alternatives']}")
    elif event_type == "token":
        print(data, end="", flush=True)
    elif event_type == "done":
        print("\n--- Complete ---")
```

### Coordinator Module

```python
from pm_agents.coordinator import (
    run_coordinator,
    run_refinement,
    extract_soft_guesses,
    parse_response,
    PROMPT,
    REFINEMENT_PROMPT,
    SOFT_GUESSES_PROMPT,
)

# Run classification (with alternatives)
classification, reasoning, alternatives = run_coordinator(user_input, llm)

# Run refinement
result = run_refinement(user_input, llm)
# result = {refined_statement, improvements, soft_guesses}

# Extract soft guesses
guesses = extract_soft_guesses(refined_input, classification, llm)
# guesses = [{topic, assumption, confidence, reason}, ...]

# Parse raw LLM response
classification, reasoning, alternatives = parse_response(response_text)
```

### Agent Modules

```python
from pm_agents.agents import (
    # Prioritization
    run_prioritization,         # (user_input, llm) -> str
    stream_prioritization,      # (user_input, llm_streaming) -> Generator[str]
    PRIORITIZATION_PROMPT,

    # Problem Space
    run_problem_space,
    stream_problem_space,
    PROBLEM_SPACE_PROMPT,

    # Context Mapping
    run_context_mapping,
    stream_context_mapping,
    CONTEXT_MAPPING_PROMPT,

    # Constraints
    run_constraints,
    stream_constraints,
    CONSTRAINTS_PROMPT,

    # Solution Validation
    run_solution_validation,
    stream_solution_validation,
    SOLUTION_VALIDATION_PROMPT,
)
```

---

## Adding New Agents

To add a new specialist agent (e.g., "competitive_analysis"):

### 1. Create the Agent Module

```python
# src/pm_agents/agents/competitive_analysis.py

"""
Competitive Analysis Agent
Helps analyze competitive landscape and positioning.
"""

PROMPT = """You are a senior PM helping with competitive analysis.

## Your Approach: Generative, Not Blocking
Instead of asking clarifying questions and waiting, you should:
1. Make soft guesses based on available context (mark with ⚠️)
2. Proceed with your analysis using those guesses
3. Generate validation questions the PM should ask stakeholders

## Output Structure
...

---

## Questions for Your Next Stakeholder Meeting
Generate 5-7 specific questions...
"""


def run_agent(user_input: str, llm) -> str:
    """Run the competitive analysis agent."""
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

from .competitive_analysis import PROMPT as COMPETITIVE_ANALYSIS_PROMPT
from .competitive_analysis import run_agent as run_competitive_analysis
from .competitive_analysis import stream_agent as stream_competitive_analysis

__all__ = [
    # ... existing exports ...
    "COMPETITIVE_ANALYSIS_PROMPT",
    "run_competitive_analysis",
    "stream_competitive_analysis",
]
```

### 3. Update Coordinator Prompt

Add the new classification option to the coordinator's prompt in `coordinator.py`:

```python
**competitive_analysis**
Use when: User needs to understand competitive landscape or positioning.
Examples: "Who are our competitors?", "How do we differentiate?"
```

### 4. Update parse_response()

Add the new classification to the valid list:

```python
valid_classifications = [
    "competitive_analysis",  # Add new one
    "solution_validation",
    "context_mapping",
    ...
]
```

### 5. Add Node and Routing in workflow.py

```python
from .agents import run_competitive_analysis, stream_competitive_analysis

def competitive_analysis_agent_node(state: State) -> State:
    output = run_competitive_analysis(state["user_input"], llm)
    return {**state, "agent_output": output}

# In build_graph():
graph.add_node("competitive_analysis_agent", competitive_analysis_agent_node)
graph.add_edge("competitive_analysis_agent", END)

# Update conditional edges mapping
graph.add_conditional_edges(
    "coordinator",
    route_to_specialist,
    {
        # ... existing routes ...
        "competitive_analysis_agent": "competitive_analysis_agent",
    }
)
```

### 6. Update Streaming Logic

In `run_streaming()` and `run_stage4_specialist()`, add to the stream_functions dict:

```python
stream_functions = {
    # ... existing ...
    "competitive_analysis": stream_competitive_analysis,
}
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
