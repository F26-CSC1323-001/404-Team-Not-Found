from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
from flask import request, session, redirect, url_for, flash, abort
from flask import Flask, render_template, jsonify, Response
import csv
import io
from datetime import datetime, date, time
import os
import secrets
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database import initialize_database, connect, COURSES
from schedule import get_schedule

app = Flask(__name__)
# Stable secret across restarts; do not commit this local file.
SECRET_FILE = Path(__file__).resolve().parent.parent / ".flask_secret"
if not SECRET_FILE.exists():
    SECRET_FILE.write_text(secrets.token_hex(32), encoding="utf-8")
app.secret_key = SECRET_FILE.read_text(encoding="utf-8").strip()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def admin_required(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Login required"}), 401
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapped


@app.before_request
def protect_pages():
    if request.endpoint in ("login", "static"):
        return None
    if not session.get("admin"):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Login required"}), 401
        return redirect(url_for("login"))
    if request.method == "POST" and request.endpoint in ("admin", "logout", "register_face_check", "register_face_save"):
        if (request.headers.get("X-CSRF-Token") if request.is_json else request.form.get("csrf_token")) != session.get("csrf_token"):
            abort(403)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # Password hash is provisioned with setup_admin.py; no default password.
        with connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS admin_users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)")
            row = conn.execute("SELECT password_hash FROM admin_users WHERE username = ?", (username,)).fetchone()
        if row and check_password_hash(row[0], password):
            session.clear()
            session["admin"] = username
            session["csrf_token"] = secrets.token_hex(24)
            return redirect(url_for("admin"))
        error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    initialize_database()
    if request.method == "POST":
        action = request.form.get("action")
        course = request.form.get("course", "")
        if course not in COURSES:
            abort(400)
        if action == "schedule":
            try:
                start = time.fromisoformat(request.form.get("start", ""))
                end = time.fromisoformat(request.form.get("end", ""))
                grace = int(request.form.get("grace", ""))
                days = sorted({int(day) for day in request.form.getlist("days")})
                if not start < end or not 0 <= grace <= 60 or not days or any(day not in range(7) for day in days):
                    raise ValueError
                if datetime.combine(date.today(), start).timestamp() + grace*60 >= datetime.combine(date.today(), end).timestamp():
                    raise ValueError
            except (ValueError, TypeError):
                flash("Invalid schedule: start must precede end, grace must fit, and select meeting days.")
            else:
                with connect() as conn:
                    conn.execute("""INSERT INTO course_schedules(course,start_time,end_time,grace_minutes,meeting_days)
                        VALUES (?,?,?,?,?) ON CONFLICT(course) DO UPDATE SET
                        start_time=excluded.start_time, end_time=excluded.end_time,
                        grace_minutes=excluded.grace_minutes, meeting_days=excluded.meeting_days""",
                        (course, start.strftime("%H:%M"), end.strftime("%H:%M"), grace, ",".join(map(str, days))))
                flash(f"Schedule saved for {course}.")
        elif action == "enroll":
            student_id = request.form.get("student_id", "").strip()
            with connect() as conn:
                if conn.execute("SELECT 1 FROM students WHERE student_id=?", (student_id,)).fetchone():
                    conn.execute("INSERT OR IGNORE INTO enrollments(student_id,course) VALUES (?,?)", (student_id, course))
                    flash("Enrollment saved.")
                else:
                    flash("Student not found. Register their face first.")
        else:
            abort(400)
        return redirect(url_for("admin"))
    with connect() as conn:
        schedules = {row[0]: dict(start=row[1], end=row[2], grace=row[3], days=row[4].split(","))
                     for row in conn.execute("SELECT course,start_time,end_time,grace_minutes,meeting_days FROM course_schedules")}
        students = conn.execute("SELECT student_id,name FROM students ORDER BY name").fetchall()
        enrollments = conn.execute("SELECT student_id,course FROM enrollments ORDER BY course,student_id").fetchall()
    return render_template("admin.html", courses=COURSES, schedules=schedules,
                           students=students, enrollments=enrollments, csrf_token=session["csrf_token"])

ALLOWED_COURSES = {"CSC130", "CSC131", "CSC132", "CSC230"}

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "student_info.db"
RECOGNITION_SCRIPT = BASE_DIR.parent / "face_recognition.py"
# Prefer the project's Python 3.12 environment for camera/MediaPipe scripts.
# This also works if Flask was accidentally started with another Python.
PROJECT_ROOT = BASE_DIR.parent
if os.name == "nt":
    PROJECT_PYTHON = PROJECT_ROOT / ".venv312" / "Scripts" / "python.exe"
else:
    PROJECT_PYTHON = PROJECT_ROOT / ".venv312" / "bin" / "python"
CAMERA_PYTHON = str(PROJECT_PYTHON) if PROJECT_PYTHON.is_file() else sys.executable
_process_lock = threading.Lock()
_recognition_process = None


