# Goals

## What we are building

A minimal, working ChatGPT-style web app called **chatgpt-replica**, built as a
one-day learning project. A user can sign up, log in, start conversations,
send chat messages, see AI-generated replies, and have their conversation
history persisted.

## Tech stack (fixed — do not substitute)

- **UI:** Streamlit
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL + Supabase Auth)
- **Vector store:** pgvector (Postgres extension, via Supabase) — no separate
  vector database
- **LLM:** one hosted LLM API (Anthropic or OpenAI — pick one and use it
  consistently everywhere `integrations/llm.py` is called)
- **Web search:** one hosted search API (e.g. Tavily, Serper, or Bing) used
  only inside `integrations/web_search.py`

## Explicitly out of scope (do not add)

- LangChain, LangGraph, LlamaIndex
- FAISS, ChromaDB, Pinecone, Weaviate, or any vector DB other than pgvector
- Mem0 or any third-party memory framework
- SQLAlchemy or any ORM (use the Supabase Python client directly)
- Repository pattern, DAO pattern, abstract base classes, factories,
  generic CRUD frameworks
- Celery, background task queues, message brokers
- Docker/Kubernetes deployment tooling
- Multi-tenant org/team features, billing, admin dashboards
- Native mobile apps

## Core features (final product)

1. **Auth** — sign up, log in, log out, get current user, via Supabase Auth.
2. **Conversations** — create, list, rename, delete conversations. Each
   belongs to exactly one user.
3. **Chat** — send a message in a conversation, get an LLM-generated reply,
   both saved to Postgres.
4. **File upload + RAG** — upload a text/PDF file, chunk and embed it,
   store chunks + embeddings in pgvector, and retrieve relevant chunks to
   augment chat answers when relevant.
5. **Web search** — optionally augment chat answers with live web search
   results when the user's message needs current information.
6. **Memory** — persist simple long-term facts about the user across
   conversations (stored in Postgres, not a separate memory service).

## Success criteria

- A user can complete this flow end-to-end with no crashes:
  sign up → log in → create a conversation → send a message → receive an
  LLM reply → close and reopen the app → see the same conversation history.
- Uploading a file makes the LLM able to answer questions about that file's
  content in the same conversation.
- All FastAPI endpoints listed in `architecture.md` exist and return the
  documented response shapes.
- The app runs locally with: one `uvicorn` process (backend) and one
  `streamlit run` process (frontend), each using only its own
  `requirements.txt`.
- No secrets (Supabase keys, LLM API keys) are hardcoded anywhere; all come
  from `.env` files.

## Build order (see tasks.md for detail)

Phase 1: FastAPI skeleton, placeholder endpoints → **done**
Phase 2: Real Supabase/Postgres persistence for conversations + messages → **done**
Phase 3: Real authentication (Supabase Auth), wired into all endpoints
Phase 4: Real LLM integration in chat
Phase 5: File upload + RAG (chunking, embeddings, pgvector retrieval)
Phase 6: Web search integration
Phase 7: Long-term memory
Phase 8: Streamlit UI wired to the finished backend

The agent should complete phases in order and must not skip ahead — later
phases assume earlier phases are fully working and tested.
