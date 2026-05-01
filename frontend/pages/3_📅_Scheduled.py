"""Schedule approved posts and view existing schedules."""
import streamlit as st
from datetime import datetime, timedelta, time as time_cls
from zoneinfo import ZoneInfo
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from api_client import (
    list_posts, schedule_post, list_schedules, cancel_schedule,
    suggest_times, list_active_jobs, get_post, APIError,
)
from utils.ui_helpers import (
    init_session, show_error, show_success, format_datetime,
)
st.set_page_config(page_title="Scheduled", page_icon="📅", layout="wide")
init_session()
st.title("📅 Scheduling")
tab_new, tab_existing, tab_jobs = st.tabs(
    ["➕ Schedule New", "📋 My Schedules", "🔧 Active Jobs (debug)"]
)
with tab_new:
    st.subheader("Schedule an Approved Post")
    try:
        approved = list_posts(page_size=100, status="approved")
    except APIError as e:
        show_error(e.detail)
        st.stop()
    if not approved["items"]:
        st.info("No approved posts available. Approve a post first.")
        if st.button("Go to My Posts"):
            st.switch_page("pages/2_📋_My_Posts.py")
    else:
        post_options = {
            f"#{p['id']} - {p['topic'][:60]}...": p["id"]
            for p in approved["items"]
        }
        default_idx = 0
        if st.session_state.selected_post_id:
            for i, (label, pid) in enumerate(post_options.items()):
                if pid == st.session_state.selected_post_id:
                    default_idx = i
                    break
        selected_label = st.selectbox(
            "Choose a post to schedule",
            list(post_options.keys()), index=default_idx,
        )
        selected_post_id = post_options[selected_label]
        with st.expander("Preview post content"):
            try:
                post = get_post(selected_post_id)
                st.markdown(post.get("content", ""))
                if post.get("hashtags"):
                    st.caption(f"🏷️ {post['hashtags']}")
            except APIError as e:
                show_error(e.detail)
        st.divider()
        st.markdown("##### 💡 Recommended Posting Times")
        col_tz, col_count = st.columns(2)
        with col_tz:
            tz_name = st.text_input("Your timezone", value="Asia/Kolkata")
        with col_count:
            count = st.slider("How many suggestions?", 3, 10, 5)
        if st.button("Get Suggestions"):
            try:
                suggs = suggest_times(count=count, timezone=tz_name)
                st.session_state["last_suggestions"] = suggs
            except APIError as e:
                show_error(e.detail)
        if "last_suggestions" in st.session_state:
            suggs = st.session_state["last_suggestions"]
            st.caption(f"Times shown in **{suggs['timezone']}**")
            for s in suggs["suggestions"]:
                st.markdown(f"- 📅 **{format_datetime(s['suggested_at'])}** — _{s['reason']}_")
        st.divider()
        st.markdown("##### 🕐 Pick a Date & Time")
        col_d, col_t, col_z = st.columns(3)
        with col_d:
            sched_date = st.date_input(
                "Date",
                value=datetime.now().date() + timedelta(days=1),
                min_value=datetime.now().date(),
            )
        with col_t:
            sched_time = st.time_input("Time", value=time_cls(9, 0))
        with col_z:
            tz_for_pick = st.text_input(
                "Timezone for picker", value=tz_name, key="tz_picker",
            )
        try:
            local_tz = ZoneInfo(tz_for_pick)
        except Exception:
            show_error(f"Invalid timezone: {tz_for_pick}")
            st.stop()
        local_dt = datetime.combine(sched_date, sched_time, tzinfo=local_tz)
        utc_iso = local_dt.astimezone(ZoneInfo("UTC")).isoformat()
        st.info(f"Will publish at **{format_datetime(local_dt.isoformat())}**")
        if st.button("📅 Schedule Now", type="primary", use_container_width=True):
            try:
                result = schedule_post(post_id=selected_post_id, scheduled_at_iso=utc_iso)
                show_success(f"Scheduled! ID: {result['id']}")
                st.balloons()
            except APIError as e:
                show_error(e.detail)
with tab_existing:
    st.subheader("My Schedules")
    status_filter = st.selectbox(
        "Status filter",
        ["All", "pending", "running", "completed", "failed", "cancelled"],
        key="sched_status_filter",
    )
    try:
        schedules = list_schedules(
            status=None if status_filter == "All" else status_filter
        )
    except APIError as e:
        show_error(e.detail)
        st.stop()
    if not schedules:
        st.info("No schedules found.")
    else:
        for sched in schedules:
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**Schedule #{sched['id']}** for Post #{sched['post_id']}")
                    st.caption(
                        f"📅 {format_datetime(sched['scheduled_at'])} · "
                        f"Status: **{sched['status']}** · "
                        f"Attempts: {sched['attempts']}/{sched['max_attempts']}"
                    )
                    if sched.get("posted_at"):
                        st.caption(f"✅ Posted: {format_datetime(sched['posted_at'])}")
                    if sched.get("linkedin_post_id"):
                        st.caption(f"🔗 LinkedIn ID: `{sched['linkedin_post_id']}`")
                    if sched.get("error_message"):
                        st.caption(f"⚠️ Error: {sched['error_message']}")
                with col_action:
                    if sched["status"] in ("pending", "failed"):
                        if st.button("❌ Cancel", key=f"cancel_{sched['id']}",
                                     use_container_width=True):
                            try:
                                cancel_schedule(sched["id"])
                                show_success("Cancelled")
                                st.rerun()
                            except APIError as e:
                                show_error(e.detail)
with tab_jobs:
    st.subheader("APScheduler Active Jobs")
    st.caption("Internal debug view of in-process scheduler jobs.")
    try:
        jobs = list_active_jobs()
        if not jobs:
            st.info("No active jobs")
        else:
            for job in jobs:
                st.code(
                    f"Job ID: {job['id']}\n"
                    f"Next run: {job['next_run_time']}\n"
                    f"Args: {job['args']}"
                )
    except APIError as e:
        show_error(e.detail)