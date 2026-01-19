from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from schemas.provider import ProviderInfo
from schemas.patient import PatientInfo
from schemas.auth import AuthInfo

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    provider_info: Optional[ProviderInfo]
    patient_info: Optional[PatientInfo]
    auth_info: Optional[AuthInfo]
    intent: Optional[str]  # "check_status" or "create_auth"
    auth_lookup_result: Optional[dict] # Result from JSON lookup
    patient_validation_status: Optional[str] 
    patient_retry_count: Optional[int]
    db_matched_patient: Optional[dict] # For storing the DB record when ID matches but details don't
    scope_start_index: Optional[int] # Index in messages list where current scope starts (for extraction)
