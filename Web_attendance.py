import cv2
import numpy as np
import face_recognition
import mysql.connector
import pickle
import json
from datetime import datetime

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="countus"
)
cursor = db.cursor()

# Load known faces from MySQL
def load_known_faces():
    cursor.execute("SELECT Face, Name, EID FROM employee_table")
    known_encodings, known_names, known_ids = [], [], []

    for encoding_blob, name, user_id in cursor.fetchall():
        if encoding_blob:
            try:
                encoding = pickle.loads(encoding_blob)
                if isinstance(encoding, np.ndarray):
                    known_encodings.append(encoding)
                    known_names.append(name)
                    known_ids.append(user_id)
            except Exception as e:
                print(f"❌ Failed to load encoding: {e}")

    print(f"✅ Loaded {len(known_encodings)} known faces.")
    return known_encodings, known_names, known_ids

known_encodings, known_names, known_ids = load_known_faces()

# Mark attendance and save to JSON
def mark_attendance(user_id, name):
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    checkin_time = now.strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT * FROM employee_attendance_live WHERE EID = %s AND DATE(Date) = %s", (user_id, today_date))
    if cursor.fetchone():
        print("🟡 Already marked today.")
        return

    try:
        cursor.execute(
            "INSERT INTO employee_attendance_live (EID, Status, CheckIN, Date) VALUES (%s, %s, %s, %s)",
            (user_id, 1, checkin_time, checkin_time)
        )
        db.commit()
        print(f"✅ Attendance marked for {name}.")

        attendance_data = {"name": name, "time": now.strftime("%H:%M:%S")}
        with open("attendance.json", "w") as f:
            json.dump(attendance_data, f)

    except Exception as e:
        print(f"❌ Error inserting into DB: {e}")

# Initialize webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ Failed to access the camera.")
    exit()

print("📷 Camera started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame.")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    recognized_name = "Unknown"
    recognized_id = None

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
        if face_distances[best_match_index] < 0.45:  # adjust threshold if needed
            recognized_name = known_names[best_match_index]
            recognized_id = known_ids[best_match_index]
            mark_attendance(recognized_id, recognized_name)
        else:
            print("🔍 Face detected but not recognized (distance too high).")


    for (top, right, bottom, left) in face_locations:
        top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, recognized_name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("❎ Exiting...")
        break

cap.release()
cv2.destroyAllWindows()
db.close()
