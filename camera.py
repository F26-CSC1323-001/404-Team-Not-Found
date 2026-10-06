import cv2

# Load the face detector
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Open the camera
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:

    # Get a frame from the camera
    success, frame = camera.read()

    if not success:
        print("Camera failed!")
        break

    # Convert the frame from color to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Find faces in the frame
    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5
    )

    # Draw a rectangle around each detected face
    for (x, y, w, h) in faces:
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    # Display the camera
    cv2.imshow("Smart Attendance Camera", frame)

    
    if cv2.waitKey(1) == ord("q"):
        break

# Release the camera and close the window
camera.release()
cv2.destroyAllWindows()