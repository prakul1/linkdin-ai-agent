"""Generate page — Phase 9.5: vibes (mandatory) + separate context/media uploads."""
import streamlit as st
from frontend.api_client import (
    generate_post, upload_file, upload_media, upload_link, get_post,
    delete_attachment, APIError,
)
from frontend.utils.ui_helpers import (
    init_session, show_error, show_success, status_badge, STYLE_LABELS,
)
st.set_page_config(page_title="Generate Post", page_icon="📝", layout="wide")
init_session()
# Vibe definitions for UI
VIBE_OPTIONS = {
    "funny": "😄 Funny",
    "serious": "🎯 Serious",
    "motivational": "🔥 Motivational",
    "witty": "✨ Witty",
    "casual": "😎 Casual",
    "professional": "💼 Professional",
    "insightful": "🧠 Insightful",
    "emotional": "❤️ Emotional",
    "celebratory": "🎉 Celebratory",
    "auto": "🤖 Auto (let AI decide)",
}
st.title("📝 Generate a New Post")
st.caption("Tell the agent the topic, vibe, and style. It handles the rest.")
# ============== INPUT FORM ==============
with st.form("generate_form", clear_on_submit=False):
    topic = st.text_area(
        "What do you want to post about? *",
        placeholder="e.g., I just got AWS certified after 3 months of prep!",
        height=100,
        max_chars=2000,
    )
    col1, col2 = st.columns(2)
    with col1:
        style = st.selectbox(
            "Writing style *",
            options=list(STYLE_LABELS.keys()),
            format_func=lambda k: STYLE_LABELS[k],
        )
    with col2:
        st.markdown("**Tone / Vibe** (required, pick 1+) *")
        st.caption("Tip: combine 2-3 vibes for richer tone. Or just pick 🤖 Auto.")
    # Vibe multi-select using checkboxes (3 columns)
    vibe_cols = st.columns(3)
    selected_vibes = []
    for idx, (key, label) in enumerate(VIBE_OPTIONS.items()):
        col = vibe_cols[idx % 3]
        if col.checkbox(label, key=f"vibe_{key}"):
            selected_vibes.append(key)
    additional = st.text_area(
        "Extra instructions (optional)",
        placeholder="e.g., Mention I'm hiring. Keep it under 200 words. Add 1 emoji per paragraph.",
        max_chars=500,
        height=80,
    )
    submit = st.form_submit_button("✨ Generate Draft", type="primary",
                                   use_container_width=True)
if submit:
    if not topic or len(topic) < 5:
        show_error("Topic must be at least 5 characters.")
    elif not selected_vibes:
        show_error("Pick at least one vibe (or just check '🤖 Auto').")
    else:
        with st.spinner(f"🤖 Generating with vibes: {', '.join(selected_vibes)}..."):
            try:
                # Get attachment_ids from session (for re-generation after attaching)
                attachment_ids = st.session_state.get("current_attachment_ids", [])
                post = generate_post(
                    topic=topic,
                    style=style,
                    vibes=selected_vibes,
                    additional_instructions=additional or None,
                    attachment_ids=attachment_ids,
                )
                st.session_state.last_generated_id = post["id"]
                st.session_state["current_attachment_ids"] = []  # reset for next gen
                show_success(f"Draft #{post['id']} created! Safety: {post.get('safety_score', '—')}/100")
            except APIError as e:
                show_error(f"Generation failed: {e.detail}")
