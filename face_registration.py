import cv2
import os

face_folder = "face_samples"

if not os.path.exists(face_folder):
    os.makedirs(face_folder)

student_id = input("Enter student ID: ")

# Counts how many face pictures are saved
sample_count = 0

# counts frames detected
frame_count = 0


# Load the face detector
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)


while True:

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


    for (x, y, w, h) in faces:

        # Cut out only the detected face
        face = gray[y:y+h, x:x+w]

        # Count detected frames
        frame_count += 1


        # Save one face every 5 detected frames
        if frame_count % 5 == 0:

            sample_count += 1

            file_name = os.path.join(
                face_folder,
                f"{student_id}_{sample_count}.jpg"
            )

            cv2.imwrite(file_name, face)

            print(f"Saved sample {sample_count}/30")


        # Draw green rectangle around detected face
        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )


        # Show the extracted face
        cv2.imshow("Detected Face", face)


    # Show normal camera
    cv2.imshow("Registration Camera", frame)


    # Stop automatically after 30 saved pictures
    if sample_count >= 30:
        print("Face registration complete!")
        break


    # Press q if you want to stop manually
    if cv2.waitKey(1) == ord("q"):
        break


# Release camera and close windows
camera.release()
cv2.destroyAllWindows()