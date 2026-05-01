"""Thin HTTP client wrapping our FastAPI backend."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from typing import Optional, List, Dict, Any
import requests
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 60
class APIError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")
def _request(method, path, **kwargs):
    url = f"{API_BASE}{path}"
    kwargs.setdefault("timeout", TIMEOUT)
    try:
        r = requests.request(method, url, **kwargs)
    except requests.exceptions.ConnectionError:
        raise APIError(0, f"Cannot reach backend at {API_BASE}. Is it running?")
    except requests.exceptions.Timeout:
        raise APIError(0, "Request timed out")
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise APIError(r.status_code, str(detail))
    if r.status_code == 204:
        return None
    return r.json()
# === POSTS ===
def generate_post(topic, style, additional_instructions=None, attachment_ids=None):
    payload = {
        "topic": topic, "style": style,
        "attachment_ids": attachment_ids or [],
    }
    if additional_instructions:
        payload["additional_instructions"] = additional_instructions
    return _request("POST", "/api/posts/generate", json=payload)
def list_posts(page=1, page_size=20, status=None, style=None):
    params = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if style:
        params["style"] = style
    return _request("GET", "/api/posts", params=params)
def get_post(post_id):
    return _request("GET", f"/api/posts/{post_id}")
def update_post(post_id, content=None, hashtags=None):
    payload = {}
    if content is not None:
        payload["content"] = content
    if hashtags is not None:
        payload["hashtags"] = hashtags
    return _request("PATCH", f"/api/posts/{post_id}", json=payload)
def approve_post(post_id):
    return _request("POST", f"/api/posts/{post_id}/approve")
def reject_post(post_id, reason=None):
    payload = {"reason": reason} if reason else {}
    return _request("POST", f"/api/posts/{post_id}/reject", json=payload)
def delete_post(post_id):
    return _request("DELETE", f"/api/posts/{post_id}")
# === UPLOADS ===
def upload_file(file_bytes, filename, content_type, post_id):
    files = {"file": (filename, file_bytes, content_type)}
    data = {"post_id": str(post_id)}
    return _request("POST", "/api/uploads/file", files=files, data=data)
def upload_link(url, post_id):
    return _request("POST", "/api/uploads/link",
                    json={"url": url, "post_id": post_id})
def delete_attachment(attachment_id):
    return _request("DELETE", f"/api/uploads/{attachment_id}")
# === SCHEDULES ===
def schedule_post(post_id, scheduled_at_iso):
    return _request("POST", "/api/schedules",
                    json={"post_id": post_id, "scheduled_at": scheduled_at_iso})
def list_schedules(status=None):
    params = {"status": status} if status else {}
    return _request("GET", "/api/schedules", params=params)
def cancel_schedule(schedule_id):
    return _request("POST", f"/api/schedules/{schedule_id}/cancel")
def suggest_times(count=5, timezone="UTC"):
    return _request("POST", "/api/schedules/suggest-times",
                    json={"count": count, "timezone": timezone})
def list_active_jobs():
    return _request("GET", "/api/schedules/active-jobs")
# === RAG ===
def rag_stats():
    return _request("GET", "/api/rag/stats")
def check_safety(content):
    return _request("POST", "/api/rag/check-safety", json={"content": content})