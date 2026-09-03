import streamlit as st
from services import api_client as api


def render(conv_id: str):
    """
    File upload widget for the currently selected conversation.
    Accepts .txt and .pdf files; shows uploaded files and allows deletion.

    The upload-counter trick prevents the widget from re-triggering on every
    Streamlit rerun: after a successful upload we bump the counter, which
    changes the widget key, which resets the widget to an empty state.
    """
    if not conv_id:
        return

    st.subheader("📎 Documents")

    # Per-conversation upload counter — changing it resets the file_uploader widget
    counter_key = f"upload_counter_{conv_id}"
    if counter_key not in st.session_state:
        st.session_state[counter_key] = 0

    upload_widget_key = f"uploader_{conv_id}_{st.session_state[counter_key]}"

    uploaded = st.file_uploader(
        "Upload a .txt or .pdf file",
        type=["txt", "pdf"],
        key=upload_widget_key,
    )

    if uploaded is not None:
        with st.spinner(f"Processing {uploaded.name}…"):
            try:
                api.upload_file(
                    conversation_id=conv_id,
                    file_name=uploaded.name,
                    file_bytes=uploaded.read(),
                )
                st.success(f"✅ **{uploaded.name}** uploaded and indexed!")
                # Bump counter → new widget key on next render → widget resets to empty
                st.session_state[counter_key] += 1
                # Clear the cached file list so it reloads
                st.session_state.pop(f"files_{conv_id}", None)
                st.rerun()
            except RuntimeError as e:
                st.error(f"Upload failed: {e}")

    # File list section
    file_key = f"files_{conv_id}"
    if file_key not in st.session_state:
        try:
            st.session_state[file_key] = api.list_files(conv_id)
        except RuntimeError:
            st.session_state[file_key] = []

    files: list = st.session_state[file_key]
    if files:
        st.caption(f"{len(files)} file(s) indexed:")
        for f in files:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.caption(f"📄 {f['filename']}")
            with col2:
                if st.button("🗑", key=f"del_file_{f['id']}", help="Delete file"):
                    try:
                        api.delete_file(f["id"])
                        st.session_state.pop(file_key, None)
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))
    else:
        st.caption("No files uploaded yet.")
