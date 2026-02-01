"""
Multi-agent PM brainstorming system.
User provides problem statement → Coordinator classifies → Routes to specialist agent.
"""

from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic

# Import specialist agents
import prioritization
import discovery

# Initialize the LLM - using Claude
# Regular LLM for coordinator (no streaming needed)
llm = ChatAnthropic(model="claude-sonnet-4-20250514")

# Streaming LLM for specialist agents (used by Streamlit UI)
llm_streaming = ChatAnthropic(model="claude-sonnet-4-20250514", streaming=True)

# --------------------
# STATE
# --------------------
# Think of this like a dict that gets passed through a pipeline
# Each node (function) reads from it and adds to it

class State(TypedDict):
    user_input: str                  # Original problem statement
    classification: str              # "prioritization" or "discovery"
    classification_reasoning: str    # Why coordinator chose this
    agent_output: str                # Final response from specialist


# --------------------
# COORDINATOR NODE
# --------------------
# First stop in the pipeline - classifies the problem and explains why

COORDINATOR_PROMPT = """You are a PM coach coordinator. Your job is to:
1. Read the user's problem statement
2. Classify it as either "prioritization" or "discovery"
3. Explain your classification in 2-3 sentences

Prioritization problems involve choosing between options, ranking, trade-offs, or resource allocation.
Discovery problems involve understanding, researching, mapping stakeholders, or surfacing hidden information.

Respond in this exact format:
CLASSIFICATION: [prioritization or discovery]
REASONING: [2-3 sentences explaining why]"""

def coordinator_node(state: State) -> State:
    """Classify the problem and explain why."""
    print("\n" + "="*50)
    print("COORDINATOR AGENT")
    print("="*50)
    print(f"Input: {state['user_input'][:100]}...")

    # Call the LLM
    messages = [
        {"role": "system", "content": COORDINATOR_PROMPT},
        {"role": "user", "content": state["user_input"]}
    ]
    response = llm.invoke(messages)
    response_text = response.content

    print(f"\nRaw response:\n{response_text}")

    # Parse the response with simple string matching
    # Looking for "CLASSIFICATION: prioritization" or "CLASSIFICATION: discovery"
    classification = "discovery"  # default fallback
    reasoning = ""

    lines = response_text.strip().split("\n")
    for line in lines:
        if line.upper().startswith("CLASSIFICATION:"):
            # Get everything after "CLASSIFICATION:"
            value = line.split(":", 1)[1].strip().lower()
            if "prioritization" in value:
                classification = "prioritization"
            else:
                classification = "discovery"
        elif line.upper().startswith("REASONING:"):
            # Get everything after "REASONING:"
            reasoning = line.split(":", 1)[1].strip()

    # Sometimes reasoning spans multiple lines after REASONING:
    # If reasoning is empty, grab everything after the classification line
    if not reasoning:
        for i, line in enumerate(lines):
            if line.upper().startswith("REASONING:"):
                reasoning = " ".join(lines[i:]).replace("REASONING:", "").strip()
                break

    print(f"\nParsed classification: {classification}")
    print(f"Parsed reasoning: {reasoning}")

    return {
        **state,
        "classification": classification,
        "classification_reasoning": reasoning
    }


# --------------------
# ROUTER
# --------------------
# Decides which specialist agent to call based on classification

def route_to_specialist(state: State) -> str:
    """Route to the appropriate specialist based on classification."""
    print(f"\n--> Routing to: {state['classification']}_agent")
    return state["classification"] + "_agent"


# --------------------
# SPECIALIST AGENT NODES
# --------------------
# These wrap the imported agent modules for use in LangGraph

def prioritization_agent_node(state: State) -> State:
    """Help user with prioritization using structured frameworks."""
    output = prioritization.run_agent(state["user_input"], llm)
    return {**state, "agent_output": output}


def discovery_agent_node(state: State) -> State:
    """Help user with discovery and research."""
    output = discovery.run_agent(state["user_input"], llm)
    return {**state, "agent_output": output}


# --------------------
# BUILD THE GRAPH
# --------------------
# This is like defining the order of functions in a pipeline

