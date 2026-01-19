from typing import Optional
from pydantic import BaseModel, Field

class ProviderInfo(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the provider calling")
    callback_number: Optional[str] = Field(default=None, description="Callback phone number of the provider")
