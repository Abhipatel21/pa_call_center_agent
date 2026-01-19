from app.state import AgentState
from utils.llm import get_llm
from utils.prompt_loader import load_prompt
from schemas.patient import PatientInfo
from langchain_core.messages import SystemMessage

def collect_patient_node(state: AgentState):
    """
    Extracts patient information.
    """
    start_index = state.get("scope_start_index", 0)
    messages = state["messages"][start_index:]
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(PatientInfo)
    
    system_prompt = load_prompt("system")
    patient_prompt = load_prompt("patient_info")
    
    prompt = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=patient_prompt),
    ] + messages
    
    result = structured_llm.invoke(prompt)
    
    # --- Robust Fallback for ID Extraction ---
    # If LLM failed to extract member_id, but the user just provided a standalone ID/Number, force extract it.
    if not result.member_id:
        # Check FULL history for the last AI message, regardless of scope
        all_messages = state["messages"]
        if len(all_messages) >= 2:
            last_ai = all_messages[-2]
             
            # Check if AI asked for Patient ID
            ai_text = getattr(last_ai, "content", "").lower()
            if "patient id" in ai_text:
                last_user = all_messages[-1] # The current user message
                user_text = getattr(last_user, "content", "").strip()
                
                # Heuristic: If user text looks like a clean ID (alphanumeric, 4-15 chars, no spaces or mostly digits)
                # Remove basic punctuation
                clean_text = user_text.replace(".", "").replace("-", "")
                
                # Simple check: Is it alphanumeric and not too long? 
                # (Matches "1111111", "PA-123", "A123")
                if clean_text.isalnum() and 4 <= len(clean_text) <= 15:
                     result.member_id = user_text
    
    # Merge with existing info if present (simple overwrite for now)
    # Merge with existing
    current_patient = state.get("patient_info")
    if current_patient:
        # Update only non-null fields
        if result.first_name: current_patient.first_name = result.first_name
        if result.last_name: current_patient.last_name = result.last_name
        if result.dob: current_patient.dob = result.dob
        if result.member_id: current_patient.member_id = result.member_id
        final_patient = current_patient
    else:
        final_patient = result
        
    return {"patient_info": final_patient}
