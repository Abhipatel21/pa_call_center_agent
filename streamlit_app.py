import streamlit as st
import os
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import build_graph

# Page config
st.set_page_config(page_title="PA Call Center Agent", page_icon="📞")
st.title("Prior Authorization Call Center Agent")

# Initialize graph
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
    
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
# Initialize Thread configuration for LangGraph (mock thread id)
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())
    
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Display details sidebar
with st.sidebar:
    st.header("Debug Info")
    if st.checkbox("Show Graph State"):
        # We can't easily peek into the graph state without running it, 
        # but we can try to get the snapshot if persistence was enabled.
        st.write("Current Thread ID:", st.session_state.thread_id)

# Start Conversation (Greeting)
# If history is empty, trigger the agent to start
if not st.session_state.messages:
    # Trigger graph with empty input to get greeting
    # Use stream or invoke
    events = st.session_state.graph.stream({"messages": []}, config=config)
    
    for event in events:
        for key, value in event.items():
            if "messages" in value:
                for msg in value["messages"]:
                    if isinstance(msg, AIMessage):
                        st.session_state.messages.append(msg)
                        
    # Rerun to display greeting
    st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message.type):
        st.markdown(message.content)

# Chat input
if prompt := st.chat_input("Response..."):
    # Add user message to state
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
        
        # Helper to yield tokens for streaming
        def stream_response():
             # Stream the graph execution
             inputs = {"messages": [HumanMessage(content=prompt)]}
             
             for event in st.session_state.graph.stream(inputs, config=config):
                print(f"DEBUG: Streamlit event: {event}")
                for node_name, values in event.items():
                    if values and "messages" in values:
                        new_messages = values["messages"]
                        for msg in new_messages:
                            if isinstance(msg, AIMessage):
                                # Since graph yields full message, we yield it
                                # If we want character by character effect for "streaming look", we can simulate or 
                                # just yield the content. st.write_stream handles generator.
                                # But graph.stream with default mode yields chunks of State, where message is complete.
                                # To get token-by-token, we need stream_mode="messages" in LangGraph
                                # But that changes the event structure.
                                # For now, let's just yield the full content chunk which might appear as a "block" update, 
                                # OR if we want token streaming, we need deeper changes.
                                # User asked "why output not streaming", implying they want partial updates.
                                # Let's simulate for now or just yield content.
                                yield msg.content
                                # Update history
                                st.session_state.messages.append(msg)
    
        # Use st.write_stream
        full_response = st.write_stream(stream_response)
