from pathlib import Path
import sqlite3
from flask import Flask, render_template, jsonify

app = Flask(__name__)
ALLOWED_COURSES = {"CSC131", "CSC132", "CSC230"}

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "student_info.db"


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/CSC131")
def csc131():
    return render_template("CSC131.html")


@app.route("/CSC132")
def csc132():
    return render_template("CSC132.html")


@app.route("/CSC230")
def csc230():
    return render_template("CSC230.html")

@app.route("/api/attendance")
def get_attendance():

    if not DB_PATH.is_file():
        return jsonify({"error": "Database not found"}), 500

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT students.name, attendance.date, attendance.time
        FROM attendance
        JOIN students
        ON attendance.student_id = students.student_id
        ORDER BY attendance.date DESC, attendance.time DESC
    """)

    records = cursor.fetchall()
    connection.close()

    return jsonify(records)


@app.route("/api/attendance/<course>")
def get_course_attendance(course):
    if course not in ALLOWED_COURSES:
        return jsonify({"error": "Unknown course"}), 404
    if not DB_PATH.is_file():
        return jsonify({"error": "Database not found"}), 500
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT students.name, attendance.date, attendance.time
        FROM attendance
        JOIN students
        ON attendance.student_id = students.student_id
        WHERE attendance.course = ?
        ORDER BY attendance.date DESC, attendance.time DESC
    """, (course,))

    records = cursor.fetchall()
    connection.close()

    return jsonify(records)

if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)