from app.state import AgentState
from langchain_core.messages import AIMessage, SystemMessage
from utils.prompt_loader import load_prompt
from utils.llm import get_llm

def greeting_node(state: AgentState):
    """
    Generates the initial greeting message.
    """
    # Only greet if no messages exist yet
    if not state.get("messages"):
        prompt_text = load_prompt("greeting")
        
        # Invoke LLM to generate dynamic greeting
        llm = get_llm()
        # Use raw invoke for streaming
        resp = llm.invoke([SystemMessage(content=prompt_text)])
        
        return {"messages": [AIMessage(content=resp.content)]}
        
    return {}
