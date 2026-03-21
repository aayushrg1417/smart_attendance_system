import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root@17",
    database="attendance_system"
)

cursor = conn.cursor()