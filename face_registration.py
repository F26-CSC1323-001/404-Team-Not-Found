
import cv2
import os
import sqlite3
from pathlib import Path
from database import initialize_database

# Project folder
BASE_DIR = Path(__file__).resolve().parent
face_folder = BASE_DIR / "face_samples"
db_path = BASE_DIR / "student_info.db"

face_folder.mkdir(exist_ok=True)

# Get student information
student_id = input("Enter student ID (numbers only): ").strip()
student_name = input("Enter student name: ").strip()

if not student_id.isdigit() or not student_name:
    print("Student ID and name cannot be empty!")
    raise SystemExit

initialize_database()

# Check whether the student already exists
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute(
    "SELECT name FROM students WHERE student_id = ?",
    (student_id,)
)

existing_student = cursor.fetchone()

if existing_student is not None:
    print(f"Student already registered: {existing_student[0]}")
    print("Use a new ID for new registrations. Existing samples are not overwritten.")
    connection.close()
    raise SystemExit

# Load the face detector
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("Camera could not open!")
    connection.close()
    raise SystemExit

sample_count = 0
frame_count = 0

print("Look at the camera and slowly turn your head.")
print("Make sure only one person is visible.")
print("Press q to cancel registration.")

while sample_count < 30:

    success, frame = camera.read()

    if not success:
        print("Camera failed!")
        break

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5
    )

    # Capture samples only when exactly one face is detected
    if len(faces) == 1:

        x, y, w, h = faces[0]

        face = gray[y:y+h, x:x+w]

        frame_count += 1

        if frame_count % 5 == 0:

            sample_count += 1

            file_name = face_folder / (
                f"{student_id}_{sample_count}.jpg"
            )

            saved = cv2.imwrite(str(file_name), face)

            if not saved:
                sample_count -= 1
                print("Failed to save face sample!")
            else:
                print(f"Saved sample {sample_count}/30")

        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )

    elif len(faces) > 1:
        cv2.putText(
            frame,
            "Multiple faces detected!",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

    cv2.imshow("Registration Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

# Save student information only after all samples are captured
if sample_count == 30:

    try:
        cursor.execute("""
            INSERT INTO students (student_id, name)
            VALUES (?, ?)
        """, (student_id, student_name))

        connection.commit()

        print("Face registration complete!")
        print(f"Student: {student_name}")
        print(f"Student ID: {student_id}")
        print("Run face_training.py to update the model.")

    except sqlite3.Error as error:
        print("Could not save student:", error)

else:
    print("Registration cancelled or incomplete.")

connection.close()
