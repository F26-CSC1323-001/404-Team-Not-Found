from datetime import datetime, time, timedelta
from database import connect, initialize_database


def get_schedule(course):
    initialize_database()
    with connect() as conn:
        row = conn.execute("SELECT start_time, end_time, grace_minutes, meeting_days FROM course_schedules WHERE course = ?", (course,)).fetchone()
    if not row:
        return None
    return {"start": row[0], "end": row[1], "grace_minutes": row[2], "meeting_days": row[3]}


def attendance_status(course, when=None):
    config = get_schedule(course)
    if config is None:
        return "Unscheduled"
    when = when or datetime.now()
    if str(when.weekday()) not in config["meeting_days"].split(","):
        return "No class"
    start = datetime.combine(when.date(), time.fromisoformat(config["start"]))
    end = datetime.combine(when.date(), time.fromisoformat(config["end"]))
    if when < start:
        return "Before class"
    if when <= start + timedelta(minutes=config["grace_minutes"]):
        return "Present"
    if when < end:
        return "Late"
    return "Closed"
