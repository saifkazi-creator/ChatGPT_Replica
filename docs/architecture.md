# Architecture

## System diagram

```
Streamlit UI  --HTTP-->  FastAPI backend  --Supabase client-->  PostgreSQL
                                |                                   |
                                |--> integrations/llm.py            |--> pgvector
                                |--> integrations/web_search.py     |--> auth.users
                                |--> integrations/memory.py (reads/writes Postgres)
```

- Streamlit **never** talks to Supabase or any LLM/search API directly. It
  only calls FastAPI endpoints over HTTP.
- FastAPI is the only thing holding Supabase and LLM API keys.
- All persistence goes through the single Supabase client in
  `backend/app/database/supabase.py`. No ORM, no raw `psycopg2`.

## Folder structure (final)

```
chatgpt-replica/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app, CORS, router registration
│   │   ├── api/                   # one router per resource
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── conversations.py
│   │   │   ├── files.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   └── exceptions.py      # AppException + handler
│   │   ├── database/
│   │   │   └── supabase.py        # single shared Supabase client
│   │   ├── schemas/                # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── conversation.py
│   │   │   ├── file.py
│   │   │   └── user.py
│   │   ├── services/               # all business logic, one file per resource
│   │   │   ├── auth_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── conversation_service.py
│   │   │   └── file_service.py
│   │   ├── rag/
│   │   │   ├── chunking.py         # split text into chunks
│   │   │   ├── embeddings.py       # call embedding API, return vectors
│   │   │   ├── retrieval.py        # pgvector similarity search
│   │   │   └── pipeline.py         # orchestrates chunk -> embed -> store
│   │   └── integrations/
│   │       ├── llm.py              # single function: send messages, get reply
│   │       ├── web_search.py       # single function: query -> results
│   │       └── memory.py           # read/write user_facts table
│   ├── migrations/                 # numbered .sql files, run manually in Supabase
│   ├── requirements.txt
│   └── .env
├── streamlit_app/
│   ├── app.py                      # page config, session state, routing
│   ├── components/
│   │   ├── sidebar.py              # conversation list, new/delete conversation
│   │   ├── chat.py                 # message list + input box
│   │   └── upload.py               # file upload widget
│   ├── services/
│   │   └── api_client.py           # thin wrapper around `requests` for FastAPI calls
│   └── requirements.txt
└── docs/
    ├── goals.md
    ├── architecture.md
    └── tasks.md
```

## Database schema (Supabase / PostgreSQL)

All tables live in the `public` schema. `auth.users` is managed by Supabase
Auth and already exists.

### conversations
| column | type | notes |
|---|---|---|
| id | uuid | primary key, default `gen_random_uuid()` |
| user_id | uuid | references `auth.users(id)` |
| title | text | default `'New Conversation'` |
| created_at | timestamptz | default `now()` |
| updated_at | timestamptz | default `now()` |

### messages
| column | type | notes |
|---|---|---|
| id | uuid | primary key, default `gen_random_uuid()` |
| conversation_id | uuid | references `conversations(id)`, `on delete cascade` |
| role | text | check in `('user','assistant','system')` |
| content | text | |
| created_at | timestamptz | default `now()` |

### documents (Phase 5)
| column | type | notes |
|---|---|---|
| id | uuid | primary key |
| conversation_id | uuid | references `conversations(id)`, cascade delete |
| filename | text | |
| created_at | timestamptz | default `now()` |

### document_chunks (Phase 5)
| column | type | notes |
|---|---|---|
| id | uuid | primary key |
| document_id | uuid | references `documents(id)`, cascade delete |
| content | text | the chunk text |
| embedding | vector(1536) | pgvector column; dimension must match the embedding model used |
| created_at | timestamptz | default `now()` |

Requires `create extension if not exists vector;` and an ivfflat or hnsw
index on `document_chunks.embedding` for similarity search.

### user_facts (Phase 7 — memory)
| column | type | notes |
|---|---|---|
| id | uuid | primary key |
| user_id | uuid | references `auth.users(id)` |
| fact | text | a single short fact, e.g. "prefers concise answers" |
| created_at | timestamptz | default `now()` |

## API contract

All routes are prefixed with `/api`.

- `GET /health`, `GET /health/db`
- `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
- `POST /conversations`, `GET /conversations`, `GET /conversations/{id}`,
  `PATCH /conversations/{id}`, `DELETE /conversations/{id}`
- `POST /chat` — body: `{conversation_id, message}` → saves user message,
  runs RAG retrieval + web search if relevant, calls the LLM, saves and
  returns the assistant reply
- `POST /files` — multipart upload, body includes `conversation_id` →
  triggers `rag/pipeline.py`
- `GET /files`, `DELETE /files/{file_id}`

Every endpoint requires a valid Supabase session token in the
`Authorization: Bearer <token>` header once Phase 3 (auth) is complete.
`user_id` for all queries comes from the verified token, never from the
request body.

## Request flow (final, all phases complete)

```
Streamlit
  -> api_client.py sends HTTP request with Bearer token
    -> FastAPI router (api/*.py)
      -> auth_service verifies the token, extracts user_id
      -> Pydantic schema validates the body
        -> service function (services/*.py)
          -> for /chat: conversation_service saves the user message
          -> rag/retrieval.py fetches relevant chunks from pgvector (if a document exists)
          -> integrations/web_search.py fetches results (if the message needs current info)
          -> integrations/llm.py sends [system + memory facts + retrieved context + history + message]
          -> conversation_service saves the assistant reply
        -> service returns a dict
      -> FastAPI serializes it against response_model
    -> JSON response
  -> Streamlit renders it
```

## Configuration (environment variables)

`backend/.env`:
```
SUPABASE_URL=
SUPABASE_KEY=
LLM_API_KEY=
LLM_MODEL=
WEB_SEARCH_API_KEY=
EMBEDDING_MODEL=
```

`streamlit_app/.env` (or Streamlit secrets):
```
BACKEND_API_URL=http://127.0.0.1:8000/api
```

No Supabase or LLM key is ever read by `streamlit_app/`.
