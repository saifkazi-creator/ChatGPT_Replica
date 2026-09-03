-- Migration 003 (corrected): Drop old tables if they exist, then recreate cleanly
-- Run this in the Supabase SQL Editor.

-- Drop old objects if they exist (from previous sessions)
DROP TABLE IF EXISTS public.document_chunks CASCADE;
DROP TABLE IF EXISTS public.documents CASCADE;
DROP FUNCTION IF EXISTS match_document_chunks CASCADE;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- documents table
CREATE TABLE public.documents (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    filename        text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- document_chunks table — 768 dims to match gemini-embedding-001
CREATE TABLE public.document_chunks (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    content     text NOT NULL,
    embedding   vector(768),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- HNSW index for fast cosine similarity search
CREATE INDEX document_chunks_embedding_idx
    ON public.document_chunks
    USING hnsw (embedding vector_cosine_ops);

-- RLS
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own documents"
    ON public.documents FOR ALL
    USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users see own document chunks"
    ON public.document_chunks FOR ALL
    USING (
        document_id IN (
            SELECT d.id FROM public.documents d
            JOIN public.conversations c ON c.id = d.conversation_id
            WHERE c.user_id = auth.uid()
        )
    );

-- Similarity search function (called via supabase.rpc)
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding        vector(768),
    conversation_id_filter uuid,
    match_count            int DEFAULT 5
)
RETURNS TABLE (
    id         uuid,
    content    text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.content,
        (1 - (dc.embedding <=> query_embedding))::float AS similarity
    FROM public.document_chunks dc
    JOIN public.documents d ON d.id = dc.document_id
    WHERE d.conversation_id = conversation_id_filter
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
