"""
Coordinator Agent
Classifies problems and routes to the appropriate specialist agent.

Currently supports 5 agent types (with room to expand to ~10):
- prioritization: Trade-offs and ranking decisions
- problem_space: Validating if problems exist and matter
- context_mapping: Learning new domains and stakeholders
- constraints: Surfacing hidden limitations
- solution_validation: Validating solutions against 4 risks

Also handles:
- Problem refinement (making vague inputs more specific)
- Soft guesses extraction (surfacing assumptions for validation)
"""

# --------------------
# PROMPTS
# --------------------

REFINEMENT_PROMPT = """You are a PM coach helping refine problem statements.

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
- Don't add fluff or corporate speak
"""

SOFT_GUESSES_PROMPT = """Identify 3-5 assumptions that would significantly change the analysis if wrong.

Based on the problem statement and classification, extract the key assumptions being made.

## Output Format
For each assumption, output on a single line:
- [Topic]: [What we're assuming] — Confidence: [High/Medium/Low] — [Brief reason]

## Focus On
- Who experiences this problem
- How severe/frequent it is
- What the current state looks like
- Why they're asking now
- What success looks like

## Example
- Target User: Enterprise customers with 100+ seats — Confidence: Medium — Not explicitly stated but implied by scale
- Severity: This is a blocking issue — Confidence: Low — Could just be annoying, not blocking
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
REASONING: [2-3 sentences explaining why this category fits]
ALTERNATIVES: [Comma-separated list of other categories that could partially fit, ranked by relevance. If none, write "None"]"""


def parse_response(response_text: str) -> tuple[str, str, list]:
    """
    Parse the coordinator's response to extract classification, reasoning, and alternatives.

    Args:
        response_text: Raw text response from the LLM

    Returns:
        Tuple of (classification, reasoning, alternatives)
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
    alternatives = []

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
        elif line.upper().startswith("ALTERNATIVES:"):
            alt_text = line.split(":", 1)[1].strip().lower()
            if alt_text and alt_text != "none":
                # Parse comma-separated alternatives
                for alt in alt_text.split(","):
                    alt = alt.strip()
                    for valid in valid_classifications:
                        if valid in alt:
                            if valid != classification:  # Don't include primary
                                alternatives.append(valid)
                            break

    # Sometimes reasoning spans multiple lines
    if not reasoning:
        for i, line in enumerate(lines):
            if line.upper().startswith("REASONING:"):
                # Get text until ALTERNATIVES line
                reasoning_lines = []
                for j in range(i, len(lines)):
                    if lines[j].upper().startswith("ALTERNATIVES:"):
                        break
                    reasoning_lines.append(lines[j])
                reasoning = " ".join(reasoning_lines).replace("REASONING:", "").strip()
                break

    return classification, reasoning, alternatives


def run_coordinator(user_input: str, llm) -> tuple[str, str, list]:
    """
    Run the coordinator to classify the problem.

    Args:
        user_input: The user's problem statement
        llm: The LLM instance

    Returns:
        Tuple of (classification, reasoning, alternatives)
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

    classification, reasoning, alternatives = parse_response(response_text)

    print(f"\nParsed classification: {classification}")
    print(f"Parsed reasoning: {reasoning}")
    print(f"Parsed alternatives: {alternatives}")

    return classification, reasoning, alternatives


# --------------------
# REFINEMENT FUNCTIONS
# --------------------

