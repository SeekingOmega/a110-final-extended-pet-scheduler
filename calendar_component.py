"""Generate the weekly calendar HTML for st.components.v1.html()."""
from datetime import date, timedelta
from html import escape

DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _hour(dt_str: str) -> int:
    """Extract hour integer from an ISO datetime string like '2026-04-28T08:30:00'."""
    try:
        return int(dt_str[11:13])
    except (IndexError, ValueError):
        return -1


def generate_calendar_html(
    week_start: date,
    existing_events: list[dict],
    proposed_events: list[dict],
    active_start: str,
    active_end: str,
) -> str:
    """Return an HTML string rendering a weekly calendar grid."""
    try:
        start_hour = int(active_start.split(":")[0])
        end_hour   = int(active_end.split(":")[0])
    except (ValueError, IndexError, AttributeError) as e:
        raise ValueError(f"Invalid active hours format (expected HH:MM): {e}") from e
    # Treat midnight (0) as end-of-day (23) so the range is never empty
    if end_hour == 0:
        end_hour = 23
    days = [week_start + timedelta(days=i) for i in range(7)]

    # Build global index lookup: (day, task_name, pet_name) → index in proposed_events
    ev_index: dict[tuple, int] = {}
    for i, ev in enumerate(proposed_events):
        ev_index[(ev["day"], ev["task_name"], ev["pet_name"])] = i

    existing_by_day: dict[str, list[dict]] = {}
    for ev in existing_events:
        h = _hour(ev.get("start", ""))
        if h < start_hour or h > end_hour:
            continue
        existing_by_day.setdefault(ev["date"], []).append(ev)

    proposed_by_day: dict[str, list[dict]] = {}
    for ev in proposed_events:
        proposed_by_day.setdefault(ev["day"], []).append(ev)

    rows = ""
    for hour in range(start_hour, end_hour + 1):
        cells = f'<td class="tl">{hour:02d}:00</td>'
        for day in days:
            day_str = day.isoformat()
            cell_content = ""
            for ev in existing_by_day.get(day_str, []):
                if _hour(ev.get("start", "")) == hour:
                    cell_content += f'<div class="ex">{escape(ev["title"])}</div>'
            for ev in proposed_by_day.get(day_str, []):
                try:
                    ev_hour = int(ev.get("start_time", "").split(":")[0])
                except (ValueError, IndexError):
                    ev_hour = -1
                if ev_hour == hour:
                    idx = ev_index.get((day_str, ev["task_name"], ev["pet_name"]), -1)
                    cell_content += (
                        f'<div class="pr" onclick="scrollToEvent({idx})" '
                        f'title="Click to highlight in approve list">'
                        f'🐾 {escape(ev["task_name"])}<br>'
                        f'<small>{escape(ev["pet_name"])} · {ev["duration_min"]}m</small>'
                        f'</div>'
                    )
            cells += f"<td>{cell_content}</td>"
        rows += f"<tr>{cells}</tr>"

    headers = "".join(
        f'<th>{DAY_ABBR[i]}<br><small>{(week_start + timedelta(days=i)).strftime("%m/%d")}</small></th>'
        for i in range(7)
    )

    return f"""
<style>
  body{{font-family:sans-serif;font-size:12px;background:#1e1e2e;color:#cdd6f4;margin:0;padding:8px}}
  table{{border-collapse:collapse;width:100%}}
  th{{background:#313244;padding:6px;text-align:center;border-bottom:2px solid #45475a}}
  td{{border:1px solid #313244;padding:3px;vertical-align:top;min-height:36px;background:#1e1e2e}}
  .tl{{background:#181825;color:#6c7086;text-align:right;font-size:11px;white-space:nowrap;width:44px}}
  .ex{{background:#313244;color:#6c7086;border-left:3px solid #585b70;border-radius:4px;
       padding:2px 4px;margin:1px;opacity:0.7;font-size:11px}}
  .pr{{background:#1e3a5f;color:#89dceb;border-left:3px solid #89b4fa;border-radius:4px;
       padding:2px 4px;margin:1px;font-size:11px;cursor:pointer}}
  .pr:hover{{background:#2a4f7a;border-left-color:#cba6f7}}
</style>
<script>
function scrollToEvent(idx) {{
  try {{
    var el = window.parent.document.getElementById('pawpal-ev-' + idx);
    if (el) {{
      el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
      el.style.transition = 'box-shadow 0.2s';
      el.style.boxShadow = '0 0 0 3px #89b4fa';
      setTimeout(function() {{ el.style.boxShadow = ''; }}, 1800);
    }}
  }} catch(e) {{}}
}}
</script>
<table>
  <thead><tr><th></th>{headers}</tr></thead>
  <tbody>{rows}</tbody>
</table>
"""


def render_unschedulable_html(unschedulable: list[dict]) -> str:
    """Return an HTML list of tasks that could not be scheduled."""
    if not unschedulable:
        return ""
    items = "".join(
        f'<li><strong>{escape(u["task_name"])}</strong> ({escape(u["pet_name"])}) on {escape(u["day"])}: {escape(u["reason"])}</li>'
        for u in unschedulable
    )
    return f"""
<style>
  body{{font-family:sans-serif;font-size:12px;background:#1e1e2e;color:#f38ba8;margin:0;padding:8px}}
  ul{{margin:0;padding-left:18px;line-height:2}}
</style>
<p><strong>⚠ Could not schedule:</strong></p><ul>{items}</ul>
"""
