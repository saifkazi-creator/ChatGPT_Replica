-- Migration 001: Create conversations and messages tables
-- Run this in the Supabase SQL editor before starting the backend.

CREATE TABLE IF NOT EXISTS public.conversations (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title       text NOT NULL DEFAULT 'New Conversation',
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.messages (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    role             text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content          text NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies: users can only see their own conversations
CREATE POLICY "Users see own conversations"
    ON public.conversations
    FOR ALL
    USING (user_id = auth.uid());

-- RLS Policies: users can only see messages in their own conversations
CREATE POLICY "Users see own messages"
    ON public.messages
    FOR ALL
    USING (
        conversation_id IN (
            SELECT id FROM public.conversations WHERE user_id = auth.uid()
        )
    );