def report_data(course, report_date):
    """Return one course/day roster, only when an actual session exists."""
    initialize_database()
    with connect() as conn:
        conn.row_factory = sqlite3.Row
        session_exists = conn.execute(
            "SELECT 1 FROM class_sessions WHERE course=? AND date=?", (course, report_date)
        ).fetchone() is not None
        rows = conn.execute("""SELECT s.student_id, s.name, a.time, a.status
            FROM enrollments e JOIN students s ON s.student_id=e.student_id
            LEFT JOIN attendance a ON a.student_id=e.student_id
                AND a.course=e.course AND a.date=?
            WHERE e.course=? ORDER BY s.name, s.student_id""", (report_date, course)).fetchall()
    schedule = get_schedule(course)
    finished = bool(schedule and report_date < date.today().isoformat())
    if schedule and report_date == date.today().isoformat():
        finished = datetime.now().time() >= time.fromisoformat(schedule["end"])
    records = []
    for row in rows:
        if row["time"]:
            status = row["status"] or "Present"
        elif session_exists and finished:
            status = "Absent"
        else:
            status = "Pending"
        records.append({"student_id": row["student_id"], "name": row["name"],
                        "time": row["time"] or "—", "status": status})
    totals = {status: sum(r["status"] == status for r in records)
              for status in ("Present", "Late", "Absent", "Pending")}
    return records, totals, session_exists


@app.get("/reports")
def reports():
    course = request.args.get("course", "CSC130")
    report_date = request.args.get("date", date.today().isoformat())
    if course not in COURSES:
        abort(400)
    try:
        date.fromisoformat(report_date)
    except ValueError:
        abort(400)
    records, totals, session_exists = report_data(course, report_date)
    if request.args.get("format") == "csv":
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["Student ID", "Student Name", "Course", "Date", "Check-in Time", "Status"])
        for row in records:
            writer.writerow([row["student_id"], row["name"], course, report_date,
                             row["time"], row["status"]])
        return Response(stream.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="attendance_{course}_{report_date}.csv"'})
    return render_template("reports.html", courses=COURSES, course=course,
                           report_date=report_date, records=records, totals=totals,
                           session_exists=session_exists)


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/CSC130")
def csc130():
    return render_template("CSC130.html")


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
    initialize_database()
    today = date.today().isoformat()
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Historical check-ins (including the status saved at check-in time).
    cursor.execute("""SELECT students.name, attendance.date, attendance.time,
                             COALESCE(attendance.status, 'Present')
                      FROM attendance JOIN students
                      ON attendance.student_id = students.student_id
                      WHERE attendance.course = ?
                      ORDER BY attendance.date DESC, attendance.time DESC""", (course,))
    records = [list(row) for row in cursor.fetchall()]
    # Absent is computed only for a recorded class session after its end.
    config = get_schedule(course)
    if config:
        cursor.execute("SELECT 1 FROM class_sessions WHERE course = ? AND date = ?", (course, today))
        session_exists = cursor.fetchone() is not None
        end_time = time.fromisoformat(config["end"])
        if session_exists and datetime.now().time() >= end_time:
            cursor.execute("""SELECT students.name FROM enrollments
                              JOIN students ON students.student_id = enrollments.student_id
                              WHERE enrollments.course = ? AND NOT EXISTS (
                                SELECT 1 FROM attendance
                                WHERE attendance.student_id = enrollments.student_id
                                  AND attendance.course = ? AND attendance.date = ?
                              ) ORDER BY students.name""", (course, course, today))
            records.extend([[name, today, "--", "Absent"] for (name,) in cursor.fetchall()])
    connection.close()
    return jsonify(records)


@app.post("/api/sessions/<course>/today")
def create_today_session(course):
    if not get_schedule(course):
        return jsonify({"error": "Course schedule not configured"}), 400
    if str(date.today().weekday()) not in get_schedule(course)["meeting_days"].split(","):
        return jsonify({"error": "This course does not meet today"}), 400
    origin = request.headers.get("Origin")
    if origin and origin.rstrip("/") != request.host_url.rstrip("/"):
        return jsonify({"error": "Invalid request origin"}), 403
    initialize_database()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO class_sessions(course, date) VALUES (?, ?)",
                     (course, date.today().isoformat()))
    return jsonify({"message": "Class session created for today"}), 201


@app.post("/api/start-attendance/<course>")
def start_attendance(course):
    global _recognition_process
    if course not in ALLOWED_COURSES:
        return jsonify({"error": "Unknown course"}), 404
    # Only allow requests originating from this local Flask dashboard.
    origin = request.headers.get("Origin")
    if origin and origin.rstrip("/") != request.host_url.rstrip("/"):
        return jsonify({"error": "Invalid request origin"}), 403
    if get_schedule(course):
        if str(date.today().weekday()) not in get_schedule(course)["meeting_days"].split(","):
            return jsonify({"error": "This course does not meet today"}), 400
        initialize_database()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT OR IGNORE INTO class_sessions(course, date) VALUES (?, ?)", (course, date.today().isoformat()))
    if not RECOGNITION_SCRIPT.is_file():
        return jsonify({"error": "Recognition script not found"}), 500
    if not (BASE_DIR.parent / "face_trainer.yml").is_file():
        return jsonify({"error": "Trained model missing. Run face_training.py first."}), 400
    with _process_lock:
        if _recognition_process is not None and _recognition_process.poll() is None:
            return jsonify({"error": "An attendance camera session is already running"}), 409
        try:
            _recognition_process = subprocess.Popen(
                [CAMERA_PYTHON, str(RECOGNITION_SCRIPT), "--course", course],
                cwd=str(BASE_DIR.parent),
            )
        except OSError as exc:
            return jsonify({"error": f"Unable to launch camera: {exc}"}), 500
    return jsonify({"message": f"Camera launched for {course}. Press M to mark attendance and Q to quit."}), 202


