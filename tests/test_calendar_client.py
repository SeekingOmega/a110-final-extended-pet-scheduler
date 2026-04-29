from unittest.mock import patch, MagicMock
from datetime import date


def _mock_service(events):
    """Build a mock Google API service that returns the given events list."""
    mock_service = MagicMock()
    mock_service.events.return_value.list.return_value.execute.return_value = {
        "items": events
    }
    mock_service.events.return_value.insert.return_value.execute.return_value = {
        "id": "abc123", "summary": "Test Event"
    }
    return mock_service


def test_read_events_returns_parsed_list():
    raw = [
        {
            "summary": "CS 101",
            "start": {"dateTime": "2026-04-28T08:00:00"},
            "end":   {"dateTime": "2026-04-28T09:30:00"},
        }
    ]
    with patch("calendar_client.get_service", return_value=_mock_service(raw)), \
         patch("calendar_client.get_user_timezone", return_value="America/New_York"):
        from calendar_client import read_events
        result = read_events(date(2026, 4, 28), date(2026, 5, 4))
    assert len(result) == 1
    assert result[0]["title"] == "CS 101"
    assert result[0]["date"] == "2026-04-28"


def test_read_events_returns_empty_list_when_no_items():
    with patch("calendar_client.get_service", return_value=_mock_service([])), \
         patch("calendar_client.get_user_timezone", return_value="America/New_York"):
        from calendar_client import read_events
        result = read_events(date(2026, 4, 28), date(2026, 5, 4))
    assert result == []


def test_create_event_calls_insert_with_correct_summary():
    mock_svc = _mock_service([])
    with patch("calendar_client.get_service", return_value=mock_svc):
        from calendar_client import create_event
        create_event("Buddy Walk", "2026-04-28", "07:00", 30)
    call_kwargs = mock_svc.events.return_value.insert.call_args.kwargs
    assert call_kwargs["body"]["summary"] == "Buddy Walk"


def test_create_event_end_time_is_duration_after_start():
    mock_svc = _mock_service([])
    with patch("calendar_client.get_service", return_value=mock_svc):
        from calendar_client import create_event
        create_event("Buddy Walk", "2026-04-28", "07:00", 30)
    body = mock_svc.events.return_value.insert.call_args.kwargs["body"]
    assert "07:30" in body["end"]["dateTime"]


def test_read_events_handles_all_day_events():
    raw = [{"summary": "Vet Appointment", "start": {"date": "2026-04-29"}, "end": {"date": "2026-04-29"}}]
    with patch("calendar_client.get_service", return_value=_mock_service(raw)), \
         patch("calendar_client.get_user_timezone", return_value="America/New_York"):
        from calendar_client import read_events
        result = read_events(date(2026, 4, 28), date(2026, 5, 4))
    assert result[0]["date"] == "2026-04-29"
    assert result[0]["title"] == "Vet Appointment"
