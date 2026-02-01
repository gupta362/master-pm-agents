"""
Coordinator Agent
Classifies problems and routes to the appropriate specialist agent.
"""

PROMPT = """You are a PM coach coordinator. Your job is to:
1. Read the user's problem statement
2. Classify it as either "prioritization" or "discovery"
3. Explain your classification in 2-3 sentences

Prioritization problems involve choosing between options, ranking, trade-offs, or resource allocation.
Discovery problems involve understanding, researching, mapping stakeholders, or surfacing hidden information.

Respond in this exact format:
CLASSIFICATION: [prioritization or discovery]
REASONING: [2-3 sentences explaining why]"""


def parse_response(response_text: str) -> tuple[str, str]:
    """
    Parse the coordinator's response to extract classification and reasoning.

    Args:
        response_text: Raw text response from the LLM

    Returns:
        Tuple of (classification, reasoning)
    """
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
