"""Google Calendar API read/write wrapper."""
from datetime import date, datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build
from calendar_auth import get_credentials

PAWPAL_CALENDAR_NAME = "Pawpal petcare scheduler"


def get_service():
    return build("calendar", "v3", credentials=get_credentials())


@lru_cache(maxsize=1)
def get_user_timezone() -> str:
    """Return the timezone string of the user's primary Google Calendar."""
    cal = get_service().calendars().get(calendarId="primary").execute()
    return cal.get("timeZone", "UTC")


def read_events(start_date: date, end_date: date) -> list[dict]:
    """Return all events in [start_date, end_date] from the primary calendar."""
    tz = ZoneInfo(get_user_timezone())
    service = get_service()
    time_min = datetime.combine(start_date, datetime.min.time(), tzinfo=tz).isoformat()
    time_max = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=tz).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    events = []
    for item in result.get("items", []):
        start_obj = item.get("start", {})
        end_obj   = item.get("end",   {})
        start = start_obj.get("dateTime", start_obj.get("date", ""))
        end   = end_obj.get("dateTime",   end_obj.get("date",   ""))
        events.append({
            "title": item.get("summary", "(no title)"),
            "start": start,
            "end":   end,
            "date":  start[:10],
        })
    return events


def get_or_create_pawpal_calendar_id() -> str:
    """Find the PawPal calendar by name, creating it if it doesn't exist."""
    service = get_service()
    for cal in service.calendarList().list().execute().get("items", []):
        if cal.get("summary") == PAWPAL_CALENDAR_NAME:
            return cal["id"]
    new_cal = service.calendars().insert(body={
        "summary": PAWPAL_CALENDAR_NAME,
        "timeZone": get_user_timezone(),
    }).execute()
    return new_cal["id"]


def create_event(
    title: str,
    day: str,
    start_time: str,
    duration_min: int,
    description: str = "",
    calendar_id: str | None = None,
) -> dict:
    """Create a calendar event. day: YYYY-MM-DD, start_time: HH:MM."""
    service = get_service()
    if calendar_id is None:
        calendar_id = get_or_create_pawpal_calendar_id()
    tz_name = get_user_timezone()
    start_dt = datetime.fromisoformat(f"{day}T{start_time}:00")
    end_dt   = start_dt + timedelta(minutes=duration_min)
    body = {
        "summary":     title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": tz_name},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": tz_name},
    }
    return service.events().insert(calendarId=calendar_id, body=body).execute()
