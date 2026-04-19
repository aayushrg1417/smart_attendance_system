from flask import Flask, render_template, request, jsonify
from flask import session, redirect, url_for
from engine.video_engine import process_video
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

    if "user" not in session:
        return redirect("/")

    username = session["user"]   # ✅ same as student

    # 👤 Fetch teacher details
    cursor.execute(
        """
        SELECT name, username, email, phone, department, division, profile_img 
        FROM users 
        WHERE username=%s
        """,
        (username,)
    )
    user = cursor.fetchone()

    print("TEACHER DATA:", user)   # debug

    return render_template("teacher.html", user=user)


# Student Page
@app.route("/student")
def student_page():

    if "user" not in session:
        return redirect("/")

    username = session["user"]   
    
    print("SESSION USER:", username)

    # Attendance
    cursor.execute(
        "SELECT date FROM attendance WHERE student_name = %s",
        (username,)
    )
    records = cursor.fetchall()
    records = [str(r[0]) for r in records]

    # User details (correct)
    cursor.execute(
        """
        SELECT name, username, email, phone, department, division, profile_img 
        FROM users 
        WHERE username=%s
        """,
        (username,)   # ✅ FIX
    )
    user = cursor.fetchone()

    print("FETCHED USER:", user)

    # Ads
    cursor.execute("""
        SELECT image_path 
        FROM ads 
        WHERE status='published'
        AND expiry_date >= CURDATE()
    """)
    ads = cursor.fetchall()

    return render_template(
        "student.html",
        name=username,
        records=records,
        user=user,
        ads=ads
    )
    

#ads/token
@app.route("/ads")
def ads_page():

    if "user" not in session:
        return redirect("/")

    username = session["user"]

    cursor.execute(
        "SELECT * FROM ads WHERE username=%s",
        (username,)
    )
    my_ads = cursor.fetchall()

    return render_template("ads.html", ads=my_ads)

#raise_token
from datetime import datetime, timedelta
import os

@app.route("/raise_token", methods=["POST"])
def raise_token():

    print("🔥 RAISE TOKEN HIT")

    if "user" not in session:
        return redirect("/")

    username = session["user"]

    # ✅ CHECK FILE EXISTS
    if "image" not in request.files:
        return "No file uploaded"

    file = request.files["image"]

    if file.filename == "":
        return "No selected file"

    duration = request.form.get("duration")

    if not duration:
        return "Duration missing"

    # 📁 CREATE FOLDER
    if not os.path.exists("static/ads"):
        os.makedirs("static/ads")

    # ✅ SAFE FILE NAME
    filename = file.filename.replace(" ", "_")
    path = os.path.join("static/ads", filename)

    file.save(path)

    print("📁 Saved at:", path)

    # 👤 GET USER DETAILS
    cursor.execute(
        "SELECT name, department FROM users WHERE username=%s",
        (username,)
    )
    user = cursor.fetchone()

    print("👤 USER:", user)

    if not user:
        return "User not found"

    # ⏳ EXPIRY CALCULATION
    days = int(duration)
    expiry_date = datetime.now() + timedelta(days=days)

    print("📅 EXPIRY:", expiry_date)

    # 💾 INSERT INTO DB
    cursor.execute(
        """
        INSERT INTO ads 
        (username, name, department, image_path, duration, status, payment_status, expiry_date)
        VALUES (%s, %s, %s, %s, %s, 'pending', 'unpaid', %s)
        """,
        (username, user[0], user[1], path, duration, expiry_date)
    )

    conn.commit()

    print("✅ INSERTED INTO DB")

    return redirect("/ads")

#Admin_panel

# 👉 Redirect /admin → /admin/dashboard
@app.route("/admin")
def admin():
    return redirect("/admin/dashboard")


# 👉 Main Admin Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/")

    cursor.execute("SELECT * FROM ads ORDER BY id DESC")
    ads = cursor.fetchall()
    
    print("ADS DATA:", ads)

    return render_template("admin.html", ads=ads)


# 👉 Accept Ad
@app.route("/accept_ad/<int:id>")
def accept_ad(id):

    if "admin" not in session:
        return redirect("/")

    cursor.execute(
        "UPDATE ads SET status='accepted' WHERE id=%s",
        (id,)
    )
    conn.commit()

    return redirect("/admin/dashboard")


# 👉 Reject Ad
@app.route("/reject_ad/<int:id>")
def reject_ad(id):

    if "admin" not in session:
        return redirect("/")

    cursor.execute(
        "UPDATE ads SET status='rejected' WHERE id=%s",
        (id,)
    )
    conn.commit()

    return redirect("/admin/dashboard")


# 👉 Publish Ad (after payment)
@app.route("/publish_ad/<int:id>")
def publish_ad(id):

    if "admin" not in session:
        return redirect("/")

    cursor.execute(
        "UPDATE ads SET status='published', payment_status='paid' WHERE id=%s",
        (id,)
    )
    conn.commit()

    return redirect("/admin/dashboard")

# Register
@app.route("/register", methods=["POST"])
def register():

    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]

    email = request.form["email"]
    phone = request.form["phone"]
    department = request.form["department"]
    division = request.form["division"]
    
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return "Username already exists"

    # 📁 HANDLE IMAGE
    file = request.files.get("profile_img")

    img_path = None

    if file and file.filename != "":
        if not os.path.exists("static/uploads"):
            os.makedirs("static/uploads")

        filename = file.filename.replace(" ", "_")
        img_path = "static/uploads/" + filename
        file.save(img_path)

    # 💾 INSERT INTO DB
    cursor.execute("""
        INSERT INTO users 
        (name, username, password, role, email, phone, department, division, profile_img)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, username, password, role, email, phone, department, division, img_path))

    conn.commit()

    return redirect("/")

#login
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # ✅ ADMIN LOGIN (ADD THIS FIRST)
    if username == "24" and password == "17":
        session["admin"] = True
        return redirect("/admin/dashboard")

    # 👤 NORMAL USER LOGIN
    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )

    user = cursor.fetchone()

    if user:
        session["user"] = user[2]
        session["role"] = user[4]

        if user[4] == "teacher":
            return redirect("/teacher")
        else:
            return redirect("/student")
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

    file = request.files["video"]
    subject = request.form.get("subject")
    lecture_type = request.form.get("lectureType")
    start_time = request.form.get("startTime")
    end_time = request.form.get("endTime")

    # create folder
    if not os.path.exists("videos"):
        os.makedirs("videos")

    video_path = f"videos/{file.filename}"
    file.save(video_path)

    # 🔥 process video
    present_students = process_video(video_path)

    today = date.today()

    for student in present_students:

        cursor.execute(
            """
            SELECT * FROM attendance 
            WHERE student_name=%s AND date=%s AND subject=%s 
            AND start_time=%s AND end_time=%s
            """,
            (student, today, subject, start_time, end_time)
        )

        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO attendance 
                (student_name, date, subject, lecture_type, start_time, end_time, video_path) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (student, today, subject, lecture_type, start_time, end_time, video_path)
            )

    conn.commit()

    return jsonify({
        "present": present_students
    })


if __name__ == "__main__":
    app.run(debug=True)