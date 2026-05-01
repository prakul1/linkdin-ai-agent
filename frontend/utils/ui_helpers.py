"""Shared UI helper functions and constants for Streamlit pages."""
import streamlit as st
from datetime import datetime
STATUS_BADGES = {
    "draft":      ("📝", "gray", "Draft"),
    "approved":   ("✅", "blue", "Approved"),
    "scheduled":  ("📅", "orange", "Scheduled"),
    "publishing": ("⏳", "violet", "Publishing"),
    "published":  ("🎉", "green", "Published"),
    "failed":     ("❌", "red", "Failed"),
    "rejected":   ("🚫", "red", "Rejected"),
}
STYLE_LABELS = {
    "formal": "🎩 Formal",
    "storytelling": "📖 Storytelling",
    "thought_leadership": "💡 Thought Leadership",
}
def status_badge(status):
    emoji, color, label = STATUS_BADGES.get(status, ("❓", "gray", status.title()))
    return f":{color}[{emoji} **{label}**]"
def show_error(error):
    st.error(f"❌ {error}", icon="🚨")
def show_success(message):
    st.success(f"✅ {message}")
def format_datetime(dt_str):
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except Exception:
        return dt_str
def init_session():
    if "selected_post_id" not in st.session_state:
        st.session_state.selected_post_id = None
    if "last_generated_id" not in st.session_state:
        st.session_state.last_generated_id = None