# ============== SHOW LAST GENERATED ==============
if st.session_state.last_generated_id:
    st.divider()
    st.subheader(f"Latest Draft (#{st.session_state.last_generated_id})")
    try:
        post = get_post(st.session_state.last_generated_id)
    except APIError as e:
        show_error(f"Couldn't load post: {e.detail}")
        st.stop()
    st.markdown(f"**Status:** {status_badge(post['status'])}")
    if post.get("safety_score") is not None:
        st.markdown(f"**Safety score:** {post['safety_score']}/100")
    st.markdown("##### Generated Content")
    st.text_area(
        "Content", value=post.get("content", ""),
        height=350, label_visibility="collapsed",
        key=f"preview_{post['id']}",
    )
    if post.get("hashtags"):
        st.caption(f"🏷️ {post['hashtags']}")
    # Show attached media (if any)
    media = [a for a in post.get("attachments", []) if a.get("is_media")]
    context_atts = [a for a in post.get("attachments", []) if not a.get("is_media")]
    if media:
        st.markdown(f"##### 🖼️ Media to Post ({len(media)})")
        media_cols = st.columns(min(len(media), 3))
        for idx, m in enumerate(media):
            with media_cols[idx]:
                st.caption(f"**{m['file_type']}**: {m['original_filename']}")
                if m['file_type'] == "image":
                    from frontend.api_client import attachment_download_url
                    st.image(attachment_download_url(m['id']), use_container_width=True)
                else:
                    st.info(f"📹 {m['original_filename']}")
                if st.button("🗑️ Remove", key=f"rm_media_{m['id']}"):
                    try:
                        delete_attachment(m['id'])
                        show_success("Removed")
                        st.rerun()
                    except APIError as e:
                        show_error(e.detail)
    if context_atts:
        with st.expander(f"📎 Context references ({len(context_atts)})"):
            for a in context_atts:
                st.caption(f"- **{a['file_type']}**: {a.get('original_filename') or a.get('url')}")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Approve & Continue", type="primary", use_container_width=True):
            st.session_state.selected_post_id = post["id"]
            st.switch_page("pages/2_📋_My_Posts.py")
    with col2:
        if st.button("✏️ Edit Manually", use_container_width=True):
            st.session_state.selected_post_id = post["id"]
            st.switch_page("pages/2_📋_My_Posts.py")
    with col3:
        if st.button("🗑️ Discard & Start Over", use_container_width=True):
            st.session_state.last_generated_id = None
            st.rerun()
# ============== TWO SEPARATE UPLOAD SECTIONS ==============
if st.session_state.last_generated_id:
    st.divider()
    st.subheader("📎 Add Attachments")
    tab_context, tab_media = st.tabs([
        "📚 Reference Material (LLM context)",
        "🖼️ Media to Post (with content)",
    ])
    # ===== CONTEXT TAB =====
    with tab_context:
        st.caption(
            "Files/links the AI will **read** to better understand your topic. "
            "Not posted to LinkedIn."
        )
        sub_file, sub_link = st.tabs(["📄 PDF/Image", "🔗 Link"])
        with sub_file:
            uploaded = st.file_uploader(
                "PDF or image for OCR/text extraction",
                type=["pdf", "png", "jpg", "jpeg", "webp"],
                key="ctx_uploader",
            )
            if uploaded and st.button("Upload as Context", key="ctx_btn"):
                try:
                    result = upload_file(
                        file_bytes=uploaded.getvalue(),
                        filename=uploaded.name,
                        content_type=uploaded.type or "application/octet-stream",
                        post_id=st.session_state.last_generated_id,
                    )
                    show_success(f"Extracted {result['extracted_text_length']} chars")
                    with st.expander("Preview extracted text"):
                        st.code(result.get("extracted_text_preview", ""))
                    st.info("💡 Now click '✨ Generate Draft' again above to regenerate with this context.")
                except APIError as e:
                    show_error(e.detail)
        with sub_link:
            url = st.text_input("URL", key="ctx_url")
            if url and st.button("Ingest Link", key="ctx_link_btn"):
                try:
                    result = upload_link(
                        url=url, post_id=st.session_state.last_generated_id,
                    )
                    show_success(f"Extracted {result['extracted_text_length']} chars")
                    with st.expander("Preview"):
                        st.code(result.get("extracted_text_preview", ""))
                    st.info("💡 Click '✨ Generate Draft' again to use this link's content.")
                except APIError as e:
                    show_error(e.detail)
    # ===== MEDIA TAB =====
    with tab_media:
        st.caption(
            "Images/videos that will be **posted along with your text** on LinkedIn. "
            "Max 3 files. (Can't mix images + videos in one post.)"
        )
        st.warning(
            "🎬 **Videos:** MP4/MOV only, max 30MB. Take longer to upload.",
            icon="ℹ️",
        )
        media_uploaded = st.file_uploader(
            "Choose image or video",
            type=["png", "jpg", "jpeg", "webp", "mp4", "mov"],
            key="media_uploader",
        )
        if media_uploaded and st.button("Attach as Media", key="media_btn"):
            try:
                result = upload_media(
                    file_bytes=media_uploaded.getvalue(),
                    filename=media_uploaded.name,
                    content_type=media_uploaded.type or "application/octet-stream",
                    post_id=st.session_state.last_generated_id,
                )
                show_success(f"Media attached: {result['original_filename']}")
                st.rerun()  # Refresh to show in preview
            except APIError as e:
                show_error(e.detail)