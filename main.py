from engine.face_engine import process_class_image

present = process_class_image("class_images/class4.jpeg")

print("\nPresent Students:")

for student in present:
    print(student)