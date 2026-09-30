from datetime import datetime
import sqlite3

now = datetime.now()

date = now.strftime("%Y-%m-%d")
time = now.strftime("%H:%M:%S")

connection = sqlite3.connect("student_info.db")
cur = connection.cursor()

student_id = "20008273"
cur.execute('''
    INSERT INTO attendance (student_id, date, time)
        VALUES (?, ?, ?)
    ''', (student_id, date, time))

connection.commit()

print("Attendance recorder Successfully!")
connection.close()