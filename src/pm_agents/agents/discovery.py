"""
Discovery Agent
Helps explore and map problem spaces, stakeholders, and hidden constraints.
"""

PROMPT = """You are a senior PM helping with discovery and research.

When given a problem:
1. Frame what the user is actually trying to discover (the underlying question)
2. Identify 3-5 discovery dimensions relevant to their situation
3. Generate 5-10 specific, concrete questions they should investigate
4. Recommend a sequence for discovery with reasoning
5. Warn about common blindspots for this type of discovery

Be specific to their situation. Don't give generic discovery advice—tailor to their actual domain and context.

Assume they're smart but new to this specific problem. Give them a roadmap, not a lecture."""


def run_agent(user_input: str, llm) -> str:
    """
    Run the discovery agent and return the response.

    Args:
        user_input: The user's problem statement
        llm: The LLM instance to use for generating responses

    Returns:
        The agent's response as a string
    """
    print("\n" + "="*50)
    print("DISCOVERY AGENT")
    print("="*50)

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_input}
    ]
    response = llm.invoke(messages)

    print(f"\nAgent output:\n{response.content[:500]}...")

    return response.content


def stream_agent(user_input: str, llm_streaming):
    """
    Stream the discovery agent's response token by token.

    Args:
        user_input: The user's problem statement
        llm_streaming: The streaming LLM instance

    Yields:
        Individual tokens as they're generated
    """
    print("\n" + "="*50)
    print("DISCOVERY AGENT (STREAMING)")
    print("="*50)

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": user_input}
    ]

    for chunk in llm_streaming.stream(messages):
        token = chunk.content
        if token:
            print(token, end="", flush=True)
            yield token

    print()  # Newline after streaming
