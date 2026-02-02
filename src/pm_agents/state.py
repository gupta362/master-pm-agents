"""State definition for the PM workflow."""

from typing import TypedDict


class State(TypedDict):
    """
    State passed through the LangGraph workflow.

    Think of this like a dict that gets passed through a pipeline.
    Each node (function) reads from it and adds to it.
    """
    user_input: str                  # Original problem statement
    classification: str              # One of: prioritization, problem_space, context_mapping, constraints, solution_validation
    classification_reasoning: str    # Why coordinator chose this
    agent_output: str                # Final response from specialist
    # New fields for generative discovery behavior
    soft_guesses: list               # [{"guess": "...", "confidence": "...", "validation_question": "..."}]
    validation_questions: list       # [{"question": "...", "priority": "...", "context": "..."}]
