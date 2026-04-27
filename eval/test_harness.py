"""
PawPal+ Scheduler Test Harness
Validates scheduling rules against mock data without real API calls.
Run: python eval/test_harness.py
"""
from datetime import date

# ── Mock data ─────────────────────────────────────────────────────────────────
ACTIVE_START = "07:00"
ACTIVE_END   = "22:00"
WEEK_START   = "2026-04-28"
WEEK_END     = "2026-05-04"

MOCK_EXISTING = [
    {"title": "CS 101",   "date": "2026-04-28", "start": "2026-04-28T08:00:00", "end": "2026-04-28T09:30:00"},
    {"title": "Math 201", "date": "2026-04-28", "start": "2026-04-28T11:00:00", "end": "2026-04-28T12:00:00"},
    {"title": "CS 101",   "date": "2026-04-30", "start": "2026-04-30T08:00:00", "end": "2026-04-30T09:30:00"},
]

MOCK_SCHEDULE = {
    "proposed_events": [
        {"task_name": "Morning Walk", "pet_name": "Buddy", "day": "2026-04-28", "start_time": "07:00", "duration_min": 30, "priority": "high"},
        {"task_name": "Morning Walk", "pet_name": "Buddy", "day": "2026-04-29", "start_time": "07:00", "duration_min": 30, "priority": "high"},
        {"task_name": "Morning Walk", "pet_name": "Buddy", "day": "2026-04-30", "start_time": "07:00", "duration_min": 30, "priority": "high"},
        {"task_name": "Feeding",      "pet_name": "Mochi", "day": "2026-04-28", "start_time": "07:30", "duration_min": 5,  "priority": "high"},
        {"task_name": "Feeding",      "pet_name": "Mochi", "day": "2026-04-29", "start_time": "07:30", "duration_min": 5,  "priority": "high"},
        {"task_name": "Grooming",     "pet_name": "Buddy", "day": "2026-04-30", "start_time": "14:00", "duration_min": 45, "priority": "low"},
    ],
    "unschedulable": [
        {"task_name": "Morning Walk", "pet_name": "Buddy", "day": "2026-05-04", "reason": "No 30-min gap within active hours after existing events"},
    ],
    "reasoning_summary": "Scheduled daily walks at 7am. Grooming on Wednesday afternoon.",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _overlaps(ev_day, ev_start, ev_dur, existing):
    """Return True if a proposed event overlaps any existing event on the same day."""
    from datetime import datetime, timedelta
    ev_s = datetime.fromisoformat(f"{ev_day}T{ev_start}:00")
    ev_e = ev_s + timedelta(minutes=ev_dur)
    for ex in existing:
        if ex["date"] != ev_day:
            continue
        ex_s = datetime.fromisoformat(ex["start"])
        ex_e = datetime.fromisoformat(ex["end"])
        if ev_s < ex_e and ev_e > ex_s:
            return True
    return False


# ── Test functions ────────────────────────────────────────────────────────────
def test_daily_tasks_not_on_wrong_day(schedule, tasks):
    from datetime import date, timedelta
    week_days = {(date.fromisoformat(WEEK_START) + timedelta(days=i)).isoformat() for i in range(7)}
    daily_task_names = {
        t["name"] for pet in tasks["pets"] for t in pet["tasks"] if t["frequency"] == "daily"
    }
    for ev in schedule["proposed_events"]:
        if ev["task_name"] in daily_task_names:
            assert ev["day"] in week_days, (
                f"Daily task '{ev['task_name']}' placed on {ev['day']} which is outside the week"
            )
    return True, "Daily tasks not carried over to wrong day"


def test_no_task_in_both_lists(schedule):
    proposed_keys = {(e["task_name"], e["pet_name"], e["day"]) for e in schedule["proposed_events"]}
    unsch_keys    = {(e["task_name"], e["pet_name"], e["day"]) for e in schedule["unschedulable"]}
    overlap = proposed_keys & unsch_keys
    assert not overlap, f"Tasks in both lists: {overlap}"
    return True, "No task appears in both proposed and unschedulable"


def test_all_events_within_active_hours(schedule):
    from datetime import datetime, timedelta
    a_start = datetime.strptime(ACTIVE_START, "%H:%M").time()
    a_end   = datetime.strptime(ACTIVE_END,   "%H:%M").time()
    for ev in schedule["proposed_events"]:
        start_t = datetime.strptime(ev["start_time"], "%H:%M").time()
        end_dt  = datetime.strptime(ev["start_time"], "%H:%M") + timedelta(minutes=ev["duration_min"])
        end_t   = end_dt.time()
        assert start_t >= a_start, f"{ev['task_name']} starts before active hours"
        assert end_t   <= a_end,   f"{ev['task_name']} ends after active hours"
    return True, "All events within active hours"


def test_no_overlap_with_existing_events(schedule, existing):
    for ev in schedule["proposed_events"]:
        assert not _overlaps(ev["day"], ev["start_time"], ev["duration_min"], existing), (
            f"{ev['task_name']} on {ev['day']} at {ev['start_time']} overlaps an existing event"
        )
    return True, "No proposed event overlaps existing calendar events"


def test_unschedulable_tasks_have_reasons(schedule):
    for item in schedule["unschedulable"]:
        assert item.get("reason"), f"Missing reason for unschedulable task: {item}"
    return True, "All unschedulable tasks have a reason"


# ── Runner ────────────────────────────────────────────────────────────────────
def run_harness():
    tasks_context = {
        "owner": {"name": "Jordan", "active_hours_start": ACTIVE_START, "active_hours_end": ACTIVE_END},
        "pets": [
            {"name": "Buddy", "tasks": [
                {"name": "Morning Walk", "duration": 30, "priority": "high", "frequency": "daily"},
                {"name": "Grooming",     "duration": 45, "priority": "low",  "frequency": "weekly"},
            ]},
            {"name": "Mochi", "tasks": [
                {"name": "Feeding", "duration": 5, "priority": "high", "frequency": "daily"},
            ]},
        ],
        "week_start": WEEK_START,
        "week_end":   WEEK_END,
    }

    tests = [
        lambda: test_daily_tasks_not_on_wrong_day(MOCK_SCHEDULE, tasks_context),
        lambda: test_no_task_in_both_lists(MOCK_SCHEDULE),
        lambda: test_all_events_within_active_hours(MOCK_SCHEDULE),
        lambda: test_no_overlap_with_existing_events(MOCK_SCHEDULE, MOCK_EXISTING),
        lambda: test_unschedulable_tasks_have_reasons(MOCK_SCHEDULE),
    ]

    print("\nPawPal+ Scheduler Test Harness")
    print("=" * 40)
    passed = 0
    for fn in tests:
        try:
            _, label = fn()
            print(f"[PASS] {label}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {e}")
    print("=" * 40)
    print(f"{passed}/{len(tests)} tests passed")
    return passed == len(tests)


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_harness() else 1)
