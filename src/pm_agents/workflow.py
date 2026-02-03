"""
LangGraph workflow for the PM brainstorming system.
Orchestrates the coordinator and specialist agents.

Currently supports 5 specialist agents:
- prioritization: Trade-offs and ranking decisions
- problem_space: Validating if problems exist
- context_mapping: Learning domains and stakeholders
- constraints: Surfacing hidden limitations
- solution_validation: Validating against 4 risks

Future expansion planned to ~10 agents (Lens + Workflow types).
"""

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic

from .state import State
from .coordinator import (
    run_coordinator,
    run_refinement,
    extract_soft_guesses,
    PROMPT as COORDINATOR_PROMPT,
)
from .agents import (
    # Prioritization
    run_prioritization,
    stream_prioritization,
    # Problem Space (new)
    run_problem_space,
    stream_problem_space,
    # Context Mapping (new)
    run_context_mapping,
    stream_context_mapping,
    # Constraints (new)
    run_constraints,
    stream_constraints,
    # Solution Validation (new)
    run_solution_validation,
    stream_solution_validation,
)

# Initialize LLMs
# max_tokens=8192 ensures complete output for complex multi-section responses
# (agents can produce 4,000-7,000 tokens; default 1024 causes truncation)
llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=8192)
llm_streaming = ChatAnthropic(model="claude-sonnet-4-20250514", streaming=True, max_tokens=8192)


# --------------------
# OUTPUT QUALITY VALIDATION
# --------------------

def validate_agent_output(output: str) -> bool:
    """
    Check that agent output meets minimum quality requirements.

    Logs warnings but does not block - this is for monitoring output quality.

    Returns:
        True if output passes all checks, False if any issues found.
    """
    issues = []

    # Check for required sections
    required_sections = [
        "Questions for Your Next Stakeholder Meeting",
        "Must Validate",
    ]

    missing = [section for section in required_sections if section not in output]
    if missing:
        issues.append(f"Missing required sections: {missing}")

    # Check for vague language
    vague_phrases = [
        "proceed with caution",
        "it depends",
        "may or may not",
        "consider carefully",
        "could be viable",
    ]

    output_lower = output.lower()
    found_vague = [phrase for phrase in vague_phrases if phrase in output_lower]
    if found_vague:
        issues.append(f"Used vague language: {found_vague}")

    # Check for soft guesses without validation questions
    soft_guess_count = output.count("⚠️")
    if soft_guess_count > 0 and "Must Validate" not in output:
        issues.append(f"Found {soft_guess_count} soft guesses but no 'Must Validate' section")

    # Log warnings
    if issues:
        print("\n" + "!"*50)
        print("OUTPUT QUALITY WARNINGS:")
        for issue in issues:
            print(f"  ⚠️ {issue}")
        print("!"*50 + "\n")
        return False

    return True


# --------------------
# GRAPH NODES
# --------------------

def coordinator_node(state: State) -> State:
    """Classify the problem and explain why."""
    classification, reasoning, alternatives = run_coordinator(state["user_input"], llm)
    return {
        **state,
        "classification": classification,
        "classification_reasoning": reasoning,
        "classification_alternatives": alternatives,
    }


def prioritization_agent_node(state: State) -> State:
    """Help user with prioritization using structured frameworks."""
    output = run_prioritization(state["user_input"], llm)
    return {**state, "agent_output": output}


def problem_space_agent_node(state: State) -> State:
    """Help user validate if a problem exists and matters."""
    output = run_problem_space(state["user_input"], llm)
    return {**state, "agent_output": output}


def context_mapping_agent_node(state: State) -> State:
    """Help user map unfamiliar domains and stakeholders."""
    output = run_context_mapping(state["user_input"], llm)
    return {**state, "agent_output": output}


def constraints_agent_node(state: State) -> State:
    """Help user surface hidden limitations and blockers."""
    output = run_constraints(state["user_input"], llm)
    return {**state, "agent_output": output}


def solution_validation_agent_node(state: State) -> State:
    """Help user validate a solution against 4 risks."""
    output = run_solution_validation(state["user_input"], llm)
    return {**state, "agent_output": output}


def route_to_specialist(state: State) -> str:
    """Route to the appropriate specialist based on classification."""
    classification = state["classification"]
    print(f"\n--> Routing to: {classification}_agent")
    return classification + "_agent"


# --------------------
# BUILD GRAPH
# --------------------

def build_graph():
    """Build the LangGraph workflow."""
    graph = StateGraph(State)

    # Add nodes
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("prioritization_agent", prioritization_agent_node)
    graph.add_node("problem_space_agent", problem_space_agent_node)
    graph.add_node("context_mapping_agent", context_mapping_agent_node)
    graph.add_node("constraints_agent", constraints_agent_node)
    graph.add_node("solution_validation_agent", solution_validation_agent_node)

    # Set entry point
    graph.set_entry_point("coordinator")

    # Add conditional routing to all 5 specialist agents
    graph.add_conditional_edges(
        "coordinator",
        route_to_specialist,
        {
            "prioritization_agent": "prioritization_agent",
            "problem_space_agent": "problem_space_agent",
            "context_mapping_agent": "context_mapping_agent",
            "constraints_agent": "constraints_agent",
            "solution_validation_agent": "solution_validation_agent",
        }
    )

    # All specialists end the workflow
    graph.add_edge("prioritization_agent", END)
    graph.add_edge("problem_space_agent", END)
    graph.add_edge("context_mapping_agent", END)
    graph.add_edge("constraints_agent", END)
    graph.add_edge("solution_validation_agent", END)

    return graph.compile()


# --------------------
# RUN FUNCTIONS
# --------------------

