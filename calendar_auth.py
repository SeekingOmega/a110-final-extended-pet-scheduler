"""Google OAuth2 flow and credential management."""
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = Path("token.json")


def _build_client_config() -> dict:
    """Build OAuth client config from env vars or fall back to credentials.json."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        return {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
    creds_path = Path("credentials.json")
    if creds_path.exists():
        import json
        return json.loads(creds_path.read_text())
    raise EnvironmentError(
        "Google OAuth credentials not configured. "
        "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
    )


def get_credentials() -> Credentials:
    """Return valid credentials, running the OAuth flow if needed."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(_build_client_config(), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(str(creds.to_json()))
    return creds


def is_authenticated() -> bool:
    """Return True if a usable token already exists."""
    if not TOKEN_PATH.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        return creds.valid or (creds.expired and bool(creds.refresh_token))
    except Exception:
        return False


def is_configured() -> bool:
    """Return True if OAuth credentials are available (env vars or credentials.json)."""
    if os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"):
        return True
    return Path("credentials.json").exists()


def revoke_credentials() -> None:
    """Delete the stored token so the user must re-authenticate."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
