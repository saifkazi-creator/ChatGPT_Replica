import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="ChatGPT Replica",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Dark theme refinements */
[data-testid="stSidebar"] {
    background-color: #0f172a;
}
[data-testid="stSidebar"] .stButton button {
    border-radius: 8px;
    text-align: left;
}
.stChatMessage {
    border-radius: 12px;
}
/* Auth form centering */
.auth-container {
    max-width: 420px;
    margin: 60px auto 0 auto;
}
h1 {
    font-size: 2rem;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

from services import api_client as api
from components import sidebar, chat, upload


# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("access_token", None),
    ("user_email", None),
    ("active_conv_id", None),
    ("conversations", []),
    ("auth_mode", "Login"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Auth gate ─────────────────────────────────────────────────────────────────
def show_auth():
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown("## 🤖 ChatGPT Replica")
    st.caption("Sign in or create an account to start chatting.")

    mode = st.radio("", ["Login", "Sign Up"],
                    index=0 if st.session_state.auth_mode == "Login" else 1,
                    horizontal=True, key="auth_mode_radio")
    st.session_state.auth_mode = mode

    with st.form("auth_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button(mode, use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            with st.spinner("Please wait…"):
                try:
                    if mode == "Login":
                        data = api.login(email, password)
                    else:
                        data = api.signup(email, password)

                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_email = data["email"]
                    st.session_state.conversations = api.list_conversations()
                    # Select most recent conversation if any
                    if st.session_state.conversations:
                        st.session_state.active_conv_id = st.session_state.conversations[0]["id"]
                    st.rerun()
                except RuntimeError as e:
                    st.error(f"❌ {e}")

    st.markdown('</div>', unsafe_allow_html=True)


# ── Main app ──────────────────────────────────────────────────────────────────
def show_app():
    # Refresh conversations list if empty
    if not st.session_state.conversations:
        try:
            st.session_state.conversations = api.list_conversations()
        except RuntimeError:
            pass

    conv_id = st.session_state.active_conv_id

    # ── Sidebar ──
    with st.sidebar:
        sidebar.render(st.session_state.conversations)

        # File upload section (in sidebar, below conversation list)
        if conv_id:
            st.divider()
            upload.render(conv_id)

    # ── Main chat area ──
    if not conv_id:
        col = st.columns([1, 2, 1])[1]
        with col:
            st.markdown("## 👋 Welcome!")
            st.markdown("Create or select a conversation from the sidebar to start chatting.")
            if st.button("➕ New Conversation", type="primary", key="welcome_new_conv"):
                try:
                    conv = api.create_conversation("New Conversation")
                    st.session_state.active_conv_id = conv["id"]
                    st.session_state.conversations = api.list_conversations()
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
    else:
        # Show conversation title in header
        active_conv = next(
            (c for c in st.session_state.conversations if c["id"] == conv_id), None
        )
        if active_conv:
            st.markdown(f"### 💬 {active_conv['title']}")
            st.divider()

        chat.render(conv_id)


# ── Router ────────────────────────────────────────────────────────────────────
if st.session_state.access_token:
    show_app()
else:
    show_auth()
