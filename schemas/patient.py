from pydantic import BaseModel, Field
from typing import Optional

class PatientInfo(BaseModel):
    first_name: Optional[str] = Field(default=None, description="Patient's first name")
    last_name: Optional[str] = Field(default=None, description="Patient's last name")
    dob: Optional[str] = Field(default=None, description="Date of birth in YYYY-MM-DD format. Example: '1990-01-01'. Convert verbal dates like '1st Jan 1990' to this format.")
    member_id: Optional[str] = Field(default=None, description="Member ID of the patient")
