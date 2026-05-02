"""LinkedIn API integration — OAuth + posting."""
import secrets
from urllib.parse import urlencode
from typing import Optional, Dict
import requests
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.utils.linkedin_constants import (
    LINKEDIN_AUTH_URL, LINKEDIN_TOKEN_URL, USERINFO_URL,
    UGC_POSTS_URL, DEFAULT_SCOPES, LINKEDIN_VERSION,
)
from app.utils.logger import logger
class LinkedInError(Exception):
    pass
class LinkedInService:
    def __init__(self, db: Session):
        self.db = db
        self.client_id = settings.linkedin_client_id
        self.client_secret = settings.linkedin_client_secret
        self.redirect_uri = settings.linkedin_redirect_uri
    def is_configured(self):
        return bool(self.client_id and self.client_secret and self.redirect_uri)
    def build_auth_url(self):
        if not self.is_configured():
            raise LinkedInError("LinkedIn credentials not configured")
        state = secrets.token_urlsafe(16)
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(DEFAULT_SCOPES),
        }
        url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
        return {"auth_url": url, "state": state}
    def exchange_code_for_token(self, code):
        if not self.is_configured():
            raise LinkedInError("LinkedIn credentials not configured")
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            r = requests.post(
                LINKEDIN_TOKEN_URL, data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
        except requests.RequestException as e:
            raise LinkedInError(f"Token exchange request failed: {e}")
        if not r.ok:
            raise LinkedInError(f"Token exchange failed: {r.text}")
        return r.json()
    def fetch_user_urn(self, access_token):
        try:
            r = requests.get(
                USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15,
            )
        except requests.RequestException as e:
            raise LinkedInError(f"Userinfo request failed: {e}")
        if not r.ok:
            raise LinkedInError(f"Userinfo failed: {r.status_code} {r.text}")
        data = r.json()
        sub = data.get("sub")
        if not sub:
            raise LinkedInError(f"No 'sub' in userinfo response: {data}")
        return f"urn:li:person:{sub}"
    def store_tokens(self, user, access_token, refresh_token, user_urn):
        user.linkedin_access_token = access_token
        user.linkedin_refresh_token = refresh_token
        user.linkedin_user_urn = user_urn
        self.db.commit()
        logger.info(f"Stored LinkedIn tokens for user {user.id}")
    def disconnect(self, user):
        user.linkedin_access_token = None
        user.linkedin_refresh_token = None
        user.linkedin_user_urn = None
        self.db.commit()
    def publish_text_post(self, access_token, author_urn, text):
        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_VERSION,
        }
        try:
            r = requests.post(UGC_POSTS_URL, json=body, headers=headers, timeout=30)
        except requests.RequestException as e:
            raise LinkedInError(f"Publish request failed: {e}")
        if not r.ok:
            raise LinkedInError(f"LinkedIn rejected post: [{r.status_code}] {r.text}")
        post_urn = r.headers.get("x-restli-id") or r.json().get("id")
        if not post_urn:
            raise LinkedInError(f"Publish succeeded but no URN returned")
        logger.info(f"Published to LinkedIn: {post_urn}")
        return post_urn
    def is_user_connected(self, user):
        return bool(user.linkedin_access_token and user.linkedin_user_urn)