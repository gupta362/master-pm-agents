# SPEC.md

## Overview

Multi-agent PM brainstorming system. User provides a problem statement, coordinator classifies and explains, then routes to specialist agent.

## Project Setup

Use uv for dependency management:
```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project and add dependencies
uv init
uv add langgraph langchain-anthropic python-dotenv

# Run the program
uv run python main.py
```

Create a .env file with your API key:
```
ANTHROPIC_API_KEY=your-key-here
```

## Architecture
```
User Input → Coordinator → Prioritization Agent → Output
                        → Discovery Agent      → Output
```

## State
```python
{
    "user_input": str,           # Original problem statement
    "classification": str,       # "prioritization" or "discovery"
    "classification_reasoning": str,  # Why coordinator chose this
    "agent_output": str          # Final response from specialist
}
```

---

## Coordinator Agent

### Purpose
Classify the problem type and explain the classification before routing.

### Input
User's problem statement

### Output
- `classification`: one of ["prioritization", "discovery"]
- `classification_reasoning`: 2-3 sentences explaining why

### Classification Logic

Route to **Prioritization** when:
- User has multiple options and needs to choose/rank
- Resource constraints force trade-offs
- Stakeholders disagree on what to do first
- Keywords: "decide", "prioritize", "trade-off", "limited resources", "what to build first"

Route to **Discovery** when:
- User needs to understand a problem space
- User is exploring stakeholders, constraints, or unknowns
- User is new to a domain and needs to map it
- Keywords: "understand", "discover", "research", "map", "identify", "surface"

### Prompt Direction
```
You are a PM coach coordinator. Your job is to:
1. Read the user's problem statement
2. Classify it as either "prioritization" or "discovery"
3. Explain your classification in 2-3 sentences

Prioritization problems involve choosing between options, ranking, trade-offs, or resource allocation.
Discovery problems involve understanding, researching, mapping stakeholders, or surfacing hidden information.

Respond in this exact format:
CLASSIFICATION: [prioritization or discovery]
REASONING: [2-3 sentences explaining why]
```

---

## Prioritization Agent

### Purpose
Help user think through trade-off decisions using structured frameworks.

### Input
- User's original problem statement
- (Knows it was classified as prioritization)

### Output Format
1. **Context restatement**: 1-2 sentences showing you understood the problem
2. **Framework selection**: Which framework fits and why (RICE, MoSCoW, etc.)
3. **Analysis table**: Markdown table with scores/rankings
4. **Recommendation**: Clear recommendation with reasoning
5. **Caveats**: What assumptions you made, what you'd want to validate

### Frameworks Available
- RICE (Reach, Impact, Confidence, Effort)
- MoSCoW (Must/Should/Could/Won't)
- Value vs. Effort matrix
- Weighted scoring

### Prompt Direction
```
You are a senior PM helping with prioritization decisions. 

When given a problem:
1. Restate the core trade-off in 1-2 sentences
2. Select the most appropriate framework (RICE, MoSCoW, Value vs Effort, or weighted scoring) and explain why
3. Apply the framework with a markdown table
4. Give a clear recommendation with reasoning
5. Note your assumptions and what you'd validate

Be specific to their situation. Don't give generic framework explanations—apply it to their actual problem.

If you need more information to score accurately, state your assumptions explicitly rather than asking questions.
```

---

## Discovery Agent

### Purpose
Help user explore and map problem spaces, stakeholders, and hidden constraints.

### Input
- User's original problem statement
- (Knows it was classified as discovery)

### Output Format
1. **Problem framing**: What are you actually trying to discover?
2. **Discovery dimensions**: Key areas to explore (stakeholders, constraints, context, etc.)
3. **Specific questions**: 5-10 concrete questions to investigate
4. **Recommended sequence**: What order to tackle discovery, and why
5. **Blindspot warning**: What's easy to miss in this type of discovery

### Frameworks Available
- Stakeholder mapping (power/interest grid)
- Jobs-to-be-Done
- Assumption mapping
- 5 Whys
- Context mapping

### Prompt Direction
```
You are a senior PM helping with discovery and research.

When given a problem:
1. Frame what the user is actually trying to discover (the underlying question)
2. Identify 3-5 discovery dimensions relevant to their situation
3. Generate 5-10 specific, concrete questions they should investigate
4. Recommend a sequence for discovery with reasoning
5. Warn about common blindspots for this type of discovery

Be specific to their situation. Don't give generic discovery advice—tailor to their actual domain and context.

Assume they're smart but new to this specific problem. Give them a roadmap, not a lecture.
```

---

## Test Cases

### Prioritization Test
**Input:** "You're building a new feature with limited engineering resources. Your CEO wants Feature A (high visibility, demo-able), your biggest customer wants Feature B (threatens churn), and your data shows Feature C has the highest usage potential. Walk me through how you'd decide what to build."

**Expected behavior:**
- Coordinator classifies as "prioritization"
- Reasoning mentions: multiple options, resource constraints, stakeholder disagreement
- Agent produces RICE or weighted scoring table with A/B/C compared
- Clear recommendation with reasoning

### Discovery Test
**Input:** "You're a PM assigned to a problem in a domain you've never worked in ('Total Category Optimization'). You have 2 weeks before your first stakeholder meeting. What information do you need to surface, and in what order?"

**Expected behavior:**
- Coordinator classifies as "discovery"
- Reasoning mentions: new domain, need to understand/map, research phase
- Agent produces discovery dimensions, specific questions, sequenced approach
- Warns about blindspots (e.g., assuming you know the vocabulary)

---

## File Structure
```
master-pm-agents/
├── main.py              # All code lives here
├── CLAUDE.md            # Code style preferences
├── SPEC.md              # This file
├── pyproject.toml       # Created by uv init
├── uv.lock              # Created by uv add
├── .env                 # ANTHROPIC_API_KEY (create this)
└── Source_Documents/    # Reference material
```

## Implementation Notes

- Start with hardcoded prompts in main.py
- Use print statements to show state at each step
- Parse coordinator output with simple string matching (not regex)
- No error handling beyond basic try/except with print
- Run with: `uv run python main.py`