"""LinkedIn OAuth flow endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.services.linkedin_service import LinkedInService, LinkedInError
from app.api.deps import get_current_user
from app.schemas.auth import LinkedInAuthURLResponse, LinkedInConnectionStatus
from app.utils.logger import logger
router = APIRouter(prefix="/api/auth", tags=["auth"])
@router.get("/linkedin/status", response_model=LinkedInConnectionStatus)
def linkedin_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    linkedin = LinkedInService(db=db)
    connected = linkedin.is_user_connected(user)
    return LinkedInConnectionStatus(
        connected=connected,
        linkedin_user_urn=user.linkedin_user_urn,
        expires_in_message=(
            "Tokens last ~60 days. Reconnect when posting fails."
            if connected else None
        ),
    )
@router.get("/linkedin/start", response_model=LinkedInAuthURLResponse)
def linkedin_start(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    linkedin = LinkedInService(db=db)
    if not linkedin.is_configured():
        raise HTTPException(
            status_code=500,
            detail="LinkedIn API not configured. Set LINKEDIN_CLIENT_ID, "
                   "LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI in .env.",
        )
    try:
        return LinkedInAuthURLResponse(**linkedin.build_auth_url())
    except LinkedInError as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/linkedin/callback")
def linkedin_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    error_description: str = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if error:
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;text-align:center;padding:50px;'>"
            f"<h1>Authorization Failed</h1><p>{error}: {error_description}</p>"
            f"<p><a href='/'>Go home</a></p></body></html>",
            status_code=400,
        )
    linkedin = LinkedInService(db=db)
    try:
        token_data = linkedin.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        user_urn = linkedin.fetch_user_urn(access_token)
        linkedin.store_tokens(user, access_token, refresh_token, user_urn)
    except LinkedInError as e:
        return HTMLResponse(
            f"<html><body style='font-family:sans-serif;text-align:center;padding:50px;'>"
            f"<h1>Connection Failed</h1><p>{e}</p></body></html>",
            status_code=500,
        )
    return HTMLResponse(
        f"<html><body style='font-family:sans-serif;text-align:center;padding:50px;'>"
        f"<h1>LinkedIn Connected!</h1>"
        f"<p>You can close this tab and go back to the app.</p>"
        f"<p style='color:#666;font-size:14px;'>URN: <code>{user_urn}</code></p>"
        f"<p><a href='http://localhost:8501'>Back to LinkedIn AI Agent</a></p>"
        f"</body></html>"
    )
@router.post("/linkedin/disconnect")
def linkedin_disconnect(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    linkedin = LinkedInService(db=db)
    linkedin.disconnect(user)
    return {"detail": "LinkedIn disconnected. Future posts will use manual mode."}