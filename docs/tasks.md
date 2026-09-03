# Tasks

Work through phases in order. Do not start a phase until the previous one's
tasks are all checked off and the app still runs. Do not implement anything
from a later phase while working on an earlier one.

## Phase 1 — FastAPI skeleton ✅
- [x] `main.py` with CORS + router registration under `/api`
- [x] `core/config.py`, `core/exceptions.py`
- [x] Placeholder `api/`, `services/`, `schemas/` for auth, chat,
      conversations, files, health
- [x] `requirements.txt`: fastapi[standard], pydantic-settings,
      python-dotenv, python-multipart

## Phase 2 — Real persistence ✅
- [x] SQL migration for `conversations`, `messages` tables
- [x] `database/supabase.py` with a real Supabase client
- [x] `conversation_service.py`: create/list/get/update/delete conversation,
      create/list message, all via Supabase
- [x] `chat_service.py`: save user message, placeholder reply, save
      assistant message
- [x] `GET /api/health/db`
- [x] `requirements.txt` += supabase

## Phase 3 — Authentication ✅
- [x] SQL: confirm `auth.users` exists (Supabase-managed, no migration needed)
- [x] `auth_service.py`:
  - `signup(email, password)` → `supabase.auth.sign_up(...)`
  - `login(email, password)` → `supabase.auth.sign_in_with_password(...)`,
    return access token
  - `logout(access_token)` → `supabase.auth.sign_out()`
  - `get_current_user(access_token)` → `supabase.auth.get_user(access_token)`
- [x] `core/security.py` (new file): FastAPI dependency `get_current_user_id`
      that reads `Authorization: Bearer <token>`, calls
      `supabase.auth.get_user(token)`, returns `user_id` or raises 401
- [x] Add `Depends(get_current_user_id)` to every endpoint in
      `conversations.py`, `chat.py`, `files.py`
- [x] Replace every `user_id or settings.DEV_USER_ID` default in
      `conversation_service.py` with the required `user_id` parameter
      (no more default) — remove `DEV_USER_ID` from `config.py`
- [x] Update `schemas/auth.py` response to include the access token
- [x] Test: signup → login → use returned token to create a conversation →
      confirm a different user's token cannot see it (RLS or explicit
      `user_id` filter in queries, whichever is already used)


## Phase 4 — Real LLM integration ✅
- [x] Add `LLM_API_KEY`, `LLM_MODEL` to `config.py` and `.env.example`
- [x] `integrations/llm.py`: one function
      `generate_reply(messages: list[dict]) -> str` that calls the chosen
      LLM API's chat/completions endpoint and returns the text reply
- [x] Update `chat_service.py`:
  - `list_messages(conversation_id)` to build the conversation history
  - pass `[{"role": ..., "content": ...}, ...]` to `llm.generate_reply`
  - replace `_generate_placeholder_response` with the real call
  - keep the save-user-message / save-assistant-message steps unchanged
- [x] Handle LLM API errors: catch exceptions, raise `AppException` with
      status 502 and a clear message — do not let the raw exception leak
- [x] Test: `POST /api/chat` returns a real, coherent model reply and both
      messages are visible in Postgres afterward

## Phase 5 — File upload + RAG ✅
- [x] SQL migration: `documents`, `document_chunks` tables (see
      `architecture.md` for exact columns), `create extension if not
      exists vector;`, and an index on `document_chunks.embedding`
- [x] `rag/chunking.py`: `chunk_text(text: str, chunk_size=800,
      overlap=100) -> list[str]` — simple character or word-based
      splitting, no external chunking library
- [x] `rag/embeddings.py`: `embed_text(text: str) -> list[float]` calling
      one embedding API (same provider as the LLM, if it offers one)
- [x] `rag/pipeline.py`: `process_document(file, conversation_id)` —
      extract text (plain text and PDF only), chunk it, embed each chunk,
      insert rows into `documents` and `document_chunks`
- [x] `rag/retrieval.py`: `retrieve_relevant_chunks(conversation_id,
      query, top_k=5)` — embed the query, run a pgvector `<->` similarity
      query scoped to that conversation's documents, return chunk texts
- [x] `file_service.py`: replace the 501 placeholders — `upload_file`
      calls `rag/pipeline.process_document`; `list_files`/`delete_file`
      query/delete from `documents`
- [x] `api/files.py`: require `conversation_id` as a form field alongside
      the uploaded file
- [x] Update `chat_service.py`: before calling the LLM, call
      `retrieve_relevant_chunks` for the current conversation; if any
      chunks come back, prepend them to the LLM messages as a system/context
      message
- [x] Test: upload a small .txt file, ask a question only answerable from
      that file's content, confirm the reply reflects it

## Phase 6 — Web search ✅
- [x] Add `WEB_SEARCH_API_KEY` to `config.py` and `.env.example`
- [x] `integrations/web_search.py`: one function
      `search_web(query: str, max_results=5) -> list[dict]` (title, url,
      snippet) calling one search API
- [x] `chat_service.py`: add a simple heuristic to decide when to search
      (e.g. message contains words like "latest", "current", "today", "who
      is", "recent") — do not build a classifier, keep the rule simple and
      explicit
- [x] When triggered, call `search_web`, format results as a short context
      block, prepend to LLM messages same as RAG context
- [x] Test: ask a question that triggers the heuristic, confirm search
      results are fetched and referenced in the reply

## Phase 7 — Memory ✅
- [x] SQL migration: `user_facts` table (see `architecture.md`)
- [x] `integrations/memory.py`:
  - `get_user_facts(user_id) -> list[str]`
  - `add_user_fact(user_id, fact: str)`
- [x] `chat_service.py`: fetch `get_user_facts(user_id)` and prepend as a
      short system message before every LLM call
- [x] Add a simple explicit trigger for saving facts: if the user's message
      starts with "remember that " or "remember:", extract the rest and
      call `add_user_fact` — do not attempt automatic fact extraction from
      every message
- [x] Test: send "remember that I prefer short answers", start a new
      conversation, confirm later replies are shorter

## Phase 8 — Streamlit UI ✅
- [x] `streamlit_app/services/api_client.py`: functions for every backend
      endpoint (`signup`, `login`, `list_conversations`,
      `create_conversation`, `send_chat_message`, `upload_file`, etc.),
      using `requests`, reading `BACKEND_API_URL` from env, storing the
      access token in `st.session_state`
- [x] `streamlit_app/app.py`: page config; if no token in session state,
      show login/signup form; else show the main chat layout
- [x] `components/sidebar.py`: list conversations (button per conversation
      to switch), "New conversation" button, delete button per conversation
- [x] `components/chat.py`: render message history for the selected
      conversation, `st.chat_input` for new messages, call
      `send_chat_message`, append reply to displayed history
- [x] `components/upload.py`: `st.file_uploader`, call `upload_file` for
      the currently selected conversation
- [x] `streamlit_app/requirements.txt`: `streamlit`, `requests`,
      `python-dotenv`
- [x] Test full flow manually: signup, login, new conversation, send
      message, see reply, upload a file, ask about it, log out, log back
      in, confirm history persisted

## Definition of done (whole project)
- [x] Every checkbox above is checked
- [x] `uvicorn app.main:app --reload` and `streamlit run app.py` both start
      without errors using only their respective `requirements.txt`
- [x] No hardcoded secrets anywhere in the codebase
- [x] `docs/goals.md` success criteria all pass manually
