from app.state import AgentState
from utils.llm import get_llm
from utils.prompt_loader import load_prompt
from langchain_core.messages import SystemMessage, AIMessage

def respond_status_node(state: AgentState):
    """
    Generates the final status response based on lookup.
    """
    lookup_result = state.get("auth_lookup_result")
    
    llm = get_llm()
    system_prompt = load_prompt("system")
    status_prompt = load_prompt("status_response", lookup_result=lookup_result)
    
    messages = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=status_prompt)
    ]
    # Optionally include history if needed for context, but the prompt handles the summary.
    
    # Use raw invoke for streaming
    # from schemas.response import AgentResponse
    # structured_llm = llm.with_structured_output(AgentResponse)
    
    response = llm.invoke(messages)
    
    # clear session state so next inquiry starts fresh
    return {
        "messages": [AIMessage(content=response.content)],
        "intent": None,
        "patient_info": None,
        "auth_info": None,
        "patient_validation_status": None,
        "patient_retry_count": 0,
        "db_matched_patient": None,
        "auth_lookup_result": None
    }
