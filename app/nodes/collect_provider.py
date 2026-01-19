from app.state import AgentState
from utils.llm import get_llm
from utils.prompt_loader import load_prompt
from schemas.provider import ProviderInfo
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def collect_provider_node(state: AgentState):
    """
    Extracts provider information from the conversation.
    """
    messages = state["messages"]
    
    # If we already have provider info, we might skip or re-evaluate. 
    # But usually we check if it is complete.
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(ProviderInfo)
    
    system_prompt = load_prompt("system")
    provider_prompt = load_prompt("provider_info")
    
    # We want to extract info from the *existing* conversation
    extraction_prompt = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=provider_prompt),
    ] + messages
    
    result = structured_llm.invoke(extraction_prompt)
    
    # Update state
    # We update whatever we found. Completeness is checked by the router/logic.
    # However, if we found something new, we should store it.
    
    # Merge with existing state if needed? 
    # For now, just overwrite or update if not None.
    
    current_info = state.get("provider_info")
    if current_info:
        # Merge existing info with new result
        # If result has None, keep existing. If result has value, overwrite existing.
        # Handle "None" string case from LLM
        new_name = result.name
        if new_name and new_name.lower() == "none":
            new_name = None
            
        new_callback = result.callback_number
        if new_callback and new_callback.lower() == "none":
            new_callback = None
            
        final_name = new_name if new_name else current_info.name
        final_callback = new_callback if new_callback else current_info.callback_number
        
        merged_info = ProviderInfo(name=final_name, callback_number=final_callback)
        return {"provider_info": merged_info}
        
    return {"provider_info": result}
