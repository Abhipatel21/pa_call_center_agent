from app.state import AgentState
from utils.llm import get_llm
from utils.prompt_loader import load_prompt
from schemas.auth import AuthInfo
from langchain_core.messages import SystemMessage

def collect_auth_node(state: AgentState):
    """
    Extracts auth information.
    """
    start_index = state.get("scope_start_index", 0)
    messages = state["messages"][start_index:]
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(AuthInfo)
    
    system_prompt = load_prompt("system")
    auth_prompt = load_prompt("auth_info")
    
    prompt = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=auth_prompt),
    ] + messages
    
    result = structured_llm.invoke(prompt)
    
    # Anti-Hallucination Safe-Guard
    if result.auth_id:
        # Check against last user message
        # Use localized 'messages' (scoped)
        last_user_msg = ""
        for m in reversed(messages):
            if m.type == "human":
                last_user_msg = m.content.lower()
                break
        
        extracted_id = result.auth_id.lower().strip()
        
        # 1. Block specific hallucinations
        if "pa1234567890" in extracted_id:
             result.auth_id = None
             
        # 2. Verify existence in text (heuristic)
        elif extracted_id not in last_user_msg:
             # Relaxed check: Only blocks if strictly NOT present.
             # "1234" in "1234" is True.
             # "1234" in "I think it is 1234" is True.
             # "PA1234" in "1234" is False -> Blocked (Good).
             result.auth_id = None
        else:
             pass

    return {
        "auth_info": result,
    }
