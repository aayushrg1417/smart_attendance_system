from deepface import DeepFace
import os
import shutil

def load_students_from_db(cursor):

    db_folder = "temp_students"

    # delete old folder
    if os.path.exists(db_folder):
        shutil.rmtree(db_folder)

    os.makedirs(db_folder)

    cursor.execute("SELECT username, profile_img FROM users WHERE role='student'")
    students = cursor.fetchall()

    for student in students:
        username = student[0]
        img_path = student[1]

        student_folder = os.path.join(db_folder, username)
        os.makedirs(student_folder, exist_ok=True)

        if os.path.exists(img_path):
            new_path = os.path.join(student_folder, "img.jpg")
            shutil.copy(img_path, new_path)

    return db_folder




def process_class_image(image_path, db_path):

    print("Processing image...")

    results = DeepFace.find(
        img_path=image_path,
        db_path=db_path,
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