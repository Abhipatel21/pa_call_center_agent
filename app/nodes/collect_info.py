from app.state import AgentState
from utils.llm import get_llm
from utils.prompt_loader import load_prompt
from langchain_core.messages import SystemMessage

def collect_info_node(state: AgentState):
    """
    Generates a question to collect missing information.
    """
    llm = get_llm()
    
    # Deterministic Override: If ID not found, ask to create new.
    # This prevents LLM from asking for name/DOB (hallucination/logic fail).
    if state.get("patient_validation_status") == "id_not_found":
        from langchain_core.messages import AIMessage
        msg = load_prompt("id_not_found_message")
        return {"messages": [AIMessage(content=msg)]}
    
    system_prompt = load_prompt("system")
    # Need to render collected info
    collected_prompt = load_prompt("collect_info", 
                                   provider_info=state.get("provider_info"),
                                   patient_info=state.get("patient_info"),
                                   # Pass validation status for prompts
                                   patient_validation_status=state.get("patient_validation_status"),
                                   patient_retry_count=state.get("patient_retry_count", 0),
                                   db_matched_patient=state.get("db_matched_patient"),
                                   
                                   auth_info=state.get("auth_info"),
                                   intent=state.get("intent", "unknown"),
                                   auth_lookup_result=state.get("auth_lookup_result"))
    
    print(f"DEBUG: collect_info prompt:\n{collected_prompt}")
                                   
    messages = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=collected_prompt)
    ] # + state["messages"] # We might want history to avoid repeating, but the prompt says "Ask for NEXT logical piece".
    
    # It's better to pass history so the LLM checks what was just asked.
    start_index = state.get("scope_start_index", 0)
    # We might want to include the message immediately preceding scope if it was the Bot's question?
    # But scope logic includes the Bot's "How would you like to proceed".
    messages.extend(state["messages"][start_index:])
    
    print("DEBUG: collect_info_node invoking LLM...")
    
    # Use raw invoke for streaming (removed Structured Output)
    # from schemas.response import AgentResponse
    # structured_llm = llm.with_structured_output(AgentResponse)
    
    response = llm.invoke(messages)
    print(f"DEBUG: collect_info_node response: {response.content}")
    
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content=response.content)]}
