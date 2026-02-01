"""State definition for the PM workflow."""

from typing import TypedDict


class State(TypedDict):
    """
    State passed through the LangGraph workflow.

    Think of this like a dict that gets passed through a pipeline.
    Each node (function) reads from it and adds to it.
    """
    user_input: str                  # Original problem statement
    classification: str              # "prioritization" or "discovery"
    classification_reasoning: str    # Why coordinator chose this
    agent_output: str                # Final response from specialist
