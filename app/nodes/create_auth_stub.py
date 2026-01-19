from app.state import AgentState
from utils.prompt_loader import load_prompt
from langchain_core.messages import AIMessage

def create_auth_stub_node(state: AgentState):
    """
    Stub for create auth workflow.
    """
    msg = load_prompt("create_auth_stub_message")
    return {
        "messages": [AIMessage(content=msg)],
        "intent": "unknown",
        "patient_info": None,
        "auth_info": None,
        "patient_validation_status": None,
        "patient_retry_count": 0,
        "db_matched_patient": None,
        "auth_lookup_result": None
    }
