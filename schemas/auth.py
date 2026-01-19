from pydantic import BaseModel, Field
from typing import Optional

class AuthInfo(BaseModel):
    auth_id: Optional[str] = Field(None, description="Prior Authorization ID if available")
    procedure_description: Optional[str] = Field(None, description="Description of the procedure if Auth ID is not available")
