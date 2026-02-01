# PM Brainstorming Assistant

A multi-agent system that helps Product Managers think through problems using AI-powered specialist agents.

## What This Does

As a PM, you face two fundamentally different types of challenges:

1. **Prioritization problems** - You have multiple options and need to decide what to build first. Stakeholders disagree, resources are limited, and you need a structured way to make trade-offs.

2. **Discovery problems** - You're exploring unfamiliar territory. You need to map stakeholders, surface hidden constraints, and figure out what questions to even ask.

This tool automatically detects which type of problem you're facing and routes you to a specialist agent:

```
Your Problem → Coordinator (classifies) → Prioritization Agent (RICE, MoSCoW, etc.)
                                        → Discovery Agent (questions, sequence, blindspots)
```

The **Coordinator** explains its reasoning, so you understand why it chose a particular path. Then the **Specialist Agent** gives you a structured, actionable response tailored to your specific situation.

## Features

- **Automatic problem classification** with transparent reasoning
- **Prioritization Agent**: Applies frameworks like RICE, MoSCoW, Value vs Effort with markdown tables
- **Discovery Agent**: Generates specific questions, discovery sequence, and warns about blindspots
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

# Install dependencies
uv sync

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

## How to Run

### Option 1: Streamlit UI (Recommended)

```bash
uv run streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Option 2: Command Line

```bash
uv run python main.py
```

This runs the built-in test cases and prints everything to the terminal.

## Example Usage

**Prioritization problem:**
> "You're building a new feature with limited engineering resources. Your CEO wants Feature A (high visibility, demo-able), your biggest customer wants Feature B (threatens churn), and your data shows Feature C has the highest usage potential. Walk me through how you'd decide what to build."

The system will:
1. Classify as "prioritization" (explains why: multiple options, resource constraints)
2. Apply RICE or weighted scoring framework
3. Produce a comparison table
4. Give a clear recommendation

**Discovery problem:**
> "You're a PM assigned to a problem in a domain you've never worked in ('Total Category Optimization'). You have 2 weeks before your first stakeholder meeting. What information do you need to surface?"

The system will:
1. Classify as "discovery" (explains why: new domain, research phase)
2. Identify key discovery dimensions
3. Generate 5-10 specific questions to investigate
4. Recommend a sequence with reasoning
5. Warn about common blindspots

## Project Structure

```
master-pm-agents/
├── main.py            # Coordinator + LangGraph workflow + streaming
├── prioritization.py  # Prioritization agent (RICE, MoSCoW, etc.)
├── discovery.py       # Discovery agent (questions, sequence, blindspots)
├── app.py             # Streamlit chat UI
├── spec.md            # Detailed agent specifications
├── CLAUDE.md          # Code style preferences
├── pyproject.toml     # Dependencies (managed by uv)
└── .env               # Your ANTHROPIC_API_KEY
```

## Tech Stack

- **LangGraph** - Agent orchestration and state management
- **LangChain + Anthropic** - LLM calls to Claude
- **Streamlit** - Chat UI with streaming support
- **uv** - Fast Python package manager
