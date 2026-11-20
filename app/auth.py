import hmac
import hashlib
import json
import base64
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from .config import settings
from .database import get_user_by_id

SESSION_COOKIE_NAME = "strix_session"

def hash_password(password: str) -> str:
    """Hash password with secure salt using SHA256."""
    salt = "strix_salt_protect_2026_"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return hash_password(plain_password) == hashed_password

def sign_session_data(data: Dict[str, Any]) -> str:
    """Create a tamper-proof cryptographically signed session token."""
    raw_json = json.dumps(data)
    payload = base64.urlsafe_b64encode(raw_json.encode()).decode()
    signature = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def verify_session_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Verify session token signature and decode user payload."""
    if not token or "." not in token:
        return None
    try:
        payload, signature = token.rsplit(".", 1)
        expected = hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        decoded = base64.urlsafe_b64decode(payload.encode()).decode()
        return json.loads(decoded)
    except Exception:
        return None

def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Return user dict if authenticated, else None."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    payload = verify_session_token(token)
    if not payload or "user_id" not in payload:
        return None
    user = get_user_by_id(payload["user_id"])
    return user

def get_current_user(request: Request) -> Dict[str, Any]:
    """Require user authentication, or redirect to login."""
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user

def get_current_admin(request: Request) -> Dict[str, Any]:
    """Require admin authentication."""
    user = get_current_user_optional(request)
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator privileges required")
    return user
