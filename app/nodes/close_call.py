from app.state import AgentState
from utils.prompt_loader import load_prompt
from langchain_core.messages import AIMessage

def close_call_node(state: AgentState):
    """
    Placeholder for any cleanup or logging.
    """
    # In a real system, we might log the call summary here.
    msg = load_prompt("close_call_message")
    return {"messages": [AIMessage(content=msg)]}
