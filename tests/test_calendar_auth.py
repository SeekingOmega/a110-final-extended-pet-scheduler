from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path


def test_is_authenticated_returns_false_when_no_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from calendar_auth import is_authenticated
    assert is_authenticated() is False


def test_is_authenticated_returns_true_with_valid_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.refresh_token = None
    with patch("calendar_auth.Credentials.from_authorized_user_file", return_value=mock_creds):
        (tmp_path / "token.json").write_text("{}")
        from calendar_auth import is_authenticated
        assert is_authenticated() is True


def test_get_credentials_refreshes_expired_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "some-token"
    (tmp_path / "token.json").write_text("{}")
    with patch("calendar_auth.Credentials.from_authorized_user_file", return_value=mock_creds), \
         patch("calendar_auth.Request") as mock_request:
        from calendar_auth import get_credentials
        result = get_credentials()
        mock_creds.refresh.assert_called_once_with(mock_request())
        assert result is mock_creds


def test_revoke_credentials_removes_token_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    token = tmp_path / "token.json"
    token.write_text("{}")
    from calendar_auth import revoke_credentials
    revoke_credentials()
    assert not token.exists()
