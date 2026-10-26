import argparse
from database import initialize_database, connect, COURSES

parser = argparse.ArgumentParser(description="Enroll an existing registered student")
parser.add_argument("student_id")
parser.add_argument("course", choices=COURSES)
args = parser.parse_args()
initialize_database()
with connect() as conn:
    if conn.execute("SELECT 1 FROM students WHERE student_id = ?", (args.student_id,)).fetchone() is None:
        raise SystemExit("Student not found. Register the student first.")
    conn.execute("INSERT OR IGNORE INTO enrollments(student_id, course) VALUES (?, ?)", (args.student_id, args.course))
print("Enrollment saved.")
