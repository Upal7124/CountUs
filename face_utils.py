import mysql.connector
import os

def save_face_to_db(image_path, eid, name, email, phone):
    try:
        filename = os.path.basename(image_path)

        # Connect to MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="countus"
        )
        cursor = conn.cursor()

        # Insert employee with filename as Face
        query = """
            INSERT INTO employee_table (EID, Name, Email, Phone, Face)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (eid, name, email, phone, filename))
        conn.commit()

        cursor.close()
        conn.close()
        return True, f"✅ Employee '{name}' added successfully."

    except Exception as e:
        return False, f"❌ Error: {str(e)}"
