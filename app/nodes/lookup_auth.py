import json
import os
from app.state import AgentState
from datetime import datetime

def lookup_auth_node(state: AgentState):
    """
    Looks up the authorization status in the JSON data.
    """
    patient = state.get("patient_info")
    auth = state.get("auth_info")
    
    if not patient or not auth:
        return {"auth_lookup_result": {"error": "Missing patient or auth info"}}
        
    # Load data
    # Adjust path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(base_dir, "data", "prior_auths.json")
    
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"auth_lookup_result": {"error": "Database not found"}}
        
    # Search logic
    # Search logic
    found_patient = None
    for p in data:
        # Match using patient_id
        data_mem_id = str(p.get("patient_id", "")).strip()
        input_mem_id = str(patient.member_id).strip()
        
        if data_mem_id == input_mem_id:
            found_patient = p
            break
            
    if not found_patient:
        return {"auth_lookup_result": {"status": "Patient not found", "details": "No member found with that ID."}}
        
    # Patient found (found_patient)
    
    # Search Auth
    found_auth = None
    
    # 1. Check Auth ID if provided
    if auth.auth_id:
        norm_input = str(auth.auth_id).strip().lower().replace(".", "")
        print(f"DEBUG: lookup_auth checking input ID '{norm_input}'")
        for a in found_patient.get("prior_auths", []):
            db_id = str(a.get("auth_id", "")).strip().lower().replace(".", "")
            print(f"DEBUG: Comparing against DB ID '{db_id}'")
            if db_id == norm_input:
                found_auth = a
                break
        
        if found_auth:
             return {"auth_lookup_result": found_auth}
        else:
             # Auth ID provided but NOT found. 
             # We must let the user know and ask for procedure.
             return {"auth_lookup_result": {"status": "auth_id_not_found", "details": f"Authorization ID {auth.auth_id}"}}

    # 2. Check Procedure if provided (and Auth ID was empty, or we would have returned above)
    if auth.procedure_description:
         p_desc = auth.procedure_description.lower()
         for a in found_patient.get("prior_auths", []):
             if p_desc in a.get("procedure_description", "").lower() or \
                p_desc in a.get("procedure_code", "").lower():
                 found_auth = a
                 break
                 
         if found_auth:
              return {"auth_lookup_result": found_auth}
         else:
              return {"auth_lookup_result": {"status": "no_info_found"}}

    # 3. Neither provided? (Should differ from collect_info loop)
    # If we are here, likely collect_info didn't get enough info, but sent us here?
    # Or maybe user said "I don't know anything".
    return {"auth_lookup_result": {"status": "no_info_found"}}