def parse_refinement_response(response_text: str) -> dict:
    """
    Parse the refinement response to extract structured data.

    Returns:
        Dict with keys: refined_statement, improvements, soft_guesses
    """
    result = {
        "refined_statement": "",
        "improvements": [],
        "soft_guesses": []
    }

    lines = response_text.strip().split("\n")
    current_section = None

    for line in lines:
        line_stripped = line.strip()

        if line_stripped.upper().startswith("REFINED_STATEMENT:"):
            current_section = "refined"
            result["refined_statement"] = line_stripped.split(":", 1)[1].strip()
        elif line_stripped.upper().startswith("IMPROVEMENTS_MADE:"):
            current_section = "improvements"
        elif line_stripped.upper().startswith("SOFT_GUESSES:"):
            current_section = "soft_guesses"
        elif line_stripped.startswith("- "):
            item = line_stripped[2:].strip()
            if current_section == "improvements":
                result["improvements"].append(item)
            elif current_section == "soft_guesses":
                result["soft_guesses"].append(item)
        elif current_section == "refined" and line_stripped:
            # Multi-line refined statement
            result["refined_statement"] += " " + line_stripped

    return result


def run_refinement(user_input: str, llm) -> dict:
    """
    Run the refinement step to make the problem statement more specific.

    Args:
        user_input: The user's original problem statement
        llm: The LLM instance

    Returns:
        Dict with keys: refined_statement, improvements, soft_guesses
    """
    print("\n" + "="*50)
    print("REFINEMENT STEP")
    print("="*50)
    print(f"Input: {user_input[:100]}...")

    messages = [
        {"role": "system", "content": REFINEMENT_PROMPT},
        {"role": "user", "content": user_input}
    ]
    response = llm.invoke(messages)
    response_text = response.content

    print(f"\nRaw response:\n{response_text}")

    result = parse_refinement_response(response_text)

    print(f"\nRefined statement: {result['refined_statement'][:100]}...")
    print(f"Improvements: {result['improvements']}")

    return result


# --------------------
# SOFT GUESSES EXTRACTION
# --------------------

def parse_soft_guesses_response(response_text: str) -> list:
    """
    Parse soft guesses response into structured list.

    Returns:
        List of dicts with keys: topic, assumption, confidence, reason
    """
    guesses = []
    lines = response_text.strip().split("\n")

    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("- "):
            # Parse format: "- [Topic]: [Assumption] — Confidence: [Level] — [Reason]"
            content = line_stripped[2:].strip()

            # Split by — (em-dash) or - (hyphen with spaces)
            parts = content.replace(" — ", " - ").split(" - ")

            if len(parts) >= 2:
                # First part: Topic: Assumption
                first_part = parts[0]
                if ":" in first_part:
                    topic, assumption = first_part.split(":", 1)
                else:
                    topic = "General"
                    assumption = first_part

                # Extract confidence if present
                confidence = "Medium"
                reason = ""
                for part in parts[1:]:
                    if "confidence" in part.lower():
                        conf_text = part.lower().replace("confidence:", "").replace("confidence", "").strip()
                        if "high" in conf_text:
                            confidence = "High"
                        elif "low" in conf_text:
                            confidence = "Low"
                        else:
                            confidence = "Medium"
                    else:
                        reason = part.strip()

                guesses.append({
                    "topic": topic.strip(),
                    "assumption": assumption.strip(),
                    "confidence": confidence,
                    "reason": reason
                })

    return guesses


def extract_soft_guesses(refined_input: str, classification: str, llm) -> list:
    """
    Extract soft guesses (assumptions) from the problem statement.

    Args:
        refined_input: The refined problem statement
        classification: The classification category
        llm: The LLM instance

    Returns:
        List of dicts with keys: topic, assumption, confidence, reason
    """
    print("\n" + "="*50)
    print("SOFT GUESSES EXTRACTION")
    print("="*50)

    context = f"""Problem Statement: {refined_input}

Classification: {classification}"""

    messages = [
        {"role": "system", "content": SOFT_GUESSES_PROMPT},
        {"role": "user", "content": context}
    ]
    response = llm.invoke(messages)
    response_text = response.content

    print(f"\nRaw response:\n{response_text}")

    guesses = parse_soft_guesses_response(response_text)

    print(f"\nParsed {len(guesses)} soft guesses")
    for g in guesses:
        print(f"  - {g['topic']}: {g['assumption'][:50]}... ({g['confidence']})")

    return guesses
