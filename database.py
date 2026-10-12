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
students = [
    ("20008273", "Aaditya"),
    ("20092753", "Alec"),
    ("20506611", "Kevin")
]
# #####################################################



if __name__=="__main__":
    for student_id, name in students:

        cur.execute("""
            SELECT * FROM students
            WHERE student_id = ?
        """, (student_id,))

        student = cur.fetchone()

    # Add student if not already registered
        if student is None:
            cur.execute("""
                INSERT INTO students (student_id, name)
                VALUES (?, ?)
            """, (student_id, name))

            print(f"{name} added successfully!")

        else:
            print(f"{name} already exists!")

connection.commit()
connection.close()

# Retrieve student name using student ID
def get_student_name(student_id):

    connection = sqlite3.connect("student_info.db")
    cur = connection.cursor()

    cur.execute("""
        SELECT name FROM students
        WHERE student_id = ?
    """, (str(student_id),))

    student = cur.fetchone()

    connection.close()

    if student is not None:
        return student[0]

    return None

print(get_student_name("20008273"))
print(get_student_name("20092753"))
print(get_student_name("20506611"))