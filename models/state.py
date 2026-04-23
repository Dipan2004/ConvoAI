from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from models.lead import LeadData
from models.schemas import Message, RetrievedChunk, ToolCallRecord


class ConversationState(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    summary: Optional[str] = None
    intent: Optional[str] = None
    intent_confidence: float = 0.0
    intent_reasoning: Optional[str] = None
    lead_data: LeadData = Field(default_factory=LeadData)
    rag_context: List[RetrievedChunk] = Field(default_factory=list)
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    turn_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    flags: Dict[str, bool] = Field(default_factory=dict)
    interrupted_flow: Optional[str] = None
    pending_clarification: Optional[str] = None
    error: Optional[str] = None

    def is_lead_captured(self) -> bool:
        return self.flags.get("lead_captured", False)

    def mark_lead_captured(self) -> None:
        self.flags["lead_captured"] = True

    def get_recent_messages(self, n: int = 6) -> List[Message]:
        return self.messages[-n:]
