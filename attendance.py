from datetime import datetime
import sqlite3


# This function will record attendance for a registered student.
def mark_attendance(student_id):

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
        return

    
    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    # Check whether attendance is already recorded today
    cur.execute("""
        SELECT id FROM attendance
        WHERE student_id = ? AND date = ?
    """, (student_id, date))

    existing_record = cur.fetchone()

    if existing_record is not None:
        print("Attendance already recorded today!")
        connection.close()
        return

    # Insert attendance record
    cur.execute("""
        INSERT INTO attendance (student_id, date, time)
        VALUES (?, ?, ?)
    """, (student_id, date, time))

    connection.commit()
    connection.close()

    print(f"Attendance recorded for {student[0]} at {time}")


# Temporary test
if __name__ == "__main__":
    mark_attendance("20008273")