import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "student_info.db"
COURSES = ("CSC131", "CSC132", "CSC230")


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
