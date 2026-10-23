from datetime import datetime
import sqlite3
from database import connect, initialize_database, COURSES


def mark_attendance(student_id, course):
    if course not in COURSES:
        return "invalid_course"
    initialize_database()
    with connect() as connection:
        student = connection.execute("SELECT name FROM students WHERE student_id = ?", (str(student_id),)).fetchone()
        if student is None:
            return "not_found"
        now = datetime.now()
        try:
            connection.execute("""INSERT INTO attendance (student_id, course, date, time)
                VALUES (?, ?, ?, ?)""", (str(student_id), course, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
        except sqlite3.IntegrityError:
            return "duplicate"
    return "recorded"


if __name__ == "__main__":
    print("Import mark_attendance(student_id, course) from this module.")
