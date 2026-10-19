
import cv2
import numpy as np
from pathlib import Path
from collections import Counter

# Find the project folder
BASE_DIR = Path(__file__).resolve().parent
face_folder = BASE_DIR / "face_samples"
trainer_path = BASE_DIR / "face_trainer.yml"

recognizer = cv2.face.LBPHFaceRecognizer_create()

face_images = []
student_labels = []

# Read all registered face images
for image_path in face_folder.glob("*.jpg"):

    try:
        student_id = int(image_path.stem.split("_")[0])
    except ValueError:
        print(f"Skipping invalid filename: {image_path.name}")
        continue

    face_image = cv2.imread(
        str(image_path),
        cv2.IMREAD_GRAYSCALE
    )

    if face_image is None:
        print(f"Could not load: {image_path.name}")
        continue

    face_images.append(face_image)
    student_labels.append(student_id)

# Check whether images were found
if not face_images:
    print("No valid face images found!")
    raise SystemExit

# Show how many samples belong to each student
sample_counts = Counter(student_labels)

print("\nTraining samples:")
for student_id, count in sorted(sample_counts.items()):
    print(f"Student {student_id}: {count} images")

# Train using all valid images
recognizer.train(
    face_images,
    np.array(student_labels, dtype=np.int32)
)

# Save the trained model
recognizer.write(str(trainer_path))

print("\nFace Training Completed!")
print(f"Total students: {len(sample_counts)}")
print(f"Total images: {len(face_images)}")
