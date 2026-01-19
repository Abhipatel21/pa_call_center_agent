from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import AgentState
from app.nodes.greeting import greeting_node
from app.nodes.collect_provider import collect_provider_node
from app.nodes.intent_router import intent_router_node
from app.nodes.collect_patient import collect_patient_node
from app.nodes.validate_patient import validate_patient_node
from app.nodes.collect_auth import collect_auth_node
from app.nodes.lookup_auth import lookup_auth_node
from app.nodes.respond_status import respond_status_node
from app.nodes.create_auth_stub import create_auth_stub_node
from app.nodes.collect_info import collect_info_node
from app.nodes.check_create_suggestion import check_create_suggestion_node
from app.nodes.process_confirmation import process_confirmation_node
from app.nodes.offer_assistance import offer_assistance_node
from app.nodes.close_call import close_call_node
from app.nodes.reset_menu import reset_menu_node

def route_after_validation(state: AgentState):
    status = state.get("patient_validation_status")
    intent = state.get("intent")
    print(f"DEBUG: route_after_validation status={status}, intent={intent}")
    
    # CRITICAL: For create_auth, we MUST proceed to collect_auth even if patient validation failed (or was skipped).
    # The user might have provided Auth info but no Patient info yet, or partial patient info.
    # We rely on route_after_auth_collection to check if we have *anything* to proceed.
    if intent == "create_auth":
        return "collect_auth"
        
    if status == "valid":
        return "collect_auth"
    # All other statuses (id_valid, mismatch, etc.) require collecting more info/corrections.
    return "collect_info"

def route_after_suggestion_check(state: AgentState):
    print(f"DEBUG: route_after_suggestion_check intent={state.get('intent')}")
    if state.get("intent") == "create_auth":
        return "create_auth_stub"
    return "offer_assistance"

def route_after_provider(state: AgentState):
    """
    Decide next step after provider collection.
    """
    pi = state.get("provider_info")
    print(f"DEBUG: route_after_provider pi={pi}")
    if not pi or not pi.name or not pi.callback_number:
        return "collect_info"
    return "intent_router"

def route_after_intent(state: AgentState):
    """
    Decide based on intent.
    """
    intent = state.get("intent")
    print(f"DEBUG: route_after_intent intent={intent}")
    
    if intent == "create_auth":
        return "collect_patient" # Start collecting info instead of stub
    elif intent == "check_status":
        return "collect_patient"
    elif intent == "end_conversation":
        # Check if we just asked "anything else?"
        messages = state.get("messages", [])
        last_ai_content = ""
        # Look for the last AI message
        for m in reversed(messages):
            if hasattr(m, "type") and m.type == "ai":
                last_ai_content = getattr(m, "content", str(m)).lower()
                break
        
        if "anything else" in last_ai_content or "assist you" in last_ai_content:
             return "close_call"
        
        # Otherwise, offer assistance before closing
        return "offer_assistance"
    elif intent == "menu_request":
        return "reset_menu"
    else:
        # If unknown, ask for clarification (handled by collect_info which sees "unknown" intent)
        return "collect_info"

def route_after_auth_collection(state: AgentState):
    """
    Decide if we have enough info to lookup or create.
    """
    patient = state.get("patient_info")
    auth = state.get("auth_info")
    intent = state.get("intent")
    
    # Check patient - RELAXED CHECK
    # We rely on validate_patient to set status="valid".
    # But for "create_auth", validate_patient might bypass DB check.
    
    if intent == "create_auth":
        # If User provided ANY info (Patient OR Auth), we assume they answered the question.
        # We assume if they answered, we accept it and move to stub.
        has_patient = patient and (patient.member_id or patient.first_name or patient.last_name or patient.dob)
        has_auth = auth and (auth.auth_id or auth.procedure_description)
        
        if has_patient or has_auth:
             return "create_auth_stub"
        
        # If absolutely nothing, go collect info (Step 1 of flow)
        return "collect_info"

    # Standard Check for check_status
    if not patient or not patient.member_id:
        return "collect_info"
        
    # Check auth
    if not auth or (not auth.auth_id and not auth.procedure_description):
        return "collect_info"
        
    # If all good
    return "lookup_auth"


