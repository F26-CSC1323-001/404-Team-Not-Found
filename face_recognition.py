import argparse
from pathlib import Path
from auto_attendance_logic import AutoCheckIn
from liveness_detection import LivenessChallenge, face_signals
import mediapipe as mp

import cv2
from database import get_student_name
from attendance import mark_attendance
from database import COURSES, initialize_database

parser = argparse.ArgumentParser()
parser.add_argument("--course", choices=COURSES, required=True)
args = parser.parse_args()
initialize_database()
BASE_DIR = Path(__file__).resolve().parent

# Create the LBPH face recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Load the trained face data
recognizer.read(str(BASE_DIR / "face_trainer.yml"))

# Load the Haar Cascade face detector
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Open camera
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW if __import__("os").name == "nt" else cv2.CAP_ANY)
if not camera.isOpened():
    raise RuntimeError("Camera could not open")

# Store attendance information
recognized_student_id = None
attendance_message = ""
auto_checkin = AutoCheckIn(required_frames=12, cooldown_seconds=10)
liveness = LivenessChallenge()
mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)
verified_id = None


def attendance_result_message(result):
    return {
        "late": "Attendance Recorded: LATE",
        "recorded": "Attendance Recorded!",
        "duplicate": "Already Marked Today!",
        "not_enrolled": "Not enrolled in this course",
        "outside_window": "Attendance window is closed",
        "not_found": "Student Not Found!",
        "invalid_course": "Invalid course",
    }.get(result, "Could not record attendance")


while True:

    # Read one frame from camera
    success, frame = camera.read()

    if not success:
        print("Camera failed!")
        break

    # Convert camera frame to grayscale
    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    # Detect faces
    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5
    )

    # Default student information
    display_name = "Waiting..."
    display_id = "--"
    display_status = "No Face Detected"
    color = (0, 0, 255)
    recognized_student_id = None

    for (x, y, w, h) in faces:

        # Cut out only the detected face
        face = gray[y:y+h, x:x+w]

        # Ask LBPH to recognize the face
        student_id, confidence = recognizer.predict(face)

        # Print the result in terminal
        print(
            f"Student ID: {student_id}, "
            f"Confidence: {confidence:.2f}"
        )

        # Check if face is recognized
        if confidence < 70:

            # Retrieve student name from database
            student_name = get_student_name(student_id)

            if student_name is not None:

                text = student_name
                display_name = student_name
                display_id = str(student_id)
                display_status = "Recognized"

                recognized_student_id = str(student_id)

                # Green
                color = (0, 255, 0)

            else:

                text = "Unknown"
                display_name = "Unknown"
                display_id = "--"
                display_status = "Not Registered"

                # Red
                color = (0, 0, 255)

        else:

            text = "Unknown"
            display_name = "Unknown"
            display_id = "--"
            display_status = "Not Recognized"

            # Red
            color = (0, 0, 255)

        # Draw rectangle around face
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            color,
            2
        )

        # Display result above face
        cv2.putText(
            frame,
            text,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    # Require exactly one recognized face AND a completed movement challenge.
    candidate = recognized_student_id if len(faces) == 1 else None
    if candidate is None:
        liveness.reset()
        verified_id = None
        allowed = None
    else:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mesh_result = mesh.process(rgb)
        if mesh_result.multi_face_landmarks:
            eye, nose = face_signals(mesh_result.multi_face_landmarks[0])
            passed = liveness.observe(candidate, eye, nose)
        else:
            liveness.reset()
            passed = False
        if verified_id != candidate:
            verified_id = None
        if passed:
            verified_id = candidate
        allowed = candidate if verified_id == candidate else None
        display_status = liveness.instruction if not passed else "Movement verified"

    stable_id = auto_checkin.observe(allowed)
    if stable_id is not None:
        result = mark_attendance(stable_id, args.course)
        attendance_message = attendance_result_message(result)
        print(f"Auto check-in {stable_id} ({args.course}): {result}")

    # Get camera frame dimensions
    height, width = frame.shape[:2]

    # Create information panel at bottom
    cv2.rectangle(
        frame,
        (0, height - 120),
        (width, height),
        (40, 40, 40),
        -1
    )

    # Display student name
    cv2.putText(
        frame,
        f"Name: {display_name}",
        (20, height - 85),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # Display student ID
    cv2.putText(
        frame,
        f"Student ID: {display_id}",
        (20, height - 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # Display recognition status
    cv2.putText(
        frame,
        f"Status: {display_status}",
        (20, height - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2
    )

    # Display attendance message
    cv2.putText(
        frame,
        attendance_message,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    # Show camera
    cv2.imshow(
        "Face Recognition",
        frame
    )

    # Check keyboard input
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    elif key == ord("m"):
        # Manual fallback is restricted to a successfully verified face.
        # For accessibility failures, use a separate supervised process.
        if verified_id != recognized_student_id or verified_id is None:
            attendance_message = "Complete movement challenge first"
            continue
        # Operator can confirm an already verified student.
        if len(faces) != 1:
            attendance_message = "Please show exactly one face"
        elif recognized_student_id is not None:
            attendance_message = attendance_result_message(mark_attendance(recognized_student_id, args.course))
        else:
            attendance_message = "Student Not Recognized!"

# Release camera
camera.release()
mesh.close()

# Close OpenCV windows
cv2.destroyAllWindows()
