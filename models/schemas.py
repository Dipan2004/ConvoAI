from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    source: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCallRecord(BaseModel):
    tool_name: str
    inputs: Dict[str, Any]
    output: Optional[Any] = None
    success: bool = False
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    lead_captured: bool = False
    error: Optional[str] = None


class IntentResult(BaseModel):
    intent: str
    confidence: float
    reasoning: str
    confidence_tier: str


class RAGResult(BaseModel):
    chunks: List[RetrievedChunk]
    generated_response: str
    grounded: bool
