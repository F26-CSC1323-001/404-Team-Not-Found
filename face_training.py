import cv2
import os
import numpy as np


face_folder = "face_samples"
recognizer = cv2.face.LBPHFaceRecognizer_create()

face_images = []
student_labels = []

for file_name in os.listdir(face_folder):
    image_path = os.path.join(face_folder, file_name)
    face_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    student_id = int(file_name.split("_")[0])
    face_images.append(face_image)
    student_labels.append(student_id)

recognizer.train(face_images, np.array(student_labels))
recognizer.write("face_trainer.yml")
print("Face Training Completed!")