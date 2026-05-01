"""Streamlit entry point — main dashboard / home page."""
import streamlit as st
from frontend.api_client import (
    list_posts, list_schedules, rag_stats, APIError,
)
from frontend.utils.ui_helpers import init_session, show_error, status_badge
st.set_page_config(
    page_title="LinkedIn AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_session()
st.title("🤖 LinkedIn AI Agent")
st.caption("Your personal content automation assistant")
st.divider()
col1, col2, col3, col4 = st.columns(4)
try:
    posts = list_posts(page_size=100)
    total_posts = posts["total"]
    by_status = {}
    for p in posts["items"]:
        s = p["status"]
        by_status[s] = by_status.get(s, 0) + 1
    with col1:
        st.metric("📚 Total Posts", total_posts)
    with col2:
        st.metric("📝 Drafts", by_status.get("draft", 0))
    with col3:
        st.metric("📅 Scheduled", by_status.get("scheduled", 0))
    with col4:
        st.metric("🎉 Published", by_status.get("published", 0))
except APIError as e:
    show_error(f"Couldn't load stats: {e.detail}")
    st.info("Make sure backend is running: `uvicorn app.main:app --reload --port 8000`")
    st.stop()
st.divider()
col_rag, col_jobs = st.columns(2)
with col_rag:
    st.subheader("🧠 Memory (RAG)")
    try:
        stats = rag_stats()
        st.metric("Documents in vector store", stats["total_documents"])
    except APIError as e:
        show_error(f"RAG stats unavailable: {e.detail}")
with col_jobs:
    st.subheader("⏰ Scheduled Jobs")
    try:
        scheds = list_schedules(status="pending")
        st.metric("Pending publishes", len(scheds))
        if scheds:
            next_one = min(scheds, key=lambda s: s["scheduled_at"])
            st.caption(f"Next: {next_one['scheduled_at']}")
    except APIError as e:
        show_error(f"Schedule data unavailable: {e.detail}")
st.divider()
st.subheader("📰 Recent Posts")
try:
    recent = list_posts(page=1, page_size=5)
    if not recent["items"]:
        st.info("No posts yet. Head to **📝 Generate Post** to create your first one!")
    else:
        for post in recent["items"]:
            with st.container(border=True):
                col_meta, col_btn = st.columns([4, 1])
                with col_meta:
                    st.markdown(f"**Topic:** {post['topic'][:120]}")
                    st.markdown(
                        f"{status_badge(post['status'])} · "
                        f"_{post['style'].replace('_', ' ').title()}_ · "
                        f"`#{post['id']}`"
                    )
                with col_btn:
                    if st.button("View →", key=f"view_{post['id']}"):
                        st.session_state.selected_post_id = post["id"]
                        st.switch_page("pages/My_Posts.py")
except APIError as e:
    show_error(f"Couldn't load recent posts: {e.detail}")
with st.sidebar:
    st.markdown("### 🚀 Quick Actions")
    if st.button("✨ New Post", use_container_width=True, type="primary"):
        st.switch_page("pages/Generate_Post.py")
    if st.button("📋 All Posts", use_container_width=True):
        st.switch_page("pages/My_Posts.py")
    if st.button("📅 Schedules", use_container_width=True):
        st.switch_page("pages/Scheduled.py")
    if st.button("💰 Cost Dashboard", use_container_width=True):
        st.switch_page("pages/Cost_Dashboard.py")
    st.divider()
    st.caption("Built with FastAPI + LangGraph + ChromaDB")