def build_graph(with_checkpointer: bool = True):
    graph = StateGraph(AgentState)
    
    # Add Nodes
    graph.add_node("greeting", greeting_node)
    graph.add_node("collect_provider", collect_provider_node)
    graph.add_node("intent_router", intent_router_node)
    graph.add_node("collect_patient", collect_patient_node)
    graph.add_node("validate_patient", validate_patient_node)
    graph.add_node("collect_auth", collect_auth_node)
    graph.add_node("collect_info", collect_info_node) # Generates questions
    graph.add_node("check_create_suggestion", check_create_suggestion_node)
    graph.add_node("process_confirmation", process_confirmation_node)
    graph.add_node("create_auth_stub", create_auth_stub_node)
    graph.add_node("offer_assistance", offer_assistance_node)
    graph.add_node("close_call", close_call_node)
    graph.add_node("lookup_auth", lookup_auth_node)
    graph.add_node("respond_status", respond_status_node)
    graph.add_node("reset_menu", reset_menu_node)
    
    # Check if this is the start of the conversation
    # We need a conditional entry or just start at Greeting
    # If messages exist, we skip greeting logic (handled in node) or route differently?
    # Actually, standard flow: Input -> Extraction -> Logic.
    # But for the very first run (no messages), we want greeting.
    # Let's just set "greeting" as entry. The node checks if history is empty.
    
    graph.set_entry_point("greeting")
    
    # Edges
    # Greeting -> if printed greeting -> END (wait for user).
    # If no greeting printed (meaning we have history), we proceed to processing?
    # Wait, greeting node returns "messages" if it generates one.
    
    def greeting_router(state: AgentState):
        # If the greeting node generated a message (i.e., we just started), end and wait for user.
        # Check if the last message was AI? Or just check if we added something?
        # A simpler way: The greeting node checks history.
        # If history was empty, it returns greeting. Then we END.
        # If history was NOT empty (user responded), we go to Collect Provider.
        
        msgs = state.get("messages", [])
        if not msgs:
            return "__end__" # Should not happen if greeting node adds one
            
        # If the last message is AI, we stop.
        # If the last message is Human, we process.
        if hasattr(msgs[-1], "type") and msgs[-1].type == "ai":
             return END

        # Check special context
        # Removed obsolete status checks (suggest_create_auth, data_mismatch)
        # as we now handle everything via linear collection/validation loop.
              
        # If human message, start processing pipeline
        return "collect_provider"

    graph.add_conditional_edges("greeting", greeting_router, {
        END: END, 
        "collect_provider": "collect_provider",
        "check_create_suggestion": "check_create_suggestion",
        "process_confirmation": "process_confirmation"
    })
    
    # Provider Collection -> Conditional
    graph.add_conditional_edges("collect_provider", route_after_provider, {
        "collect_info": "collect_info",
        "intent_router": "intent_router"
    })
    
    # Intent -> Conditional
    graph.add_conditional_edges("intent_router", route_after_intent, {
        "create_auth_stub": "create_auth_stub",
        "collect_patient": "collect_patient",
        "collect_info": "collect_info",
        "close_call": "close_call",
        "offer_assistance": "offer_assistance",
        "reset_menu": "reset_menu"
    })
    
    # Create Auth Stub -> End
    graph.add_edge("create_auth_stub", END)
    graph.add_edge("offer_assistance", END)
    graph.add_edge("close_call", END)
    graph.add_edge("reset_menu", END)
    
    # Collect Patient -> Collect Auth (always extract both if checking status, or logical flow)
    # We can chain them.
    # Collect Patient -> Validate
    graph.add_edge("collect_patient", "validate_patient")

    # Validate -> Conditional
    graph.add_conditional_edges("validate_patient", route_after_validation, {
        "collect_auth": "collect_auth",
        "collect_info": "collect_info"
    })

    # Check Suggestion -> Conditional
    graph.add_conditional_edges("check_create_suggestion", route_after_suggestion_check, {
        "create_auth_stub": "create_auth_stub",
        "offer_assistance": "offer_assistance"
    })
    
    # Collect Auth -> Check if complete
    graph.add_conditional_edges("collect_auth", route_after_auth_collection, {
        "collect_info": "collect_info",
        "lookup_auth": "lookup_auth",
        "create_auth_stub": "create_auth_stub"
    })
    
    
    # Lookup -> Respond Status
    graph.add_edge("lookup_auth", "respond_status")
    
    # Respond Status -> End
    graph.add_edge("respond_status", END)
    
    if with_checkpointer:
        return graph.compile(checkpointer=MemorySaver())
    return graph.compile()

# Expose the graph instance for langgraph dev/cli (No custom checkpointer)
graph = build_graph(with_checkpointer=False)
