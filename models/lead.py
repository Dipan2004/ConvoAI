from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class LeadData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    platform: Optional[str] = None
    captured_at: Optional[datetime] = None

    def is_complete(self) -> bool:
        return all([self.name, self.email, self.platform])

    def missing_fields(self) -> list[str]:
        fields = []
        if not self.name:
            fields.append("name")
        if not self.email:
            fields.append("email")
        if not self.platform:
            fields.append("platform")
        return fields

    def next_missing_field(self) -> Optional[str]:
        missing = self.missing_fields()
        return missing[0] if missing else None


class LeadRecord(BaseModel):
    id: Optional[str] = None
    session_id: str
    lead_data: LeadData
    created_at: datetime = datetime.utcnow()
    notified: bool = False
