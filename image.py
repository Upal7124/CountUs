import cv2
import numpy as np
import face_recognition
import mysql.connector
import pickle

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="countus"
)
cursor = db.cursor()

# Load image and generate face encoding
image_path = "upal.jpg"  # Replace with your image path
image = face_recognition.load_image_file(image_path)
face_encodings = face_recognition.face_encodings(image)

if len(face_encodings) > 0:
    encoding_blob = pickle.dumps(face_encodings[0])  # Convert encoding to binary
    name = "Upal Ghosh"
    user_id = 1
    mail = "ghoshupal25@gmail.com"
    phone = 7278313646
    salary = 20000

    # Store in database (Corrected SQL syntax)
    cursor.execute(
        "INSERT INTO employee_table (EID, Name, Face, Email, Phone, Salary) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, name, encoding_blob, mail, phone, salary)
    )
    
    db.commit()
    print(f"✅ Face encoding saved for {name} (ID: {user_id})")
else:
    print("❌ No face detected in the image!")

db.close()
