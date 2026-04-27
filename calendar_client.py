"""Google Calendar API read/write wrapper."""
from datetime import date, datetime, timedelta
from googleapiclient.discovery import build
from calendar_auth import get_credentials

TIMEZONE = "America/Los_Angeles"


def get_service():
    """Build and return an authenticated Google Calendar API service client."""
    return build("calendar", "v3", credentials=get_credentials())


def read_events(start_date: date, end_date: date) -> list[dict]:
    """Return all events in [start_date, end_date] from the primary calendar."""
    service = get_service()
    time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
    time_max = datetime.combine(end_date, datetime.max.time().replace(microsecond=0)).isoformat() + "Z"
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


def create_event(title: str, day: str, start_time: str, duration_min: int, description: str = "") -> dict:
    """Create a calendar event. day: YYYY-MM-DD, start_time: HH:MM."""
    service = get_service()
    start_dt = datetime.fromisoformat(f"{day}T{start_time}:00")
    end_dt   = start_dt + timedelta(minutes=duration_min)
    body = {
        "summary":     title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": TIMEZONE},
    }
    return service.events().insert(calendarId="primary", body=body).execute()
