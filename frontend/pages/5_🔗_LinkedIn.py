"""LinkedIn page — Phase 9.5: media download in manual queue."""
import streamlit as st
from frontend.api_client import (
    linkedin_status, linkedin_start, linkedin_disconnect,
    list_schedules, get_post, attachment_download_url, APIError,
)
from frontend.utils.ui_helpers import (
    init_session, show_error, show_success, format_datetime,
)
st.set_page_config(page_title="LinkedIn", page_icon="🔗", layout="wide")
init_session()
st.title("🔗 LinkedIn Connection")
try:
    status = linkedin_status()
except APIError as e:
    show_error(f"Couldn't fetch status: {e.detail}")
    st.stop()
col_status, col_action = st.columns([2, 1])
with col_status:
    if status["connected"]:
        st.success("✅ **LinkedIn is connected** — your scheduled posts will publish automatically (including media).")
        st.code(status.get("linkedin_user_urn", ""), language=None)
        if status.get("expires_in_message"):
            st.caption(f"ℹ️ {status['expires_in_message']}")
    else:
        st.warning("⚠️ **LinkedIn is NOT connected** — your posts will use Manual Mode.")
with col_action:
    if status["connected"]:
        if st.button("🔌 Disconnect", use_container_width=True):
            try:
                linkedin_disconnect()
                show_success("Disconnected.")
                st.rerun()
            except APIError as e:
                show_error(e.detail)
    else:
        if st.button("➡️ Connect LinkedIn", type="primary", use_container_width=True):
            try:
                result = linkedin_start()
                st.session_state["linkedin_auth_url"] = result["auth_url"]
            except APIError as e:
                show_error(f"{e.detail}")
if st.session_state.get("linkedin_auth_url"):
    st.divider()
    st.markdown("### 🔗 Click the link below to authorize:")
    st.markdown(f"#### [👉 Open LinkedIn Authorization]({st.session_state['linkedin_auth_url']})")
st.divider()
st.subheader("📋 Manual Posting Queue")
st.caption("Posts scheduled while LinkedIn was disconnected. Copy text + download media.")
try:
    completed_schedules = list_schedules(status="completed")
    manual_schedules = [
        s for s in completed_schedules
        if s.get("linkedin_post_id", "").startswith("manual:")
    ]
    if not manual_schedules:
        st.info("✨ No manual posts in queue. Everything is auto-posted!")
    else:
        for sched in manual_schedules:
            try:
                post = get_post(sched["post_id"])
            except APIError:
                continue
            with st.container(border=True):
                st.markdown(f"**Post #{post['id']}** — {post['topic'][:80]}")
                st.caption(f"Scheduled for {format_datetime(sched['scheduled_at'])}")
                full_text = (post.get("content") or "").strip()
                if post.get("hashtags") and post["hashtags"] not in full_text:
                    full_text = f"{full_text}\n\n{post['hashtags']}"
                st.text_area(
                    "Ready to copy:", value=full_text, height=180,
                    key=f"manual_{post['id']}",
                )
                # Phase 9.5: show media with download buttons
                media = [a for a in post.get("attachments", []) if a.get("is_media")]
                if media:
                    st.markdown(f"**📎 Media to attach ({len(media)}):**")
                    media_cols = st.columns(min(len(media), 3))
                    for idx, m in enumerate(media):
                        with media_cols[idx]:
                            if m["file_type"] == "image":
                                st.image(
                                    attachment_download_url(m["id"]),
                                    use_container_width=True,
                                )
                            st.markdown(
                                f"[📥 Download {m['original_filename']}]"
                                f"({attachment_download_url(m['id'])})"
                            )
                st.caption("👆 Copy text, download media, paste both into LinkedIn manually.")
                st.markdown(
                    "[🔗 Open LinkedIn → Create Post](https://www.linkedin.com/feed/?shareActive=true)"
                )
except APIError as e:
    show_error(e.detail)
st.divider()
with st.expander("ℹ️ How to set up LinkedIn API"):
    st.markdown("""
1. https://www.linkedin.com/developers/apps → Create app
2. **Products** tab → request "Sign In with LinkedIn" + "Share on LinkedIn"
3. **Auth** tab → add redirect URL: `http://localhost:8000/api/auth/linkedin/callback`
4. Copy Client ID + Secret → add to `.env`:""")