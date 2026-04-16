from flask import Flask, render_template, request, jsonify
from flask import session, redirect, url_for
from engine.face_engine import process_class_image
from database.db import conn, cursor
from datetime import date
import os

app = Flask(__name__)

app.secret_key = "secret123"


# 🏠 Home
@app.route("/")
def home():
    return render_template("index.html")


# 👨‍🏫 Teacher Page
@app.route("/teacher")
def teacher_page():
    return render_template("teacher.html")


# 🎓 Student Page
@app.route("/student/<name>")
def student_page(name):
    cursor.execute(
        "SELECT date FROM attendance WHERE student_name = %s",
        (name,)
    )
    records = cursor.fetchall()

    records = [str(r[0]) for r in records]

    return render_template("student.html", name=name, records=records)

# Register
@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]

    cursor.execute(
        "INSERT INTO users (name, username, password, role) VALUES (%s, %s, %s, %s)",
        (name, username, password, role)
    )
    conn.commit()

    return redirect("/")

#login
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )

    user = cursor.fetchone()

    if user:
        session["user"] = user[1]
        session["role"] = user[4]

        if user[4] == "teacher":
            return redirect("/teacher")
        else:
            return redirect(f"/student/{user[1]}")
    else:
        return "Invalid Login"
    
   
#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
    


# 📸 Mark Attendance
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    file = request.files["image"]

    # ensure folder exists
    if not os.path.exists("class_images"):
        os.makedirs("class_images")

    image_path = "class_images/temp.jpg"
    file.save(image_path)

    present_students = process_class_image(image_path)

    today = date.today()

    for student in present_students:

        # avoid duplicate entry
        cursor.execute(
            "SELECT * FROM attendance WHERE student_name=%s AND date=%s",
            (student, today)
        )

        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO attendance (student_name, date) VALUES (%s, %s)",
                (student, today)
            )

    conn.commit()

    return jsonify({
        "present": present_students
    })


if __name__ == "__main__":
    app.run(debug=True)