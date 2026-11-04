import sqlite3
from pathlib import Path

# Find the existing database
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "student_info.db"

if not DB_PATH.is_file():
    print("Database not found!")
else:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Check the existing attendance columns
    cursor.execute("PRAGMA table_info(attendance)")
    columns = [column[1] for column in cursor.fetchall()]

    # Add the course column only if missing
    if "course" not in columns:
        cursor.execute(
            "ALTER TABLE attendance ADD COLUMN course TEXT"
        )
        connection.commit()
        print("Course column added successfully!")
    else:
        print("Course column already exists!")

    connection.close()
