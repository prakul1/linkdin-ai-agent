"""LinkedIn connection management + Manual Posting Queue."""
import streamlit as st
from frontend.api_client import (
    linkedin_status, linkedin_start, linkedin_disconnect,
    list_schedules, get_post, APIError,
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
        st.success("✅ **LinkedIn is connected** — your scheduled posts will publish automatically.")
        st.code(status.get("linkedin_user_urn", ""), language=None)
        if status.get("expires_in_message"):
            st.caption(f"ℹ️ {status['expires_in_message']}")
    else:
        st.warning("⚠️ **LinkedIn is NOT connected** — your posts will use Manual Mode.")
        st.markdown(
            "In Manual Mode, scheduled posts get marked as 'published' and appear "
            "in the **Manual Posting Queue** below for you to copy & paste."
        )
with col_action:
    if status["connected"]:
        if st.button("🔌 Disconnect", use_container_width=True):
            try:
                linkedin_disconnect()
                show_success("Disconnected. Refresh to see updated status.")
                st.rerun()
            except APIError as e:
                show_error(e.detail)
    else:
        if st.button("➡️ Connect LinkedIn", type="primary", use_container_width=True):
            try:
                result = linkedin_start()
                st.session_state["linkedin_auth_url"] = result["auth_url"]
            except APIError as e:
                show_error(f"{e.detail}\n\nIf no Developer App yet, you can still use Manual Mode.")
if st.session_state.get("linkedin_auth_url"):
    st.divider()
    st.markdown("### 🔗 Click the link below to authorize:")
    st.markdown(f"#### [👉 Open LinkedIn Authorization]({st.session_state['linkedin_auth_url']})")
    st.caption("After approving, you'll see a success page. Then refresh THIS page.")
st.divider()
st.subheader("📋 Manual Posting Queue")
st.caption(
    "Posts that were scheduled while LinkedIn was disconnected. "
    "Copy each one and paste into LinkedIn manually."
)
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
                st.caption(f"Originally scheduled for {format_datetime(sched['scheduled_at'])}")
                full_text = (post.get("content") or "").strip()
                if post.get("hashtags") and post["hashtags"] not in full_text:
                    full_text = f"{full_text}\n\n{post['hashtags']}"
                st.text_area(
                    "Ready to copy:", value=full_text, height=200,
                    key=f"manual_{post['id']}",
                )
                st.caption("👆 Click the copy icon in the top-right of the text box, then paste into LinkedIn.")
                col_open, col_done = st.columns(2)
                with col_open:
                    st.markdown("[🔗 Open LinkedIn → Create Post](https://www.linkedin.com/feed/?shareActive=true)")
                with col_done:
                    st.caption(f"LinkedIn ID: `{sched['linkedin_post_id']}`")
except APIError as e:
    show_error(e.detail)
st.divider()
with st.expander("ℹ️ How to set up LinkedIn API (one-time, ~10 min)"):
    st.markdown("""
### Step 1: Create a LinkedIn Developer App
1. Go to https://www.linkedin.com/developers/apps
2. Click **"Create app"**
3. Fill in name, attach a LinkedIn Page (create dummy if needed), upload logo
4. Click **Create app**
### Step 2: Add Required Products
In your app → **Products** tab, request:
- "Sign In with LinkedIn using OpenID Connect"
- "Share on LinkedIn"
### Step 3: Configure Redirect URL
In **Auth** tab → "Authorized redirect URLs" add: