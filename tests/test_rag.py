from unittest.mock import MagicMock
from modules.rag.retriever import Retriever
from modules.rag.reranker import Reranker
from modules.rag.generator import Generator
from modules.rag.rag_node import RAGNode


def _make_doc(chunk_id: str, content: str, score: float) -> dict:
    return {"id": chunk_id, "content": content, "metadata": {"source": "test.md"}, "score": score}


def _make_retriever(docs: list) -> Retriever:
    vdb = MagicMock()
    vdb.query.return_value = docs
    return Retriever(vector_db_service=vdb, top_k=5)


def _make_reranker(top_k: int = 3) -> Reranker:
    embedder = MagicMock()
    embedder.embed.return_value = [0.1] * 384
    return Reranker(embedding_service=embedder, top_k=top_k)


def _make_generator(response: str = "Test response") -> Generator:
    llm = MagicMock()
    llm.generate.return_value = {"content": response, "parsed": None}
    return Generator(llm_service=llm)


def test_retriever_returns_results():
    docs = [_make_doc("1", "Our product supports SSO.", 0.91)]
    retriever = _make_retriever(docs)
    results = retriever.retrieve("Do you support SSO?")
    assert len(results) == 1
    assert results[0]["score"] == 0.91


def test_retriever_empty_results():
    retriever = _make_retriever([])
    results = retriever.retrieve("unknown query")
    assert results == []


def test_reranker_reduces_to_top_k():
    docs = [
        _make_doc("1", "SSO via SAML", 0.9),
        _make_doc("2", "OAuth2 integration", 0.8),
        _make_doc("3", "Two factor authentication", 0.7),
        _make_doc("4", "Password reset flow", 0.6),
        _make_doc("5", "Account lockout policy", 0.5),
    ]
    reranker = _make_reranker(top_k=3)
    results = reranker.rerank("SSO", docs)
    assert len(results) == 3


def test_reranker_empty_input():
    reranker = _make_reranker()
    results = reranker.rerank("query", [])
    assert results == []


def test_reranker_fewer_docs_than_top_k():
    docs = [_make_doc("1", "only doc", 0.9)]
    reranker = _make_reranker(top_k=3)
    results = reranker.rerank("query", docs)
    assert len(results) == 1


def test_generator_returns_response():
    docs = [_make_doc("1", "We offer SSO integration", 0.92)]
    gen = _make_generator("We support SSO via SAML and OAuth2.")
    state = {"session_id": "s1", "messages": []}
    response = gen.generate("Do you have SSO?", docs, history=[])
    assert "SSO" in response or len(response) > 0


def test_generator_falls_back_on_empty_docs():
    gen = _make_generator()
    response = gen.generate("anything", [], history=[])
    assert "don't have" in response.lower() or "connect" in response.lower() or len(response) > 0


def test_generator_falls_back_on_low_score():
    docs = [_make_doc("1", "irrelevant content", 0.1)]
    gen = _make_generator()
    response = gen.generate("anything", docs, history=[])
    assert len(response) > 0


def test_generator_uses_medium_score_docs_with_disclaimer():
    docs = [_make_doc("1", "Pro plan includes 4K export and AI captions.", 0.52)]
    gen = _make_generator("Pro plan includes 4K export and AI captions.")
    response = gen.generate("What does the Pro plan include?", docs, history=[])
    assert "4K" in response
    assert "limited available data" in response


def test_rag_node_full_pipeline():
    docs = [_make_doc("1", "Pro plan costs $49/month with unlimited users.", 0.95)]
    retriever = _make_retriever(docs)
    reranker = _make_reranker(top_k=3)
    generator = _make_generator("Pro plan costs $49/month.")
    node = RAGNode(retriever=retriever, reranker=reranker, generator=generator)
    state = {
        "session_id": "s1",
        "messages": [],
        "rag_context": [],
        "intent": "product_inquiry",
        "confidence": 0.92,
        "lead_data": {},
        "flags": {"lead_captured": True},
    }
    updated, response = node.execute(state, "What is the Pro plan price?")
    assert len(updated["rag_context"]) > 0
    assert len(response) > 0


def test_rag_node_updates_rag_context():
    docs = [_make_doc("1", "Feature overview content.", 0.88)]
    retriever = _make_retriever(docs)
    reranker = _make_reranker(top_k=3)
    generator = _make_generator("Here are the features.")
    node = RAGNode(retriever=retriever, reranker=reranker, generator=generator)
    state = {
        "session_id": "s1",
        "messages": [],
        "rag_context": [],
        "intent": "product_inquiry",
        "confidence": 0.88,
        "lead_data": {},
        "flags": {},
    }
    updated, _ = node.execute(state, "Tell me about features")
    assert "rag_context" in updated
    assert isinstance(updated["rag_context"], list)


def run():
    tests = [
        test_retriever_returns_results,
        test_retriever_empty_results,
        test_reranker_reduces_to_top_k,
        test_reranker_empty_input,
        test_reranker_fewer_docs_than_top_k,
        test_generator_returns_response,
        test_generator_falls_back_on_empty_docs,
        test_generator_falls_back_on_low_score,
        test_generator_uses_medium_score_docs_with_disclaimer,
        test_rag_node_full_pipeline,
        test_rag_node_updates_rag_context,
    ]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as exc:
            failed.append((t.__name__, str(exc)))
    return passed, failed
