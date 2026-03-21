from deepface import DeepFace
import os

STUDENT_DB = "students"


def process_class_image(image_path):

    print("Processing image...")

    results = DeepFace.find(
        img_path=image_path,
        db_path=STUDENT_DB,
        model_name="ArcFace",
        detector_backend="retinaface",
        enforce_detection=False
    )

    present_students = set()

    for face_matches in results:

        if face_matches.empty:
            continue

        best_match = face_matches.iloc[0]["identity"]

        student_name = os.path.basename(os.path.dirname(best_match))

        present_students.add(student_name)

    return list(present_students)