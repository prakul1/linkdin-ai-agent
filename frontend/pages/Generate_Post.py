"""Generate a new LinkedIn post."""
import streamlit as st
from frontend.api_client import (
    generate_post, upload_file, upload_link, get_post, APIError,
)
from frontend.utils.ui_helpers import (
    init_session, show_error, show_success, status_badge, STYLE_LABELS,
)
st.set_page_config(page_title="Generate Post", page_icon="📝", layout="wide")
init_session()
st.title("📝 Generate a New Post")
st.caption("Tell the agent what you want to write about. It handles the rest.")
with st.form("generate_form", clear_on_submit=False):
    topic = st.text_area(
        "What do you want to post about?",
        placeholder="e.g., I just got AWS certified after 3 months of prep!",
        height=100,
        max_chars=2000,
    )
    col1, col2 = st.columns(2)
    with col1:
        style = st.selectbox(
            "Writing style",
            options=list(STYLE_LABELS.keys()),
            format_func=lambda k: STYLE_LABELS[k],
        )
    with col2:
        st.text("")
        st.text("")
        submit = st.form_submit_button("✨ Generate Draft", type="primary",
                                       use_container_width=True)
    additional = st.text_area(
        "Additional instructions (optional)",
        placeholder="e.g., Mention I'm hiring. Keep it under 200 words.",
        max_chars=500,
        height=80,
    )
if submit:
    if not topic or len(topic) < 5:
        show_error("Topic must be at least 5 characters.")
    else:
        with st.spinner("🤖 Agent thinking..."):
            try:
                post = generate_post(
                    topic=topic, style=style,
                    additional_instructions=additional or None,
                )
                st.session_state.last_generated_id = post["id"]
                show_success(f"Draft created! Post #{post['id']}")
            except APIError as e:
                show_error(f"Generation failed: {e.detail}")
if st.session_state.last_generated_id:
    st.divider()
    st.subheader(f"Latest Draft (#{st.session_state.last_generated_id})")
    try:
        post = get_post(st.session_state.last_generated_id)
    except APIError as e:
        show_error(e.detail)
        st.stop()
    st.markdown(f"**Status:** {status_badge(post['status'])}")
    st.markdown(f"**Style:** {STYLE_LABELS.get(post['style'], post['style'])}")
    if post.get("safety_score") is not None:
        st.markdown(f"**Safety score:** {post['safety_score']}/100")
    st.markdown("##### Generated Content")
    st.text_area(
        "Content", value=post.get("content", ""),
        height=400, label_visibility="collapsed",
        key=f"preview_{post['id']}",
    )
    if post.get("hashtags"):
        st.caption(f"🏷️ {post['hashtags']}")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Approve & Continue", type="primary", use_container_width=True):
            st.session_state.selected_post_id = post["id"]
            st.switch_page("pages/My_Posts.py")
    with col2:
        if st.button("✏️ Edit Manually", use_container_width=True):
            st.session_state.selected_post_id = post["id"]
            st.switch_page("pages/My_Posts.py")
    with col3:
        if st.button("🗑️ Discard", use_container_width=True):
            st.session_state.last_generated_id = None
            st.rerun()
if st.session_state.last_generated_id:
    st.divider()
    with st.expander("📎 Attach a file or link (optional)"):
        tab_file, tab_link = st.tabs(["📄 Upload File", "🔗 Add Link"])
        with tab_file:
            uploaded = st.file_uploader(
                "Choose a PDF or image",
                type=["pdf", "png", "jpg", "jpeg", "webp"],
            )
            if uploaded and st.button("Upload File"):
                try:
                    result = upload_file(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        content_type=uploaded.type or "application/octet-stream",
                        post_id=st.session_state.last_generated_id,
                    )
                    show_success(f"Extracted {result['extracted_text_length']} chars.")
                    with st.expander("Preview"):
                        st.code(result.get("extracted_text_preview", ""))
                except APIError as e:
                    show_error(e.detail)
        with tab_link:
            url = st.text_input("Paste a URL")
            if url and st.button("Ingest Link"):
                try:
                    result = upload_link(
                        url=url, post_id=st.session_state.last_generated_id,
                    )
                    show_success(f"Extracted {result['extracted_text_length']} chars.")
                    with st.expander("Preview"):
                        st.code(result.get("extracted_text_preview", ""))
                except APIError as e:
                    show_error(e.detail)