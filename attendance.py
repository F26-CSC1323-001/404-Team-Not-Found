from datetime import datetime
import sqlite3


# This function will record attendance for a registered student.
def mark_attendance(student_id, course):

    connection = sqlite3.connect("student_info.db")
    cur = connection.cursor()

    # Check whether student exists
    cur.execute("""
        SELECT name FROM students
        WHERE student_id = ?
    """, (student_id,))

    student = cur.fetchone()

    if student is None:
        print("Student not found!")
        connection.close()
        return "not found"

    
    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    # Check whether attendance is already recorded today
    cur.execute("""
        SELECT id FROM attendance
        WHERE student_id = ? AND date = ? AND course = ?
    """, (student_id, date, course))

    existing_record = cur.fetchone()

    if existing_record is not None:
        print("Attendance already recorded today!")
        connection.close()
        return "duplicate"

    # Insert attendance record
    cur.execute("""
        INSERT INTO attendance (student_id, course, date, time)
        VALUES (?, ?, ?, ?)
    """, (student_id, course, date, time))

    connection.commit()
    connection.close()

    print(f"Attendance recorded for {student[0]} at {time}")
    return "recorded"


if __name__ == "__main__":
    result = mark_attendance("20008273", "CSC131")
    print("Result:", result)