def run(user_input: str) -> State:
    """Run the PM brainstorming system with a user input."""
    print("\n" + "#"*60)
    print("PM BRAINSTORMING SYSTEM")
    print("#"*60)
    print(f"\nUser input: {user_input}")

    workflow = build_graph()

    initial_state = {
        "user_input": user_input,
        "classification": "",
        "classification_reasoning": "",
        "agent_output": "",
        "soft_guesses": [],
        "validation_questions": [],
    }

    final_state = workflow.invoke(initial_state)

    # Validate output quality (logs warnings but doesn't block)
    validate_agent_output(final_state['agent_output'])

    print("\n" + "#"*60)
    print("FINAL RESULTS")
    print("#"*60)
    print(f"\nClassification: {final_state['classification']}")
    print(f"Reasoning: {final_state['classification_reasoning']}")
    print(f"\n{'='*50}")
    print("SPECIALIST AGENT OUTPUT:")
    print("="*50)
    print(final_state['agent_output'])

    return final_state


def run_streaming(user_input: str):
    """
    Run the PM system with streaming output for the UI.

    Yields tuples of (event_type, data):
    - ("coordinator", {"classification": str, "reasoning": str})
    - ("token", str)
    - ("done", full_output_str)
    """
    print("\n" + "#"*60)
    print("PM BRAINSTORMING SYSTEM (STREAMING)")
    print("#"*60)
    print(f"\nUser input: {user_input}")

    # Run coordinator
    classification, reasoning, alternatives = run_coordinator(user_input, llm)
    yield ("coordinator", {"classification": classification, "reasoning": reasoning, "alternatives": alternatives})

    # Stream specialist agent based on classification
    full_output = ""

    # Map classification to stream function
    stream_functions = {
        "prioritization": stream_prioritization,
        "problem_space": stream_problem_space,
        "context_mapping": stream_context_mapping,
        "constraints": stream_constraints,
        "solution_validation": stream_solution_validation,
    }

    # Get the appropriate stream function (default to problem_space)
    stream_fn = stream_functions.get(classification, stream_problem_space)

    for token in stream_fn(user_input, llm_streaming):
        full_output += token
        yield ("token", token)

    # Validate output quality (logs warnings but doesn't block)
    validate_agent_output(full_output)

    print("\n" + "="*50)
    print("STREAMING COMPLETE")
    print("="*50)

    yield ("done", full_output)


# --------------------
# STAGED WORKFLOW FUNCTIONS
# --------------------
# These functions support the human-in-the-loop checkpoint flow.
# Each stage is a generator that yields results for the UI to display.

def run_stage1_refinement(user_input: str):
    """
    Stage 1: Refine the problem statement.

    Makes vague inputs more specific and surfaces initial assumptions.

    Yields:
        ("refinement", {
            "refined_statement": str,
            "improvements": list[str],
            "soft_guesses": list[str]
        })
    """
    print("\n" + "#"*60)
    print("STAGE 1: REFINEMENT")
    print("#"*60)

    result = run_refinement(user_input, llm)
    yield ("refinement", result)


def run_stage2_classification(refined_input: str):
    """
    Stage 2: Classify the problem.

    Determines which specialist agent to route to.

    Yields:
        ("classification", {
            "classification": str,
            "reasoning": str,
            "alternatives": list[str]
        })
    """
    print("\n" + "#"*60)
    print("STAGE 2: CLASSIFICATION")
    print("#"*60)

    classification, reasoning, alternatives = run_coordinator(refined_input, llm)
    yield ("classification", {
        "classification": classification,
        "reasoning": reasoning,
        "alternatives": alternatives
    })


def run_stage3_soft_guesses(refined_input: str, classification: str):
    """
    Stage 3: Extract soft guesses (assumptions).

    Identifies key assumptions that could change the analysis if wrong.

    Yields:
        ("soft_guesses", list[{
            "topic": str,
            "assumption": str,
            "confidence": str,
            "reason": str
        }])
    """
    print("\n" + "#"*60)
    print("STAGE 3: SOFT GUESSES")
    print("#"*60)

    guesses = extract_soft_guesses(refined_input, classification, llm)
    yield ("soft_guesses", guesses)


def run_stage4_specialist(refined_input: str, classification: str, confirmed_guesses: list = None):
    """
    Stage 4: Run specialist agent with streaming.

    Incorporates confirmed guesses into the specialist context.

    Args:
        refined_input: The refined problem statement
        classification: Which specialist to use
        confirmed_guesses: List of user-confirmed assumptions to inject

    Yields:
        ("token", str) - streaming tokens
        ("done", str) - full output when complete
    """
    print("\n" + "#"*60)
    print("STAGE 4: SPECIALIST")
    print("#"*60)

    # Build context with confirmed guesses
    context = refined_input
    if confirmed_guesses:
        guesses_text = "\n".join([
            f"- {g['topic']}: {g['assumption']} (Confirmed)"
            for g in confirmed_guesses
        ])
        context = f"""{refined_input}

## Confirmed Assumptions
The following have been validated with the user:
{guesses_text}"""

    print(f"Context with guesses:\n{context[:200]}...")

    # Map classification to stream function
    stream_functions = {
        "prioritization": stream_prioritization,
        "problem_space": stream_problem_space,
        "context_mapping": stream_context_mapping,
        "constraints": stream_constraints,
        "solution_validation": stream_solution_validation,
    }

    stream_fn = stream_functions.get(classification, stream_problem_space)

    full_output = ""
    for token in stream_fn(context, llm_streaming):
        full_output += token
        yield ("token", token)

    # Validate output quality
    validate_agent_output(full_output)

    print("\n" + "="*50)
    print("SPECIALIST STREAMING COMPLETE")
    print("="*50)

    yield ("done", full_output)
