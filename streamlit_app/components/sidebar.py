import streamlit as st
from services import api_client as api


def render(conversations: list):
    """
    Render the left sidebar:
    - App branding
    - 'New Conversation' button
    - Scrollable conversation list (click to switch, rename ✏️, delete 🗑)
    - Logout button
    """
    st.markdown("""
    <div style="text-align:center; padding: 8px 0 16px 0;">
        <span style="font-size:28px;">🤖</span>
        <span style="font-size:20px; font-weight:700; color:#e2e8f0; margin-left:6px;">ChatGPT Replica</span>
    </div>
    """, unsafe_allow_html=True)

    # New conversation
    if st.button("➕  New Conversation", use_container_width=True, key="new_conv_btn"):
        try:
            conv = api.create_conversation("New Conversation")
            st.session_state.active_conv_id = conv["id"]
            st.session_state.conversations = api.list_conversations()
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))

    st.divider()

    # Conversation list
    if not conversations:
        st.caption("No conversations yet. Start one above!")
    else:
        for conv in conversations:
            cid = conv["id"]
            title = conv["title"] or "Untitled"
            is_active = (cid == st.session_state.get("active_conv_id"))
            rename_key = f"renaming_{cid}"

            # ── Inline rename mode ──────────────────────────────────────────
            if st.session_state.get(rename_key, False):
                new_title = st.text_input(
                    "Rename",
                    value=title,
                    key=f"rename_input_{cid}",
                    label_visibility="collapsed",
                )
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("✅ Save", key=f"save_{cid}", use_container_width=True):
                        if new_title.strip():
                            try:
                                api.rename_conversation(cid, new_title.strip())
                                st.session_state.conversations = api.list_conversations()
                            except RuntimeError as e:
                                st.error(str(e))
                        st.session_state[rename_key] = False
                        st.rerun()
                with col_cancel:
                    if st.button("✖ Cancel", key=f"cancel_{cid}", use_container_width=True):
                        st.session_state[rename_key] = False
                        st.rerun()

            # ── Normal display mode ─────────────────────────────────────────
            else:
                col1, col2, col3 = st.columns([5, 1, 1])
                with col1:
                    btn_style = "primary" if is_active else "secondary"
                    label = f"{'▶ ' if is_active else ''}{title[:28]}"
                    if st.button(label, key=f"conv_{cid}", use_container_width=True,
                                 type=btn_style):
                        st.session_state.active_conv_id = cid
                        st.rerun()
                with col2:
                    if st.button("✏️", key=f"ren_{cid}", help="Rename conversation"):
                        st.session_state[rename_key] = True
                        st.rerun()
                with col3:
                    if st.button("🗑", key=f"del_{cid}", help="Delete conversation"):
                        try:
                            api.delete_conversation(cid)
                            st.session_state.conversations = api.list_conversations()
                            if st.session_state.get("active_conv_id") == cid:
                                convs = st.session_state.conversations
                                st.session_state.active_conv_id = convs[0]["id"] if convs else None
                            st.rerun()
                        except RuntimeError as e:
                            st.error(str(e))

    st.divider()

    # User info + logout
    email = st.session_state.get("user_email", "")
    if email:
        st.caption(f"👤 {email}")

    if st.button("🚪 Log out", use_container_width=True, key="logout_btn"):
        api.logout()
        for key in ["access_token", "user_email", "active_conv_id", "conversations"]:
            st.session_state.pop(key, None)
        st.rerun()
