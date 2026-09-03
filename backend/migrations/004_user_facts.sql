-- Migration 004: user_facts table for long-term memory
-- Run this in the Supabase SQL Editor.

CREATE TABLE IF NOT EXISTS public.user_facts (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    fact       text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.user_facts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own facts"
    ON public.user_facts FOR ALL
    USING (user_id = auth.uid());
