import json
import os
from app.state import AgentState
from datetime import datetime

def validate_patient_node(state: AgentState):
    """
    Validates patient info against the database.
    Strict order: ID -> Name (First + Last) -> DOB.
    Updates patient_validation_status and patient_retry_count.
    """
    patient = state.get("patient_info")
    if not patient:
        return {} # Nothing to validate
        
    intent = state.get("intent")
    
    # Special Path for Create Auth: We don't check DB, just completeness.
    if intent == "create_auth":
        updates = {}
        # Check completeness
        has_id = bool(patient.member_id)
        has_name = bool(patient.first_name and patient.last_name)
        has_dob = bool(patient.dob)
        
        if has_id and has_name and has_dob:
            updates["patient_validation_status"] = "valid"
            updates["patient_retry_count"] = 0
            updates["db_matched_patient"] = None # No DB match needed
            print("DEBUG: validate_patient -> create_auth valid (all fields present)")
            return updates
        else:
            # If not complete, we rely on collect_info to ask.
            # But we need to set status to something that encourages collection?
            # Or just leave it as is?
            # collect_info looks for missing fields.
            # But route_after_validation needs "valid" to proceed to collect_auth.
            # So if not valid, we return empty/partial updates?
            # We should probably explicitly set status to 'collecting' or similar if we want to be safe, 
            # but current logic defaults to 'collect_info' if not valid.
            print(f"DEBUG: validate_patient -> create_auth incomplete. ID={has_id}, Name={has_name}, DOB={has_dob}")
            # we can set a dummy status like 'in_progress' to prevent errors?
            # actually if we return {}, route_after_validation sees status=None -> "collect_info". Correct.
            return {} 
            
    current_retry = state.get("patient_retry_count", 0)
        
    current_retry = state.get("patient_retry_count", 0)
    db_patient = state.get("db_matched_patient")
    
    # Load data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(base_dir, "data", "prior_auths.json")
    
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"patient_validation_status": "error_db"}

    # Helper: Normalize
    def norm(s): return str(s).strip().lower() if s else ""
    
    # Helper: Date Check
    def check_date(user_date_str, db_date_str):
        if not user_date_str or not db_date_str: return False
        try:
             d1 = datetime.strptime(user_date_str, "%Y-%m-%d")
             d2 = datetime.strptime(db_date_str, "%Y-%m-%d")
             return d1 == d2
        except ValueError:
            return norm(user_date_str) == norm(db_date_str)

    updates = {}
    
    # Pre-check: Did ID change?
    if db_patient and patient.member_id:
         if norm(patient.member_id) != norm(db_patient.get("patient_id")):
              db_patient = None
              updates["db_matched_patient"] = None
              updates["patient_retry_count"] = 0

    # 1. Check ID first.
    if not db_patient:
        if not patient.member_id:
            return {} 

        found_patient = None
        for p in data:
            if norm(p.get("patient_id")) == norm(patient.member_id):
                found_patient = p
                break
                
        if found_patient:
            updates["db_matched_patient"] = found_patient
            updates["patient_validation_status"] = "id_valid" # ID Found!
            print("DEBUG: validate_patient -> id_valid")
            return updates
        else:
            print("DEBUG: validate_patient -> id_not_found")
            return {"patient_validation_status": "id_not_found"}

    # 2. Check Name (First AND Last Name)
    # We have db_patient.
    
    # Needs both to proceed to verification
    if not patient.first_name or not patient.last_name:
        return {"patient_validation_status": "id_valid"} 
        
    # Check First Name AND Last Name
    db_first = norm(db_patient.get("first_name"))
    db_last = norm(db_patient.get("last_name"))
    
    user_first = norm(patient.first_name)
    user_last = norm(patient.last_name)
    
    # Strict Check
    if db_first != user_first or db_last != user_last:
        # WRONG Name
        new_retry = current_retry + 1
        updates["patient_retry_count"] = new_retry
        if new_retry >= 2: # 2nd fail
            updates["patient_validation_status"] = "end_failure"
        else:
            updates["patient_validation_status"] = "name_mismatch"
        return updates
        
    # Name Correct.
    
    # 3. Check DOB
    if not patient.dob:
        updates["patient_validation_status"] = "name_valid" # Need DOB
        updates["patient_retry_count"] = 0 # reset retry for DOB phase
        return updates
    
    # Check DOB
    if check_date(patient.dob, db_patient.get("dob")):
        # All Valid
        updates["patient_validation_status"] = "valid"
        updates["patient_retry_count"] = 0
        return updates
    else:
        # DOB Mismatch
        new_retry = current_retry + 1
        updates["patient_retry_count"] = new_retry
        updates["patient_validation_status"] = "dob_mismatch"
        return updates

    return updates
