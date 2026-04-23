from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from config.settings import settings
from core.agent import Agent
from core.graph_builder import GraphBuilder
from core.state_manager import StateManager
from modules.conversation.clarification_node import ClarificationNode
from modules.conversation.fallback_node import FallbackNode
from modules.conversation.smalltalk_node import SmallTalkNode
from modules.intent.intent_classifier import IntentClassifier
from modules.intent.intent_node import IntentNode
from modules.lead.lead_manager import LeadManager
from modules.lead.lead_node import LeadNode
from modules.lead.validator import LeadValidator
from modules.rag.generator import Generator
from modules.rag.rag_node import RAGNode
from modules.rag.reranker import Reranker
from modules.rag.retriever import Retriever
from services.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.redis_service import RedisService
from services.vector_db_service import VectorDBService
from utils.logger import AppLogger
from utils.prompt_loader import PromptLoader

logger = AppLogger(__name__)

_agent: Optional[Agent] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str

    @field_validator("session_id")
    @classmethod
    def session_id_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("session_id cannot be empty")
        return v

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > settings.max_message_length:
            raise ValueError(f"message exceeds {settings.max_message_length} characters")
        return v


class MetaResponse(BaseModel):
    intent: Optional[str] = None
    confidence: Optional[float] = None
    tokens: Optional[Dict[str, int]] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[float] = None
    lead_captured: bool = False
    error: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    meta: MetaResponse


def _build_agent() -> Agent:
    redis_service = RedisService()
    llm_service = LLMService()
    embedding_service = EmbeddingService()
    vector_db_service = VectorDBService(embedding_service=embedding_service)
    prompt_loader = PromptLoader()
    prompt_loader.preload_all()

    intent_classifier = IntentClassifier(llm_service=llm_service, prompt_loader=prompt_loader)
    intent_node = IntentNode(classifier=intent_classifier)

    retriever = Retriever(vector_db_service=vector_db_service, top_k=5)
    reranker = Reranker(embedding_service=embedding_service, top_k=3)
    generator = Generator(llm_service=llm_service, prompt_loader=prompt_loader)
    rag_node = RAGNode(retriever=retriever, reranker=reranker, generator=generator)

    lead_validator = LeadValidator()
    lead_manager = LeadManager(validator=lead_validator)
    lead_node = LeadNode(lead_manager=lead_manager, rag_node=rag_node)

    smalltalk_node = SmallTalkNode(llm_service=llm_service)
    fallback_node = FallbackNode()
    clarification_node = ClarificationNode()

    graph = GraphBuilder(
        intent_node=intent_node,
        rag_node=rag_node,
        lead_node=lead_node,
        clarification_node=clarification_node,
        fallback_node=fallback_node,
        smalltalk_node=smalltalk_node,
    ).build()

    state_manager = StateManager(redis_service=redis_service)
    return Agent(
        state_manager=state_manager,
        graph=graph,
        rate_limit=settings.rate_limit_per_minute,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    _agent = _build_agent()
    logger.info({"event": "app_startup", "version": settings.app_version})
    yield
    logger.info({"event": "app_shutdown"})


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = _agent.handle_request(
        session_id=request.session_id,
        user_input=request.message,
    )
    meta = result.get("meta", {})
    return ChatResponse(
        session_id=result["session_id"],
        response=result["response"],
        meta=MetaResponse(
            intent=meta.get("intent"),
            confidence=meta.get("confidence"),
            tokens=meta.get("tokens"),
            cost_usd=meta.get("cost_usd"),
            latency_ms=meta.get("latency_ms"),
            lead_captured=meta.get("lead_captured", False),
            error=meta.get("error"),
        ),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error({
        "event": "unhandled_exception",
        "error": str(exc),
        "path": str(request.url),
    })
    return JSONResponse(
        status_code=500,
        content={
            "response": "Something went wrong. Please try again.",
            "meta": {"error": "internal_error"},
        },
    )
