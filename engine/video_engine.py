import cv2
import os
import shutil
from engine.face_engine import process_class_image


def extract_frames(video_path, output_folder="frames", frame_interval=30, max_frames=12):

    # delete old frames first
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)

    os.makedirs(output_folder)

    cap = cv2.VideoCapture(video_path)

    count = 0
    saved_frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if count % frame_interval == 0:
            frame = cv2.resize(frame, (640, 480))

            frame_path = f"{output_folder}/frame_{count}.jpg"
            cv2.imwrite(frame_path, frame)

            saved_frames.append(frame_path)

            if len(saved_frames) >= max_frames:
                break

        count += 1

    cap.release()
    return saved_frames


def process_video(video_path, db_path):

    frame_folder = "frames"

    frame_paths = extract_frames(video_path, frame_folder)

    all_students = set()

    for frame in frame_paths:
        students = process_class_image(frame, db_path)
        all_students.update(students)

    #  DELETE frames only (NOT video)
    if os.path.exists(frame_folder):
        shutil.rmtree(frame_folder)

    print("Frames deleted after processing")

    return list(all_students)