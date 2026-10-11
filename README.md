# Student Attendance Management System

A beginner-friendly BTech mini-project prototype built with Python Flask and SQLite.

## Features
- Demo login
- Add and list students
- Add and list subjects
- Mark attendance by subject and date
- Update attendance if the same session is saved again
- Calculate attendance percentages
- Delete students or subjects (related attendance records are also removed)

## Requirements
- Python 3.10 or newer recommended
- Internet connection only if Flask needs to be installed
- VS Code or another code editor
- A web browser

## Setup on Windows
1. Extract the ZIP file.
2. Open the extracted `student_attendance_management_system` folder in VS Code.
3. Open Terminal > New Terminal.
4. (Optional but recommended) Create a virtual environment:
   ```powershell
   py -m venv venv
   .\venv\Scripts\activate
   ```
5. Install the dependency:
   ```powershell
   py -m pip install -r requirements.txt
   ```
6. Run the app:
   ```powershell
   py app.py
   ```
7. Open this address in your browser:
   `http://127.0.0.1:5000`
8. Sign in with the demo credentials:
   - Username: `admin`
   - Password: `admin123`

## First-time usage
1. Open **Students** and add sample students.
2. Open **Subjects** and add subjects.
3. Open **Attendance**, choose a subject and date, then click **Load session**.
4. Mark each student Present or Absent and click **Save Attendance**.
5. Open **Reports**, select the subject, and click **Generate Report**.

## Attendance percentage
Attendance percentage = (Number of classes present / Number of classes marked) × 100.

Only sessions that have attendance saved are counted. This prototype does not automatically create class sessions.

## Database
The app automatically creates `attendance.db` when started. It stores student, subject, and attendance data locally in SQLite.

## Important notes
- This is a learning prototype, not a production-ready attendance or authentication system.
- The demo username/password are hard-coded for simplicity. Do not deploy this app publicly with demo credentials.
- For real deployment, use secure password hashing, CSRF protection, stronger session configuration, access controls, backups, and proper validation.
- This is a standalone Python web app. It is not an actual SAP implementation. If the assignment requires SAP, use your authorized SAP training environment and the modules specified by your instructor.