def build_graph():
    """Build the LangGraph workflow."""

    # Create a new graph with our State schema
    graph = StateGraph(State)

    # Add nodes (functions that process state)
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("prioritization_agent", prioritization_agent_node)
    graph.add_node("discovery_agent", discovery_agent_node)

    # Set the entry point - where the pipeline starts
    graph.set_entry_point("coordinator")

    # Add conditional routing from coordinator to specialists
    # route_to_specialist returns either "prioritization_agent" or "discovery_agent"
    graph.add_conditional_edges(
        "coordinator",
        route_to_specialist,
        {
            "prioritization_agent": "prioritization_agent",
            "discovery_agent": "discovery_agent"
        }
    )

    # Both specialist agents end the workflow
    graph.add_edge("prioritization_agent", END)
    graph.add_edge("discovery_agent", END)

    # Compile and return
    return graph.compile()


# --------------------
# RUN FUNCTION
# --------------------

def run(user_input: str):
    """Run the PM brainstorming system with a user input."""
    print("\n" + "#"*60)
    print("PM BRAINSTORMING SYSTEM")
    print("#"*60)
    print(f"\nUser input: {user_input}")

    # Build the graph
    workflow = build_graph()

    # Create initial state
    initial_state = {
        "user_input": user_input,
        "classification": "",
        "classification_reasoning": "",
        "agent_output": ""
    }

    # Run the workflow
    final_state = workflow.invoke(initial_state)

    # Print final results
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


# --------------------
# STREAMING RUN FUNCTION (for Streamlit UI)
# --------------------

def run_streaming(user_input: str):
    """
    Run the PM system with streaming output for the UI.

    Yields tuples of (event_type, data):
    - ("coordinator", {"classification": str, "reasoning": str})
    - ("token", str)  # streaming tokens from specialist
    - ("done", full_output_str)
    """
    print("\n" + "#"*60)
    print("PM BRAINSTORMING SYSTEM (STREAMING)")
    print("#"*60)
    print(f"\nUser input: {user_input}")

    # Step 1: Run coordinator to classify
    print("\n" + "="*50)
    print("COORDINATOR AGENT")
    print("="*50)

    messages = [
        {"role": "system", "content": COORDINATOR_PROMPT},
        {"role": "user", "content": user_input}
    ]
    response = llm.invoke(messages)
    response_text = response.content

    print(f"\nRaw response:\n{response_text}")

    # Parse classification (same logic as coordinator_node)
    classification = "discovery"
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

    if not reasoning:
        for i, line in enumerate(lines):
            if line.upper().startswith("REASONING:"):
                reasoning = " ".join(lines[i:]).replace("REASONING:", "").strip()
                break

    print(f"\nParsed classification: {classification}")
    print(f"Parsed reasoning: {reasoning}")

    # Yield coordinator result to UI
    yield ("coordinator", {"classification": classification, "reasoning": reasoning})

    # Step 2: Stream specialist agent response
    full_output = ""
    if classification == "prioritization":
        for token in prioritization.stream_agent(user_input, llm_streaming):
            full_output += token
            yield ("token", token)
    else:
        for token in discovery.stream_agent(user_input, llm_streaming):
            full_output += token
            yield ("token", token)

    print("\n" + "="*50)
    print("STREAMING COMPLETE")
    print("="*50)

    yield ("done", full_output)


# --------------------
# TEST CASES
# --------------------

if __name__ == "__main__":

    # TEST 1: Prioritization
    print("\n" + "~"*70)
    print("TEST 1: PRIORITIZATION SCENARIO")
    print("~"*70)

    prioritization_input = """You're building a new feature with limited engineering resources.
Your CEO wants Feature A (high visibility, demo-able), your biggest customer wants Feature B
(threatens churn), and your data shows Feature C has the highest usage potential.
Walk me through how you'd decide what to build."""

    run(prioritization_input)

    print("\n\n")

    # TEST 2: Discovery
    print("\n" + "~"*70)
    print("TEST 2: DISCOVERY SCENARIO")
    print("~"*70)

    discovery_input = """You're a PM assigned to a problem in a domain you've never worked in
('Total Category Optimization'). You have 2 weeks before your first stakeholder meeting.
What information do you need to surface, and in what order?"""

    run(discovery_input)
