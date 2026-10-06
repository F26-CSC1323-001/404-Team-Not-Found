import cv2


# Create the LBPH face recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()


# Load the trained face data
recognizer.read("face_trainer.yml")


# Load the Haar Cascade face detector
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# Open camera
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)


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


        # Lower confidence value means a closer match
        if confidence < 70:

            text = f"Student ID: {student_id}"

            # Green
            color = (0, 255, 0)

        else:

            text = "Unknown"

            # Red
            color = (0, 0, 255)


        # Draw rectangle around face
        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            color,
            2
        )


        # Display result above face
        cv2.putText(
            frame,
            text,
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )


    # Show camera
    cv2.imshow(
        "Face Recognition",
        frame
    )


    # Press q to stop
    if cv2.waitKey(1) == ord("q"):
        break


# Release camera
camera.release()

# Close OpenCV windows
cv2.destroyAllWindows()