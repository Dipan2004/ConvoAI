from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class LeadData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    use_case: Optional[str] = None
    captured_at: Optional[datetime] = None

    def is_complete(self) -> bool:
        return all([self.name, self.email, self.company, self.use_case])

    def missing_fields(self) -> list[str]:
        fields = []
        if not self.name:
            fields.append("name")
        if not self.email:
            fields.append("email")
        if not self.company:
            fields.append("company")
        if not self.use_case:
            fields.append("use_case")
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
