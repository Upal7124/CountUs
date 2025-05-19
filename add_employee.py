import face_recognition
import mysql.connector
import pickle
import os

def save_face_to_db(image_path, eid, name, email, phone):
    try:
        # Load image and encode face
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if not encodings:
            return False, "❌ No face found in the image."

        face_encoding = encodings[0]
        encoded_data = pickle.dumps(face_encoding)

        # Get only the filename (not full path)
        face_filename = os.path.basename(image_path)

        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="countus"
        )
        cursor = conn.cursor()

        # Insert employee with face data and filename
        query = """
            INSERT INTO employee_table (EID, Name, Email, Phone, Face, face_filename)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (eid, name, email, phone, encoded_data, face_filename))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('employee'))

    except Exception as e:
        return False, f"❌ Error: {str(e)}"
