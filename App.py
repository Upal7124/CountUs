from flask import Flask, render_template, request, redirect, url_for, flash, Response
import subprocess
import signal
import os
import uuid
from face_utils import save_face_to_db  # Ensure this exists!
import mysql.connector
from datetime import date,datetime,timedelta

face_process = None

app = Flask(__name__)
app.secret_key = 'secret'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

@app.route('/Simple_dashboard')
def dashboard_simple():
    return render_template('index.html')

@app.route('/employee')
def employee():
    employees = get_all_employees()
    return render_template('emp.html', employees=employees)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='countus'
    )
def get_all_employees():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="countus"
    )
    cursor = conn.cursor()

    # Get the face filename instead of raw face data
    cursor.execute("SELECT EID, face_filename, Name, Email, Phone, Salary FROM employee_table")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'id': row[0],
            'face_url': f"uploads/{row[1]}" if row[1] else None,
            'name': row[2],
            'email': row[3],
            'phone': row[4],
            'salary': row[5]
        }
        for row in rows
    ]



@app.route('/add_employee', methods=['POST'])
def add_employee():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    face_image = request.files.get('face_image')

    if face_image:
        filename = str(uuid.uuid4()) + os.path.splitext(face_image.filename)[1]
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        face_image.save(image_path)

        eid = str(uuid.uuid4())[:6]  # Generate unique Employee ID

        success, message = save_face_to_db(image_path, eid, name, email, phone)

        flash(message)
        if success:
            return redirect(url_for('employee'))
        else:
            return message, 400

    return "No image uploaded", 400
@app.route('/live_attendance')
def live_attendance():
    return render_template('live_attendance.html')

@app.route('/start', methods=['POST'])
def start():
    global face_process
    if face_process is None or face_process.poll() is not None:
        face_process = subprocess.Popen(
            ['python', 'Web_attendance.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE  # for Windows
        )
        print("✅ Face attendance process started.")
    else:
        print("⚠️ Process already running.")
    return redirect(url_for('live_attendance'))


@app.route('/stop', methods=['POST'])
def stop():
    global face_process
    if face_process is not None:
        face_process.terminate()
        face_process = None
        print("🛑 Face attendance process stopped.")
    else:
        print("⚠️ No process was running.")
    return redirect(url_for('live_attendance'))

@app.route('/')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    today = date.today()

    # Total Employees
    cursor.execute("SELECT COUNT(*) AS total FROM employee_table")
    total_employees = cursor.fetchone()['total']

    # Present Today
    cursor.execute("""
        SELECT COUNT(DISTINCT EID) AS present
        FROM employee_attendance_live
        WHERE status = 1 AND date = %s
    """, (today,))
    present_today = cursor.fetchone()['present']

    # Absent = Total - Present
    absent_today = total_employees - present_today

    # Get employee names who are present today
    cursor.execute("""
        SELECT e.name, a.CheckIN
        FROM employee_attendance_live a
        JOIN employee_table e ON a.EID = e.EID
        WHERE a.status = 1 AND a.date = %s
    """, (today,))
    raw_present_employees = cursor.fetchall()
    present_employees = []
    for emp in raw_present_employees:
        name = emp['name']
        checkin_raw = emp['CheckIN']

        if isinstance(checkin_raw, datetime):  # ✅ Check if it's really a datetime
            checkin_dt = checkin_raw
            checkin = checkin_dt.strftime("%H:%M:%S")

            checkout_dt = checkin_dt + timedelta(hours=8)
            checkout = checkout_dt.strftime("%H:%M:%S")
        else:
            checkin = "N/A"
            checkout = "N/A"

            present_employees.append({
            'name': name,
            'checkin': checkin,
            'check_out': checkout
        })

    cursor.close()
    conn.close()

    return render_template("Index.html",
                           total=total_employees,
                           present=present_today,
                           absent=absent_today,
                           present_employees=present_employees)
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

