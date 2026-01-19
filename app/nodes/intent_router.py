from app.state import AgentState
from utils.llm import get_llm
from utils.prompt_loader import load_prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field

class IntentDecision(BaseModel):
    intent: str = Field(description="The determined intent: 'check_status', 'create_auth', 'end_conversation', or 'unknown'")
    is_new_request: bool = Field(False, description="True if the user is explicitly asking to start a NEW inquiry or check ANOTHER status. False if providing info for current inquiry.")

def intent_router_node(state: AgentState):
    """
    Determines the user's intent.
    """
    messages = state["messages"]
    
    # Heuristic: Check for "Anything else?" loop
    if len(messages) >= 2:
        last_user = messages[-1]
        last_ai = messages[-2]
        
        # Robustly get content regardless of object type (dict or object)
        ai_text = getattr(last_ai, "content", str(last_ai)).lower() if hasattr(last_ai, "content") else str(last_ai).lower()
        user_text = getattr(last_user, "content", str(last_user)).lower().strip() if hasattr(last_user, "content") else str(last_user).lower().strip()
        
        # 1. Menu Option Heuristics (Force New Request)
        # Check Status variants
        if "check" in user_text and ("status" in user_text or "auth" in user_text or "prior" in user_text) and not "create" in user_text:
             print("DEBUG: Heuristic -> check_status (New Request)")
             return {
                 "intent": "check_status",
                 # Force Clear Context
                 "patient_info": None,
                 "auth_info": None,
                 "patient_validation_status": None,
                 "patient_retry_count": 0,
                 "db_matched_patient": None,
                 "auth_lookup_result": None,
                 "scope_start_index": len(messages) - 1 # Scope starts at CURRENT user message
             }
             
        # Create Auth variants
        if ("create" in user_text or "new" in user_text) and ("auth" in user_text or "authorization" in user_text):
             print("DEBUG: Heuristic -> create_auth (New Request)")
             return {
                 "intent": "create_auth",
                 # Force Clear Context
                 "patient_info": None,
                 "auth_info": None,
                 "patient_validation_status": None,
                 "patient_retry_count": 0,
                 "db_matched_patient": None,
                 "auth_lookup_result": None,
                 "scope_start_index": len(messages) - 1 # Scope starts at CURRENT user message
             }
            
        # Check if AI asked about assistance OR if it was the stub message
        if "anything else" in ai_text or "assist you" in ai_text or "not fully implemented" in ai_text:
            # Check if user said yes
            affirmations = ["yes", "yeah", "sure", "ok", "okay", "yep"]
            
            # Relaxes check: just needs to start with or be an affirmation
            # But keep it safe to avoiding catching "Yes I want to create auth" as unknown?
            # Actually, prompt says if they say yes to "anything else", it's unknown/menu.
            
            user_tokens = user_text.split()
            if len(user_tokens) <= 5 and any(word in user_text for word in affirmations):
                return {
                    "intent": "menu_request", # New internal intent to show menu
                    "patient_info": None,
                    "auth_info": None,
                    "patient_validation_status": None,
                    "patient_retry_count": 0,
                    "db_matched_patient": None,
                    "auth_lookup_result": None
                }
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(IntentDecision)
    
    system_prompt = load_prompt("system")
    intent_prompt = load_prompt("intent")
    
    prompt = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=intent_prompt),
    ] + messages
    
    result = structured_llm.invoke(prompt)
    
    updates = {"intent": result.intent}
    
    # Stratgy: Check for Intent Switching or Explicit New Request
    current_intent = state.get("intent")
    
    # Logic to clear context:
    # 1. is_new_request is True (Explicit "check another", "start over")
    # 2. Switching from one valid intent to another (e.g. check_status -> create_auth)
    
    is_intent_switch = (current_intent in ["check_status", "create_auth"] and 
                        result.intent in ["check_status", "create_auth"] and 
                        current_intent != result.intent)
                        
    # Safety Check: The LLM sometimes flags data entry ("111", "Kevin") as is_new_request=True.
    # We only honor is_new_request if:
    # 1. The intent actually switched (handled by is_intent_switch).
    # 2. OR the user input contains explicit trigger keywords ("check", "new", "start", etc).
    
    triggers = ["check", "status", "auth", "prior", "create", "new", "start", "another", "reset", "menu"]
    user_content = getattr(messages[-1], "content", "").lower()
    has_trigger_word = any(t in user_content for t in triggers)
    
    # If same intent, only allow reset if trigger word exists.
    valid_new_request = result.is_new_request
    if valid_new_request and not is_intent_switch:
         if not has_trigger_word:
             valid_new_request = False

    if valid_new_request or is_intent_switch:
         updates["patient_info"] = None
         updates["auth_info"] = None
         updates["patient_validation_status"] = None
         updates["patient_retry_count"] = 0
         updates["db_matched_patient"] = None
         updates["auth_lookup_result"] = None
         # Set scope to start at the CURRENT user message (which triggered the switch)
         # The current message is the last one in input 'messages'.
         # Index is len(messages) - 1.
         updates["scope_start_index"] = len(messages) - 1
         return updates

    # Sticky Logic (Only if NOT clearing context)
    if current_intent == "check_status" or current_intent == "create_auth":
        if result.intent == "unknown":
            # If user provides data like "1234", "Kevin", "MRI", LLM might say unknown.
            # We want to keep current intent so it routes to collectors.
            print(f"DEBUG: Sticky Intent -> preserving {current_intent}")
            updates["intent"] = current_intent
        elif result.intent == current_intent:
             updates["intent"] = current_intent
             
    # Fail-Safe: Suspicious Continuation Check
    # If state was unknown (current_intent is None/unknown), but LLM jumped to create_auth/check_status
    # WITHOUT is_new_request=True.
    # This often happens when LLM sees history and resumes.
    # CRITICAL FIX: If we ALREADY have patient_info (meaning we are mid-flow but intent was somehow lost/unknown),
    # treat this as valid continuation (Sticky) rather than suspicious.
    has_patient_info = state.get("patient_info") is not None and state.get("patient_info").member_id is not None
    
    if (not current_intent or current_intent == "unknown") and \
       (updates.get("intent") == "create_auth" or updates.get("intent") == "check_status") and \
       not result.is_new_request and \
       not has_patient_info: # Only block if we have NO patient info
           updates["intent"] = "unknown"
           # Also clear context to be safe
           updates["patient_info"] = None
           updates["auth_info"] = None
           return updates
    
    return updates
