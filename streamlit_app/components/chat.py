import streamlit as st
from services import api_client as api


def _ensure_messages_loaded(conv_id: str):
    """Load messages from backend on first visit to this conversation."""
    key = f"messages_{conv_id}"
    if key not in st.session_state:
        try:
            raw = api.get_messages(conv_id)
            # Only keep user / assistant roles for display
            st.session_state[key] = [
                {"role": m["role"], "content": m["content"]}
                for m in raw
                if m["role"] in ("user", "assistant")
            ]
        except RuntimeError:
            st.session_state[key] = []


def render(conv_id: str):
    """
    Render the chat panel for the selected conversation.
    Loads history from the backend on first visit, then tracks locally.
    """
    if not conv_id:
        st.info("👈 Select or create a conversation to get started.")
        return

    _ensure_messages_loaded(conv_id)
    msg_key = f"messages_{conv_id}"
    messages: list = st.session_state[msg_key]

    # Render existing history
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # New message input
    user_input = st.chat_input("Send a message…", key=f"chat_input_{conv_id}")
    if user_input:
        # Immediately show user bubble
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call backend and show assistant reply via stream
        with st.chat_message("assistant"):
            try:
                http_resp = api.send_chat_message_stream(conv_id, user_input)

                def _text_chunks():
                    for raw in http_resp.iter_content(chunk_size=None):
                        if raw:
                            yield raw.decode("utf-8", errors="replace")

                reply = st.write_stream(_text_chunks())

                # Persist to session state
                st.session_state[msg_key].append({"role": "user", "content": user_input})
                st.session_state[msg_key].append({"role": "assistant", "content": reply})

                # Auto-generate title after the first exchange
                active_convs = st.session_state.get("conversations", [])
                active_conv = next((c for c in active_convs if c["id"] == conv_id), None)
                if active_conv and active_conv.get("title") == "New Conversation":
                    try:
                        api.auto_title_conversation(conv_id)
                    except RuntimeError:
                        pass  # title generation failure is non-fatal

                # Refresh conversation list (updates title + updated_at order)
                st.session_state.conversations = api.list_conversations()
                st.rerun()
            except RuntimeError as e:
                st.error(f"❌ {e}")
