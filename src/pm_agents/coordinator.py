"""
Coordinator Agent
Classifies problems and routes to the appropriate specialist agent.

Currently supports 5 agent types (with room to expand to ~10):
- prioritization: Trade-offs and ranking decisions
- problem_space: Validating if problems exist and matter
- context_mapping: Learning new domains and stakeholders
- constraints: Surfacing hidden limitations
- solution_validation: Validating solutions against 4 risks
"""

PROMPT = """You are a PM coach coordinator. Your job is to:
1. Read the user's problem statement
2. Classify it into ONE of these 5 categories
3. Explain your classification in 2-3 sentences

## Categories

**prioritization**
Use when: Choosing between options, ranking, trade-offs, resource allocation, deciding what to build first.
Examples: "Should we build A or B?", "How do I prioritize these features?", "Which project is more important?"

**problem_space**
Use when: Validating if a problem actually exists and matters. User is uncertain if the pain point is real.
Examples: "I think users struggle with X, but not sure if real problem", "Is this actually a problem worth solving?", "Do customers really care about this?"

**context_mapping**
Use when: User needs to learn/map an unfamiliar domain, organization, or stakeholder landscape.
Examples: "Just joined team, need to learn the domain", "Who are the key stakeholders?", "I don't understand how this space works"

**constraints**
Use when: User suspects hidden blockers or limitations but can't articulate them. Something is blocking progress.
Examples: "Engineering keeps saying 'won't work' but I don't know why", "What am I missing?", "Why can't we do this?"

**solution_validation**
Use when: User has a solution idea and wants to validate if it's a good idea (value, usability, feasibility, viability).
Examples: "Want to build X. Is this a good idea?", "Will this solution work?", "Should we proceed with this approach?"

## Response Format
Respond in this exact format:
CLASSIFICATION: [prioritization, problem_space, context_mapping, constraints, or solution_validation]
REASONING: [2-3 sentences explaining why this category fits]"""


def parse_response(response_text: str) -> tuple[str, str]:
    """
    Parse the coordinator's response to extract classification and reasoning.

    Args:
        response_text: Raw text response from the LLM

    Returns:
        Tuple of (classification, reasoning)
    """
    # Valid classifications (order matters for matching)
    valid_classifications = [
        "solution_validation",  # Check longer names first
        "context_mapping",
        "problem_space",
        "prioritization",
        "constraints",
    ]

    classification = "problem_space"  # default fallback for unknown
    reasoning = ""

    lines = response_text.strip().split("\n")
    for line in lines:
        if line.upper().startswith("CLASSIFICATION:"):
            value = line.split(":", 1)[1].strip().lower()
            # Find matching classification
            for valid in valid_classifications:
                if valid in value:
                    classification = valid
                    break
        elif line.upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    # Sometimes reasoning spans multiple lines
    if not reasoning:
        for i, line in enumerate(lines):
            if line.upper().startswith("REASONING:"):
                reasoning = " ".join(lines[i:]).replace("REASONING:", "").strip()
                break

    return classification, reasoning


def run_coordinator(user_input: str, llm) -> tuple[str, str]:
    """
    Run the coordinator to classify the problem.

    Args:
        user_input: The user's problem statement
        llm: The LLM instance

    Returns:
        Tuple of (classification, reasoning)
    """
    print("\n" + "="*50)
    print("COORDINATOR AGENT")
    print("="*50)
    print(f"Input: {user_input[:100]}...")

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_input}
    ]
    response = llm.invoke(messages)
    response_text = response.content

    print(f"\nRaw response:\n{response_text}")

    classification, reasoning = parse_response(response_text)

    print(f"\nParsed classification: {classification}")
    print(f"Parsed reasoning: {reasoning}")

    return classification, reasoning
