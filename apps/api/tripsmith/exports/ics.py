from __future__ import annotations

import datetime as dt

from tripsmith.schemas.itinerary import ItineraryJson


def to_ics(*, trip_id: str, itinerary: ItineraryJson) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    lines: list[str] = []
    lines.append("BEGIN:VCALENDAR\r\n")
    lines.append("VERSION:2.0\r\n")
    lines.append("PRODID:-//TripSmith//EN\r\n")
    for day in itinerary.days:
        base = dt.datetime.combine(day.date, dt.time(9, 0), tzinfo=dt.timezone.utc)
        offsets = {"morning": 0, "afternoon": 4, "evening": 8}
        for item in day.items:
            start = base + dt.timedelta(hours=offsets[item.period])
            end = start + dt.timedelta(minutes=item.stay_minutes)
            uid = f"{trip_id}-{day.date.isoformat()}-{item.period}@tripsmith"
            lines.append("BEGIN:VEVENT\r\n")
            lines.append(f"UID:{uid}\r\n")
            lines.append(f"DTSTAMP:{now.strftime('%Y%m%dT%H%M%SZ')}\r\n")
            lines.append(f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}\r\n")
            lines.append(f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}\r\n")
            lines.append(f"SUMMARY:{_escape(item.poi_name)}\r\n")
            lines.append(f"DESCRIPTION:{_escape(item.weather_summary)}\r\n")
            lines.append("END:VEVENT\r\n")
    lines.append("END:VCALENDAR\r\n")
    return "".join(lines)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

