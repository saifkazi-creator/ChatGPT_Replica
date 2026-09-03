-- Migration 002: Remove user_id from messages (not in architecture.md spec)
-- Messages are already scoped to a user via conversation_id -> conversations.user_id
-- Run this in the Supabase SQL Editor.

-- Drop the RLS policy that depends on user_id first
DROP POLICY IF EXISTS "Users can manage own messages" ON public.messages;

-- Now drop the column
ALTER TABLE public.messages DROP COLUMN IF EXISTS user_id CASCADE;
