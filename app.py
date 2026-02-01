"""
Streamlit chat UI for PM Brainstorming System.

Run with: uv run streamlit run app.py
"""

import streamlit as st
from pm_agents import run_streaming

st.title("PM Brainstorming Assistant")
st.caption("Ask me about prioritization decisions or discovery challenges")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # If message has coordinator info, show it first
        if "coordinator" in message:
            st.info(
                f"**Classification:** {message['coordinator']['classification']}\n\n"
                f"**Reasoning:** {message['coordinator']['reasoning']}"
            )
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Describe your PM problem..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        # Placeholder for coordinator result
        coordinator_placeholder = st.empty()
        # Placeholder for streaming response
        response_placeholder = st.empty()

        # Run the streaming workflow
        full_response = ""
        coordinator_data = None

        for event_type, data in run_streaming(prompt):
            if event_type == "coordinator":
                # Show classification as an info box
                coordinator_data = data
                coordinator_placeholder.info(
                    f"**Classification:** {data['classification']}\n\n"
                    f"**Reasoning:** {data['reasoning']}"
                )

            elif event_type == "token":
                # Accumulate tokens and display with cursor
                full_response += data
                response_placeholder.markdown(full_response + "▌")

            elif event_type == "done":
                # Final update without cursor
                response_placeholder.markdown(full_response)

        # Add assistant message to chat history (with coordinator info)
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "coordinator": coordinator_data
        })
