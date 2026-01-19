from app.state import AgentState
from utils.llm import get_llm
from utils.prompt_loader import load_prompt
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

class CreateAuthDecision(BaseModel):
    decision: str = Field(description="'yes' or 'no' based on user response to creating a new authorization")

def check_create_suggestion_node(state: AgentState):
    """
    Checks if user wants to create a new auth after validation failure.
    """
    messages = state["messages"]
    
    llm = get_llm()
    structured_llm = llm.with_structured_output(CreateAuthDecision)
    
    system_prompt = load_prompt("system")
    decision_prompt = load_prompt("check_create_decision")
    
    prompt = [
        SystemMessage(content=system_prompt),
        SystemMessage(content=decision_prompt)
    ] + messages[-1:] 
    # Or check recent history.
    
    # Ideally, we should parse based on context, but let's trust the last user message
    
    result = structured_llm.invoke(prompt)
    
    return {"intent": "create_auth" if result.decision == "yes" else "end_conversation"}
