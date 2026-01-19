from app.state import AgentState
from utils.llm import get_llm
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

class ConfirmationDecision(BaseModel):
    decision: str = Field(description="'yes' or 'no' based on user confirmation")

def process_confirmation_node(state: AgentState):
    """
    Handles user response to data mismatch confirmation.
    If 'yes', updates patient_info with db_matched_patient.
    If 'no', clears patient info to restart collection? Or ends?
    Prompt says: "If user says yes then only ask about the authorization number".
    """
    messages = state["messages"]
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(ConfirmationDecision)
    
    system_prompt = "You are checking if the user confirmed the patient details (yes/no). Extract the decision."
    
    # Check last message
    prompt = [SystemMessage(content=system_prompt)] + messages[-1:]
    
    result = structured_llm.invoke(prompt)
    
    updates = {}
    
    if result.decision == "yes":
        # Override patient info with DB data
        db_patient = state.get("db_matched_patient")
        if db_patient:
            from schemas.patient import PatientInfo
            new_info = PatientInfo(
                first_name=db_patient.get("first_name"),
                last_name=db_patient.get("last_name"),
                dob=db_patient.get("dob"),
                member_id=db_patient.get("member_id")
            )
            updates["patient_info"] = new_info
            updates["patient_validation_status"] = "valid" # Mark valid to proceed
            updates["db_matched_patient"] = None
    else:
        # User said NO.
        # "If user says no then workflow should end with info that thanks..."
        updates["intent"] = "end_conversation" # Or verify end logic
        
    return updates
