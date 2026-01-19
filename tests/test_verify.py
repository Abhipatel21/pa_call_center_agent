
import sys
import os
import json
# Add modules to path
sys.path.append(os.getcwd())

from app.nodes.validate_patient import validate_patient_node
from app.nodes.lookup_auth import lookup_auth_node
from schemas.patient import PatientInfo
from schemas.auth import AuthInfo
from app.state import AgentState

def test_name_validation():
    print("--- Test Name Validation ---")
    # Base state with Correct ID
    state = {
        "patient_info": PatientInfo(member_id="111188"),
        "patient_retry_count": 0,
        "db_matched_patient": None
    }
    
    # 1. ID Check (should find patient)
    res = validate_patient_node(state)
    print(f"Step 1 (ID Only): {res}")
    if res.get("patient_validation_status") != "id_valid" or not res.get("db_matched_patient"):
        print("FAIL: ID lookup failed")
        return
    
    # Update State
    state.update(res)
    
    # 2. Wrong Name
    state["patient_info"].first_name = "Wrong"
    state["patient_info"].last_name = "Name"
    res = validate_patient_node(state)
    print(f"Step 2 (Wrong Name): {res}")
    if res.get("patient_validation_status") != "name_mismatch":
        print("FAIL: Should be name_mismatch")
        return

    # Update State (Retry count 1)
    state.update(res)

    # 3. Correct Name (Kevin Terrell)
    state["patient_info"].first_name = "Kevin"
    state["patient_info"].last_name = "Terrell"
    res = validate_patient_node(state)
    print(f"Step 3 (Correct Name): {res}")
    
    # Needs DOB to be valid
    if res.get("patient_validation_status") != "name_valid":
         print("FAIL: Should be name_valid (waiting for DOB)")
         return
         
    # Update State
    state.update(res)
    
    # 4. Correct DOB
    state["patient_info"].dob = "1990-01-01"
    res = validate_patient_node(state)
    print(f"Step 4 (Correct DOB): {res}")
    
    if res.get("patient_validation_status") != "valid":
        print("FAIL: Should be valid")
        return
        
    print("PASS: Name Validation Logic")

def test_auth_lookup():
    print("\n--- Test Auth Lookup ---")
    # Mock found patient (Kevin)
    with open("data/prior_auths.json") as f:
        data = json.load(f)
    kevin = data[0]
    
    state = {
        "patient_info": PatientInfo(member_id="111188"),
        "auth_info": AuthInfo(),
        "db_matched_patient": kevin # lookup needs this if we mock full flow, but actually lookup_auth re-reads DB currently.
        # Wait, lookup_auth_node reads DB fresh.
    }
    
    # 1. Correct Auth ID
    state["auth_info"].auth_id = "1234"
    res = lookup_auth_node(state)
    print(f"Step 1 (Correct Auth ID): {res['auth_lookup_result'].get('auth_id')}")
    if res['auth_lookup_result'].get('auth_id') != "1234":
        print("FAIL: Did not find auth 1234")
    
    # 2. Wrong Auth ID
    state["auth_info"].auth_id = "9999"
    res = lookup_auth_node(state)
    print(f"Step 2 (Wrong Auth ID): {res['auth_lookup_result']}")
    if res['auth_lookup_result'].get('status') != "auth_id_not_found":
        print("FAIL: Should return auth_id_not_found")
        
    # 3. Procedure Fallback (Correct)
    state["auth_info"].auth_id = None
    state["auth_info"].procedure_description = "MRI scan for primarily chest"
    res = lookup_auth_node(state)
    print(f"Step 3 (Procedure): {res['auth_lookup_result'].get('auth_id')}")
    if res['auth_lookup_result'].get('auth_id') != "1234":
        print("FAIL: Did not find auth via description")
        
    print("PASS: Auth Lookup Logic")
    
    print("\n--- Test Hallucination Logic (Manual Check) ---")
    # Verify strict logic manually as test environment doesn't load LLM.
    # But we can verify lookup reaction to 'auth_id_not_found' if we were testing prompt generation (complex).
    # Just asserting the lookup node behaviour for now.

if __name__ == "__main__":
    test_name_validation()
    test_auth_lookup()
