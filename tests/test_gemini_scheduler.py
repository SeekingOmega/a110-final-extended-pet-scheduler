import json
import pytest
from unittest.mock import MagicMock, patch


def _make_scheduler(mock_client):
    from gemini_scheduler import GeminiScheduler
    calendar_reader = MagicMock(return_value=[
        {"title": "CS 101", "date": "2026-04-28", "start": "2026-04-28T08:00:00", "end": "2026-04-28T09:30:00"}
    ])
    task_lister = MagicMock(return_value={
        "owner": {"name": "Jordan", "active_hours_start": "07:00", "active_hours_end": "22:00"},
        "pets": [{"name": "Buddy", "tasks": [{"name": "Walk", "duration": 30, "priority": "high", "frequency": "daily"}]}],
        "week_start": "2026-04-28",
        "week_end": "2026-05-04",
    })
    with patch("google.genai.Client", return_value=mock_client):
        scheduler = GeminiScheduler(api_key="fake-key", calendar_reader=calendar_reader, task_lister=task_lister)
    return scheduler


MOCK_SCHEDULE = {
    "proposed_events": [
        {"task_name": "Walk", "pet_name": "Buddy", "day": "2026-04-28", "start_time": "07:00", "duration_min": 30, "priority": "high"}
    ],
    "unschedulable": [],
    "reasoning_summary": "Walk scheduled at 7am before class.",
}


def _build_mock_client():
    """Build a mock genai.Client whose chats.create returns a controlled chat."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_client.chats.create.return_value = mock_chat
    return mock_client, mock_chat


def test_generate_schedule_returns_proposed_events():
    mock_client, mock_chat = _build_mock_client()

    # First response: a function call to list_pet_tasks
    fc = MagicMock()
    fc.name = "list_pet_tasks"
    fc.args = {}
    resp1 = MagicMock()
    resp1.function_calls = [fc]

    # Second response: final text with JSON (no function calls)
    resp2 = MagicMock()
    resp2.function_calls = []
    resp2.text = json.dumps(MOCK_SCHEDULE)

    mock_chat.send_message.side_effect = [resp1, resp2]

    scheduler = _make_scheduler(mock_client)
    result = scheduler.generate_schedule()
    assert "proposed_events" in result
    assert result["proposed_events"][0]["task_name"] == "Walk"


def test_generate_schedule_logs_tool_steps():
    mock_client, mock_chat = _build_mock_client()

    fc = MagicMock()
    fc.name = "list_pet_tasks"
    fc.args = {}
    resp1 = MagicMock()
    resp1.function_calls = [fc]

    resp2 = MagicMock()
    resp2.function_calls = []
    resp2.text = json.dumps(MOCK_SCHEDULE)

    mock_chat.send_message.side_effect = [resp1, resp2]

    scheduler = _make_scheduler(mock_client)
    scheduler.generate_schedule()
    assert len(scheduler.steps) >= 1
    assert scheduler.steps[0]["tool"] == "list_pet_tasks"


def test_generate_schedule_logs_calendar_read_step():
    mock_client, mock_chat = _build_mock_client()

    # First call: read_calendar_events
    fc1 = MagicMock()
    fc1.name = "read_calendar_events"
    fc1.args = {"start_date": "2026-04-28", "end_date": "2026-05-04"}
    resp1 = MagicMock()
    resp1.function_calls = [fc1]

    # Second call: list_pet_tasks
    fc2 = MagicMock()
    fc2.name = "list_pet_tasks"
    fc2.args = {}
    resp2 = MagicMock()
    resp2.function_calls = [fc2]

    # Final: text response
    resp3 = MagicMock()
    resp3.function_calls = []
    resp3.text = json.dumps(MOCK_SCHEDULE)

    mock_chat.send_message.side_effect = [resp1, resp2, resp3]
    scheduler = _make_scheduler(mock_client)
    result = scheduler.generate_schedule()
    assert "proposed_events" in result
    assert any(s["tool"] == "read_calendar_events" for s in scheduler.steps)
    assert scheduler.steps[0].get("result_count") is not None


def test_reschedule_rejected_returns_proposed_events():
    mock_client, mock_chat = _build_mock_client()

    resp1 = MagicMock()
    resp1.function_calls = []
    resp1.text = json.dumps(MOCK_SCHEDULE)

    mock_chat.send_message.return_value = resp1
    scheduler = _make_scheduler(mock_client)

    rejected = [{"task_name": "Walk", "pet_name": "Buddy", "day": "2026-04-28", "start_time": "07:00", "duration_min": 30, "priority": "high"}]
    confirmed = []
    result = scheduler.reschedule_rejected(rejected=rejected, confirmed=confirmed)
    assert "proposed_events" in result
    assert scheduler.steps == []  # no tool calls in this mock


def test_unknown_tool_raises():
    mock_client, _ = _build_mock_client()
    scheduler = _make_scheduler(mock_client)
    with pytest.raises(ValueError, match="Unknown tool"):
        scheduler._execute_tool("nonexistent_tool", {})
