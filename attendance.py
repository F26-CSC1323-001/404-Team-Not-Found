from datetime import datetime
import sqlite3
from database import connect, initialize_database, COURSES
from schedule import attendance_status


def mark_attendance(student_id, course, when=None):
    if course not in COURSES:
        return "invalid_course"
    initialize_database()
    when = when or datetime.now()
    status = attendance_status(course, when)
    if status in ("Before class", "Closed", "No class"):
        return "outside_window"
    # Unscheduled courses retain their previous behavior until configured.
    scheduled = status != "Unscheduled"
    if not scheduled:
        status = "Present"
    with connect() as connection:
        student = connection.execute("SELECT name FROM students WHERE student_id = ?", (str(student_id),)).fetchone()
        if student is None:
            return "not_found"
        # Enrollment is required for CSC130 so that absent students can be identified.
        if scheduled:
            enrolled = connection.execute("SELECT 1 FROM enrollments WHERE student_id = ? AND course = ?", (str(student_id), course)).fetchone()
            if not enrolled:
                return "not_enrolled"
        try:
            connection.execute("""INSERT INTO attendance (student_id, course, date, time, status)
                VALUES (?, ?, ?, ?, ?)""", (str(student_id), course, when.strftime("%Y-%m-%d"), when.strftime("%H:%M:%S"), status))
        except sqlite3.IntegrityError:
            return "duplicate"
    return "recorded" if status == "Present" else "late"


if __name__ == "__main__":
    print("Import mark_attendance(student_id, course) from this module.")
