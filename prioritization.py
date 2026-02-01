"""
Prioritization Agent
Helps with trade-off decisions using frameworks like RICE, MoSCoW, etc.
"""

PROMPT = """You are a senior PM helping with prioritization decisions.

When given a problem:
1. Restate the core trade-off in 1-2 sentences
2. Select the most appropriate framework (RICE, MoSCoW, Value vs Effort, or weighted scoring) and explain why
3. Apply the framework with a markdown table
4. Give a clear recommendation with reasoning
5. Note your assumptions and what you'd validate

Be specific to their situation. Don't give generic framework explanations—apply it to their actual problem.

If you need more information to score accurately, state your assumptions explicitly rather than asking questions."""


def run_agent(user_input: str, llm) -> str:
    """
    Run the prioritization agent and return the response.

    Args:
        user_input: The user's problem statement
        llm: The LLM instance to use for generating responses

    Returns:
        The agent's response as a string
    """
    print("\n" + "="*50)
    print("PRIORITIZATION AGENT")
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
    Stream the prioritization agent's response token by token.

    Args:
        user_input: The user's problem statement
        llm_streaming: The streaming LLM instance

    Yields:
        Individual tokens as they're generated
    """
    print("\n" + "="*50)
    print("PRIORITIZATION AGENT (STREAMING)")
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
