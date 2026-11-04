import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "student_info.db"
COURSES = ("CSC130", "CSC131", "CSC132", "CSC230")


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with connect() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            course TEXT
        )""")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(attendance)")}
        if "course" not in columns:
            connection.execute("ALTER TABLE attendance ADD COLUMN course TEXT")
        if "status" not in columns:
            connection.execute("ALTER TABLE attendance ADD COLUMN status TEXT")
        connection.execute("""CREATE TABLE IF NOT EXISTS enrollments (
            student_id TEXT NOT NULL,
            course TEXT NOT NULL,
            PRIMARY KEY(student_id, course),
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS class_sessions (
            course TEXT NOT NULL,
            date TEXT NOT NULL,
            PRIMARY KEY(course, date)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS course_schedules (
            course TEXT PRIMARY KEY,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            grace_minutes INTEGER NOT NULL,
            meeting_days TEXT NOT NULL DEFAULT '0,1,2,3,4'
        )""")
        connection.execute("""INSERT OR IGNORE INTO course_schedules
            (course, start_time, end_time, grace_minutes, meeting_days)
            VALUES ('CSC130', '08:00', '09:00', 15, '0,1,2,3,4')""")
        connection.execute("""CREATE UNIQUE INDEX IF NOT EXISTS attendance_per_course_day
            ON attendance(student_id, course, date)
            WHERE course IS NOT NULL""")


def get_student_name(student_id):
    with connect() as connection:
        row = connection.execute("SELECT name FROM students WHERE student_id = ?", (str(student_id),)).fetchone()
    return row[0] if row else None


if __name__ == "__main__":
    initialize_database()
    print("Database ready. Existing attendance records preserved.")
