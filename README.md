# ConvoAI

A production-style conversational AI backend that converts user messages into structured business workflows using intent detection, agent orchestration, lead capture, and retrieval-augmented responses.

---

## Overview

ConvoAI is designed to simulate how modern SaaS platforms handle intelligent conversations.

It processes user input, identifies intent, routes requests through a graph-based agent system, captures leads when required, and generates grounded responses using a Retrieval-Augmented Generation (RAG) pipeline.

---

## Key Features

* Intent classification with confidence scoring
* Agent-based orchestration using LangGraph
* Lead capture and validation workflow
* Retrieval-Augmented Generation (RAG) pipeline
* Stateful conversations with Redis
* Modular architecture (production-style monolith)
* Structured logging and observability
* Rate limiting and input validation

---

## System Architecture

```
User → FastAPI API
     → Agent (LangGraph)
     → Intent Detection
     → Router
        → Small Talk
        → Lead Capture
        → RAG
        → Fallback
     → Response
     → State Persistence (Redis)
```

---

## Tech Stack

### Backend

* FastAPI
* Python 3.10+

### AI / Orchestration

* OpenRouter (LLM layer)
* LangGraph (agent workflow engine)

### Data Layer

* Redis (session state)
* ChromaDB (vector database)
* Sentence Transformers (embeddings)

### Frontend

* React + TailwindCSS (minimal product UI)

### Utilities

* Pydantic (config & validation)
* Custom logger (structured logging)

---

## Project Structure

```
app/
core/
modules/
services/
utils/
models/
tests/
```

* `core/` → agent, graph builder, state manager
* `modules/` → intent, RAG, lead, conversation nodes
* `services/` → LLM, Redis, vector DB
* `utils/` → logger, parser, validators
* `tests/` → unit and integration tests

---

## API

### POST /chat

**Request**

```json
{
  "session_id": "string",
  "message": "string"
}
```

**Response**

```json
{
  "response": "string",
  "meta": {
    "intent": "string",
    "confidence": 0.0
  }
}
```

---

## Core Flow

1. User sends a message
2. Session state is loaded from Redis
3. Intent is classified (rule-based + LLM)
4. LangGraph routes to the correct node
5. Node executes:

   * Small Talk
   * Lead Capture
   * RAG
   * Fallback
6. Response is generated
7. State is persisted

---
## WhatsApp Integration

The system can be integrated with WhatsApp using Meta’s WhatsApp Business API.

A webhook endpoint receives incoming messages, extracts the user's phone number as session_id and message text, then forwards it to the /chat endpoint.

Responses are sent back using the WhatsApp API, maintaining stateful conversations through Redis using the phone number as session identifier.

## Running the Project

### 1. Setup Environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### 2. Configure

```bash
copy .env.example .env
```

Add your API key:

```
OPENROUTER_API_KEY=your_key
```

---

### 3. Start Redis

```bash
docker run -d -p 6379:6379 redis:alpine
```

---

### 4. Run Backend

```bash
uvicorn app.main:app --reload
```

---

### 5. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```
http://localhost:5173
```

---

### 6. Test API

```bash
curl -Method POST http://localhost:8000/chat `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"session_id": "test-1", "message": "Hello"}'
```

---

## Testing

Run all tests:

```bash
python app/test_runner.py
```

---

## Design Decisions

* **Modular Monolith**
  Combines simplicity of deployment with clean separation of concerns

* **Hybrid Intent System (Rules + LLM)**
  Ensures reliability while leveraging AI flexibility

* **Agent-Based Routing (LangGraph)**
  Enables scalable and extensible workflows

* **Lead Gating Before RAG**
  Simulates real-world SaaS conversion flows

* **Fail-Safe Architecture**
  Handles LLM failures, empty RAG context, and invalid inputs gracefully

---

## Limitations

* RAG performance depends on available knowledge base
* Free-tier LLMs may introduce latency or rate limits
* Minimal frontend (focused on backend evaluation)

---

## Future Improvements

* Add real knowledge base ingestion pipeline
* Multi-LLM routing for cost optimization
* Streaming responses
* Advanced analytics and monitoring
* Authentication and multi-user support

---

## Author

Dipan
Computer Science Engineering Student

---

## License

This project is for educational and evaluation purposes.
