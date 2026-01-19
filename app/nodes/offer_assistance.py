from app.state import AgentState
from utils.prompt_loader import load_prompt
from langchain_core.messages import AIMessage

def offer_assistance_node(state: AgentState):
    """
    Offers help if the user declined a specific suggestion (like creating an auth).
    """
    msg = load_prompt("offer_assistance_message")
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
