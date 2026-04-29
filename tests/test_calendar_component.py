from datetime import date
from calendar_component import generate_calendar_html, render_unschedulable_html


def test_existing_event_title_in_html():
    html = generate_calendar_html(
        week_start=date(2026, 4, 28),
        existing_events=[{
            "title": "CS 101", "date": "2026-04-28",
            "start": "2026-04-28T08:00:00", "end": "2026-04-28T09:30:00"
        }],
        proposed_events=[],
        active_start="07:00",
        active_end="22:00",
    )
    assert "CS 101" in html


def test_proposed_event_title_in_html():
    html = generate_calendar_html(
        week_start=date(2026, 4, 28),
        existing_events=[],
        proposed_events=[{
            "task_name": "Morning Walk", "pet_name": "Buddy",
            "day": "2026-04-28", "start_time": "07:00", "duration_min": 30, "priority": "high"
        }],
        active_start="07:00",
        active_end="22:00",
    )
    assert "Morning Walk" in html
    assert "Buddy" in html


def test_html_contains_all_seven_day_headers():
    html = generate_calendar_html(
        week_start=date(2026, 4, 28),
        existing_events=[],
        proposed_events=[],
        active_start="07:00",
        active_end="22:00",
    )
    for label in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        assert label in html


def test_event_outside_active_hours_not_rendered():
    html = generate_calendar_html(
        week_start=date(2026, 4, 28),
        existing_events=[{
            "title": "Late Night Meeting", "date": "2026-04-28",
            "start": "2026-04-28T23:00:00", "end": "2026-04-28T23:30:00"
        }],
        proposed_events=[],
        active_start="07:00",
        active_end="22:00",
    )
    assert "Late Night Meeting" not in html


def test_multi_hour_event_appears_in_each_spanned_row():
    html = generate_calendar_html(
        week_start=date(2026, 4, 28),
        existing_events=[{
            "title": "Lecture", "date": "2026-04-28",
            "start": "2026-04-28T08:00:00", "end": "2026-04-28T10:30:00"
        }],
        proposed_events=[],
        active_start="07:00",
        active_end="22:00",
    )
    # Title row (08:00) and two continuation rows (09:00, 10:00) must all be present
    assert html.count("Lecture") == 1                  # title shown once
    assert html.count('class="ex-cont"') == 2          # continuation blocks for 09:00 and 10:00


def test_render_unschedulable_html_empty_returns_empty_string():
    html = render_unschedulable_html([])
    assert html == ""


def test_render_unschedulable_html_contains_task_and_reason():
    html = render_unschedulable_html([{
        "task_name": "Walk",
        "pet_name": "Buddy",
        "day": "2026-04-28",
        "reason": "No 30-min gap within active hours",
    }])
    assert "Walk" in html
    assert "Buddy" in html
    assert "No 30-min gap within active hours" in html
