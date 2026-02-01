"""
LangGraph workflow for the PM brainstorming system.
Orchestrates the coordinator and specialist agents.
"""

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic

from .state import State
from .coordinator import run_coordinator, PROMPT as COORDINATOR_PROMPT
from .agents import run_prioritization, run_discovery, stream_prioritization, stream_discovery

# Initialize LLMs
llm = ChatAnthropic(model="claude-sonnet-4-20250514")
llm_streaming = ChatAnthropic(model="claude-sonnet-4-20250514", streaming=True)


# --------------------
# GRAPH NODES
# --------------------

def coordinator_node(state: State) -> State:
    """Classify the problem and explain why."""
    classification, reasoning = run_coordinator(state["user_input"], llm)
    return {
        **state,
        "classification": classification,
        "classification_reasoning": reasoning
    }


def prioritization_agent_node(state: State) -> State:
    """Help user with prioritization using structured frameworks."""
    output = run_prioritization(state["user_input"], llm)
    return {**state, "agent_output": output}


def discovery_agent_node(state: State) -> State:
    """Help user with discovery and research."""
    output = run_discovery(state["user_input"], llm)
    return {**state, "agent_output": output}


def route_to_specialist(state: State) -> str:
    """Route to the appropriate specialist based on classification."""
    print(f"\n--> Routing to: {state['classification']}_agent")
    return state["classification"] + "_agent"


# --------------------
# BUILD GRAPH
# --------------------

def build_graph():
    """Build the LangGraph workflow."""
    graph = StateGraph(State)

    # Add nodes
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("prioritization_agent", prioritization_agent_node)
    graph.add_node("discovery_agent", discovery_agent_node)

    # Set entry point
    graph.set_entry_point("coordinator")

    # Add conditional routing
    graph.add_conditional_edges(
        "coordinator",
        route_to_specialist,
        {
            "prioritization_agent": "prioritization_agent",
            "discovery_agent": "discovery_agent"
        }
    )

    # Both specialists end the workflow
    graph.add_edge("prioritization_agent", END)
    graph.add_edge("discovery_agent", END)

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
        "agent_output": ""
    }

    final_state = workflow.invoke(initial_state)

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
    classification, reasoning = run_coordinator(user_input, llm)
    yield ("coordinator", {"classification": classification, "reasoning": reasoning})

    # Stream specialist agent
    full_output = ""
    if classification == "prioritization":
        for token in stream_prioritization(user_input, llm_streaming):
            full_output += token
            yield ("token", token)
    else:
        for token in stream_discovery(user_input, llm_streaming):
            full_output += token
            yield ("token", token)

    print("\n" + "="*50)
    print("STREAMING COMPLETE")
    print("="*50)

    yield ("done", full_output)
