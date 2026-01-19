from app.state import AgentState
from utils.prompt_loader import load_prompt
from langchain_core.messages import AIMessage

def reset_menu_node(state: AgentState):
    """
    Resets the conversation state and displays the main menu options.
    Used when the user says "Yes" to "Anything else?" but doesn't specify an intent.
    """
    msg_content = load_prompt("menu_prompt")
    
    # Force clear all context variables
    # Set scope to start *after* the current messages (including the one being added)
    # Since we add 1 message, the next user message will be at len(messages) + 1.
    # But wait, we want to include the AI prompt "How can I help" as context?
    # If we set index to len(messages), it points to the NEW message (AI Message).
    # Then user reply is len+1.
    # Included AI message is fine.
    
    return {
        "messages": [AIMessage(content=msg_content)],
        "intent": "unknown", 
        "patient_info": None,
        "auth_info": None,
        "patient_validation_status": None,
        "patient_retry_count": 0,
        "db_matched_patient": None,
        "auth_lookup_result": None,
        "scope_start_index": len(state["messages"]) 
    }
