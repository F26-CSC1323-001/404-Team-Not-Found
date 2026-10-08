import sqlite3

connection = sqlite3.connect("student_info.db")
cur = connection.cursor()

# Create the students table
cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL
    )
""")

# create the table for attendance
cur.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL
    )
''')

# student_info for a while till I create a function for the input for new students
student_id = "20008273"
name = "Aaditya"

student_id = "20092753"
name = "Alec"
# #####################################################


# Check if student already exists
cur.execute("""
    SELECT * FROM students
    WHERE student_id = ?
""", (student_id,))

student = cur.fetchone()

# Add student only if they don't already exist
if student is None:
    cur.execute("""
        INSERT INTO students (student_id, name)
        VALUES (?, ?)
    """, (student_id, name))

    print("Student added successfully!")

else:
    print("Student already exists!")

connection.commit()
connection.close()