"""Google OAuth2 flow and credential management."""
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = Path("token.json")
CREDS_PATH = Path("credentials.json")


def get_credentials() -> Credentials:
    """Return valid credentials, running the OAuth flow if needed."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                raise FileNotFoundError(
                    f"Google OAuth credentials file not found at '{CREDS_PATH}'. "
                    "Download it from Google Cloud Console and save it as credentials.json."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
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


def revoke_credentials() -> None:
    """Delete the stored token so the user must re-authenticate."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
