from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    content: str = Field(description="The response message to be shown to the user.")
