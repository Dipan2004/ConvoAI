from enum import Enum


class Intent(str, Enum):
    PRODUCT_INQUIRY = "product_inquiry"
    SUPPORT_REQUEST = "support_request"
    LEAD_CAPTURE = "lead_capture"
    SMALL_TALK = "small_talk"
    OUT_OF_SCOPE = "out_of_scope"
    CLARIFICATION = "clarification"


class ConfidenceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NodeName(str, Enum):
    INTENT = "intent"
    RAG = "rag"
    LEAD = "lead"
    SMALL_TALK = "small_talk"
    FALLBACK = "fallback"
    CLARIFICATION = "clarification"


class ToolName(str, Enum):
    SEARCH_KNOWLEDGE_BASE = "search_knowledge_base"
    CREATE_LEAD = "create_lead"
    SEND_NOTIFICATION = "send_notification"


class ErrorCode(str, Enum):
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_PARSE_FAILURE = "LLM_PARSE_FAILURE"
    RAG_LOW_SCORE = "RAG_LOW_SCORE"
    LEAD_VALIDATION_FAILED = "LEAD_VALIDATION_FAILED"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
