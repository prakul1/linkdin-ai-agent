"""Browse, edit, approve, reject, delete posts."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from api_client import (
    list_posts, get_post, update_post, approve_post,
    reject_post, delete_post, APIError,
)
from utils.ui_helpers import (
    init_session, show_error, show_success, status_badge,
    format_datetime, STYLE_LABELS,
)
st.set_page_config(page_title="My Posts", page_icon="📋", layout="wide")
init_session()
st.title("📋 My Posts")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    status_filter = st.selectbox(
        "Filter by status",
        options=["All", "draft", "approved", "scheduled", "published", "failed", "rejected"],
    )
with col_f2:
    style_filter = st.selectbox(
        "Filter by style",
        options=["All"] + list(STYLE_LABELS.keys()),
        format_func=lambda k: "All" if k == "All" else STYLE_LABELS[k],
    )
with col_f3:
    page_size = st.selectbox("Per page", [10, 20, 50], index=1)
try:
    response = list_posts(
        page=1, page_size=page_size,
        status=None if status_filter == "All" else status_filter,
        style=None if style_filter == "All" else style_filter,
    )
except APIError as e:
    show_error(e.detail)
    st.stop()
posts = response["items"]
st.caption(f"Showing {len(posts)} of {response['total']} posts")
if not posts:
    st.info("No posts match the current filters.")
    if st.button("➕ Generate your first post"):
        st.switch_page("pages/1_📝_Generate_Post.py")
    st.stop()
left, right = st.columns([1, 2])
with left:
    st.subheader("All posts")
    for post in posts:
        is_selected = st.session_state.selected_post_id == post["id"]
        label = f"**#{post['id']}** · {post['topic'][:50]}..."
        if st.button(
            label, key=f"sel_{post['id']}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state.selected_post_id = post["id"]
            st.rerun()
        st.caption(f"{status_badge(post['status'])} · {format_datetime(post['created_at'])}")
with right:
    if not st.session_state.selected_post_id:
        st.info("👈 Select a post on the left")
        st.stop()
    try:
        post = get_post(st.session_state.selected_post_id)
    except APIError as e:
        show_error(e.detail)
        st.session_state.selected_post_id = None
        st.stop()
    st.subheader(f"Post #{post['id']}")
    st.markdown(f"{status_badge(post['status'])} · _{STYLE_LABELS.get(post['style'], post['style'])}_")
    st.markdown(f"**Topic:** {post['topic']}")
    st.caption(f"Created: {format_datetime(post['created_at'])}")
    if post.get("safety_score") is not None:
        st.caption(f"Safety: {post['safety_score']}/100")
    if post.get("attachments"):
        with st.expander(f"📎 {len(post['attachments'])} attachment(s)"):
            for att in post["attachments"]:
                st.caption(f"- **{att['file_type']}**: {att.get('original_filename') or att.get('url')}")
    can_edit = post["status"] in ("draft", "approved")
    st.markdown("##### Content")
    edited_content = st.text_area(
        "Edit content", value=post.get("content", ""),
        height=350, disabled=not can_edit,
        key=f"edit_content_{post['id']}",
        label_visibility="collapsed",
    )
    edited_hashtags = st.text_input(
        "Hashtags", value=post.get("hashtags") or "",
        disabled=not can_edit,
        key=f"edit_tags_{post['id']}",
    )
    content_changed = edited_content != (post.get("content") or "")
    tags_changed = edited_hashtags != (post.get("hashtags") or "")
    if can_edit and (content_changed or tags_changed):
        if st.button("💾 Save Changes", type="primary"):
            try:
                update_post(post["id"],
                            content=edited_content if content_changed else None,
                            hashtags=edited_hashtags if tags_changed else None)
                show_success("Saved!")
                st.rerun()
            except APIError as e:
                show_error(e.detail)
    st.divider()
    col_a, col_b, col_c, col_d = st.columns(4)
    if post["status"] == "draft":
        with col_a:
            if st.button("✅ Approve", type="primary", use_container_width=True,
                         key=f"approve_{post['id']}"):
                try:
                    approve_post(post["id"])
                    show_success("Approved!")
                    st.rerun()
                except APIError as e:
                    show_error(e.detail)
        with col_b:
            if st.button("🚫 Reject", use_container_width=True,
                         key=f"reject_{post['id']}"):
                try:
                    reject_post(post["id"])
                    show_success("Rejected")
                    st.rerun()
                except APIError as e:
                    show_error(e.detail)
    if post["status"] == "approved":
        with col_a:
            if st.button("📅 Schedule", type="primary", use_container_width=True,
                         key=f"sched_{post['id']}"):
                st.session_state.selected_post_id = post["id"]
                st.switch_page("pages/3_📅_Scheduled.py")
    with col_d:
        if post["status"] != "published":
            if st.button("🗑️ Delete", use_container_width=True,
                         key=f"del_{post['id']}"):
                try:
                    delete_post(post["id"])
                    show_success("Deleted")
                    st.session_state.selected_post_id = None
                    st.rerun()
                except APIError as e:
                    show_error(e.detail)