@app.get("/api/attendance-session")
def attendance_session():
    with _process_lock:
        active = _recognition_process is not None and _recognition_process.poll() is None
    return jsonify({"active": active})

# Browser-based face registration. Keep biometric data local and admin-only.
@app.get("/register-face")
@admin_required
def register_face_page():
    initialize_database()
    return render_template("register_face.html", csrf_token=session["csrf_token"])


def _decode_face(data_url):
    import base64
    import cv2
    import numpy as np
    if not isinstance(data_url, str) or not data_url.startswith("data:image/jpeg;base64,"):
        raise ValueError("Expected a JPEG camera frame")
    encoded = data_url.split(",", 1)[1]
    if len(encoded) > 450000:
        raise ValueError("Camera frame too large")
    try:
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(encoded, validate=True), dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception as exc:
        raise ValueError("Invalid camera frame") from exc
    if frame is None:
        raise ValueError("Could not read camera frame")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(55, 55))
    if len(faces) != 1:
        raise ValueError("Exactly one clearly visible face is required")
    x, y, w, h = faces[0]
    return cv2.resize(gray[y:y+h, x:x+w], (160, 160))


def _possible_match(face):
    import cv2
    model = Path(__file__).resolve().parent.parent / "face_trainer.yml"
    if not model.exists():
        return None
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(model))
    try:
        predicted_id, distance = recognizer.predict(face)
    except cv2.error:
        return None
    # LBPH distance is not a probability; flag for human review, never assert identity.
    if distance >= 70:
        return None
    with connect() as conn:
        row = conn.execute("SELECT student_id,name FROM students WHERE student_id=?", (str(predicted_id),)).fetchone()
    return {"student_id": row[0], "name": row[1], "distance": round(float(distance), 1)} if row else None


@app.post("/api/registration/check")
@admin_required
def register_face_check():
    try:
        face = _decode_face((request.get_json(silent=True) or {}).get("image"))
        return jsonify({"possible_match": _possible_match(face)})
    except (ValueError, ImportError, AttributeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/registration/save")
@admin_required
def register_face_save():
    import cv2
    import numpy as np
    import tempfile
    import shutil
    data = request.get_json(silent=True) or {}
    student_id = str(data.get("student_id", "")).strip()
    name = str(data.get("name", "")).strip()
    images = data.get("images", [])
    if not student_id.isdigit() or not 1 <= len(name) <= 100 or not isinstance(images, list) or len(images) != 30:
        return jsonify({"error": "Enter a numeric ID, name, and exactly 30 face frames."}), 400
    initialize_database()
    with connect() as conn:
        if conn.execute("SELECT 1 FROM students WHERE student_id=?", (student_id,)).fetchone():
            return jsonify({"error": "Student ID already registered."}), 409
    try:
        faces = [_decode_face(item) for item in images]
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    matches = [_possible_match(faces[i]) for i in (0, 9, 19, 29)]
    matches = [m for m in matches if m]
    if matches and not data.get("reviewed_possible_match"):
        return jsonify({"error": "Possible existing registration. Admin review required.", "possible_match": matches[0]}), 409
    # If admin overrides a warning, require explicit confirmation in UI.
    samples = Path(__file__).resolve().parent.parent / "face_samples"
    samples.mkdir(exist_ok=True)
    written = []
    try:
        for i, face in enumerate(faces, 1):
            path = samples / f"{student_id}_{i}.jpg"
            if path.exists() or not cv2.imwrite(str(path), face):
                raise RuntimeError("Could not safely save face samples")
            written.append(path)
        with connect() as conn:
            conn.execute("INSERT INTO students(student_id,name) VALUES (?,?)", (student_id, name))
        # Retrain using the project's existing script; registration succeeds only if training succeeds.
        result = subprocess.run([CAMERA_PYTHON, str(PROJECT_ROOT / "face_training.py")],
                                capture_output=True, text=True, timeout=90)
        if result.returncode != 0:
            raise RuntimeError("Training failed: " + result.stderr[-250:])
    except Exception as exc:
        for path in written:
            path.unlink(missing_ok=True)
        with connect() as conn:
            conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        return jsonify({"error": str(exc)}), 500
    return jsonify({"message": "Registration and model training complete", "student_id": student_id, "name": name})


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)
