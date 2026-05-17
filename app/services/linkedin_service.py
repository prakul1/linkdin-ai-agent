"""LinkedIn API integration — Phase 9.5: now supports media (image + video) posts."""
import secrets
from urllib.parse import urlencode
from typing import Optional, Dict, List
import requests
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.utils.linkedin_constants import (
    LINKEDIN_AUTH_URL, LINKEDIN_TOKEN_URL, USERINFO_URL,
    UGC_POSTS_URL, ASSETS_REGISTER_URL,
    DEFAULT_SCOPES, LINKEDIN_VERSION,
)
from app.utils.logger import logger
# LinkedIn API recipes
RECIPE_IMAGE = "urn:li:digitalmediaRecipe:feedshare-image"
RECIPE_VIDEO = "urn:li:digitalmediaRecipe:feedshare-video"
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
    # ============== OAUTH (unchanged from Phase 9) ==============
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
            "grant_type": "authorization_code", "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id, "client_secret": self.client_secret,
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
        sub = r.json().get("sub")
        if not sub:
            raise LinkedInError("No 'sub' in userinfo")
        return f"urn:li:person:{sub}"
    def store_tokens(self, user, access_token, refresh_token, user_urn):
        user.linkedin_access_token = access_token
        user.linkedin_refresh_token = refresh_token
        user.linkedin_user_urn = user_urn
        self.db.commit()
    def disconnect(self, user):
        user.linkedin_access_token = None
        user.linkedin_refresh_token = None
        user.linkedin_user_urn = None
        self.db.commit()
    def is_user_connected(self, user):
        return bool(user.linkedin_access_token and user.linkedin_user_urn)
    # ============== TEXT-ONLY POST (unchanged) ==============
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
            raise LinkedInError(f"LinkedIn rejected: [{r.status_code}] {r.text}")
        post_urn = r.headers.get("x-restli-id") or r.json().get("id")
        if not post_urn:
            raise LinkedInError("Publish succeeded but no URN returned")
        return post_urn
    # ============== NEW PHASE 9.5: MEDIA UPLOAD + POST ==============
    def _register_upload(self, access_token, author_urn, recipe):
        """Step 1 of media upload: ask LinkedIn for an upload URL."""
        body = {
            "registerUploadRequest": {
                "recipes": [recipe],
                "owner": author_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }],
            }
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        try:
            r = requests.post(
                ASSETS_REGISTER_URL, json=body, headers=headers, timeout=30
            )
        except requests.RequestException as e:
            raise LinkedInError(f"Register upload failed: {e}")
        if not r.ok:
            raise LinkedInError(f"Register upload rejected: [{r.status_code}] {r.text}")
        data = r.json().get("value", {})
        try:
            upload_url = (
                data["uploadMechanism"]
                ["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]
                ["uploadUrl"]
            )
            asset_urn = data["asset"]
            return upload_url, asset_urn
        except KeyError as e:
            raise LinkedInError(f"Unexpected register-upload response shape: {e}")
    def _upload_binary(self, upload_url, access_token, file_path):
        """Step 2 of media upload: PUT the bytes to the URL we got."""
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except IOError as e:
            raise LinkedInError(f"Could not read file {file_path}: {e}")
        try:
            r = requests.put(
                upload_url, data=data,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=120,  # videos can be slow
            )
        except requests.RequestException as e:
            raise LinkedInError(f"Binary upload failed: {e}")
        if not r.ok and r.status_code not in (200, 201):
            raise LinkedInError(f"Binary upload rejected: [{r.status_code}] {r.text}")
        logger.info(f"Uploaded media bytes successfully ({len(data)} bytes)")
    def upload_media_asset(self, access_token, author_urn, file_path, kind):
        """
        Full upload flow: register + upload binary.
        kind: 'image' or 'video'.
        Returns the asset URN to use in publish_media_post.
        """
        recipe = RECIPE_IMAGE if kind == "image" else RECIPE_VIDEO
        upload_url, asset_urn = self._register_upload(access_token, author_urn, recipe)
        self._upload_binary(upload_url, access_token, file_path)
        logger.info(f"Media asset registered: {asset_urn}")
        return asset_urn
    def publish_media_post(
        self,
        access_token: str,
        author_urn: str,
        text: str,
        media_assets: List[Dict[str, str]],
    ) -> str:
        """
        Publish a post with media attachments.
        media_assets: [{"asset_urn": "urn:li:image:..", "kind": "image"|"video", "title": "..."}]
        """
        if not media_assets:
            return self.publish_text_post(access_token, author_urn, text)
        # All media must be same category for a single post
        kinds = {m["kind"] for m in media_assets}
        if len(kinds) > 1:
            raise LinkedInError("Cannot mix images and videos in one post")
        kind = kinds.pop()
        category = "IMAGE" if kind == "image" else "VIDEO"
        media_list = []
        for i, m in enumerate(media_assets):
            media_list.append({
                "status": "READY",
                "description": {"text": m.get("title", "")[:200] or ""},
                "media": m["asset_urn"],
                "title": {"text": m.get("title", "")[:200] or f"Media {i+1}"},
            })
        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": category,
                    "media": media_list,
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
            r = requests.post(UGC_POSTS_URL, json=body, headers=headers, timeout=60)
        except requests.RequestException as e:
            raise LinkedInError(f"Publish media request failed: {e}")
        if not r.ok:
            raise LinkedInError(f"LinkedIn rejected media post: [{r.status_code}] {r.text}")
        post_urn = r.headers.get("x-restli-id") or r.json().get("id")
        if not post_urn:
            raise LinkedInError("Publish succeeded but no URN returned")
        logger.info(f"Published media post: {post_urn}")
        return post_urn