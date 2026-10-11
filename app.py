import os
import sqlite3
from functools import wraps
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-real-use")
DATABASE = os.path.join(os.path.dirname(__file__), "attendance.db")

# Demo-only login. For a real deployment, use a users table and hashed passwords.
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin123"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT NOT NULL UNIQUE,
            subject_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
            UNIQUE(student_id, subject_id, attendance_date),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
    """)
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == DEMO_USERNAME and password == DEMO_PASSWORD:
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password. Please try again.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    student_count = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    subject_count = db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    today_count = db.execute(
        "SELECT COUNT(*) FROM attendance WHERE attendance_date = ?", (date.today().isoformat(),)
    ).fetchone()[0]
    present_count = db.execute(
        "SELECT COUNT(*) FROM attendance WHERE attendance_date = ? AND status = 'Present'",
        (date.today().isoformat(),)
    ).fetchone()[0]
    return render_template(
        "dashboard.html",
        student_count=student_count,
        subject_count=subject_count,
        today_count=today_count,
        present_count=present_count,
        today=date.today().isoformat()
    )


@app.route("/students", methods=["GET", "POST"])
@login_required
def students():
    db = get_db()
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        if not all([roll_no, name, department, year]):
            flash("Please fill in every student field.", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO students (roll_no, name, department, year) VALUES (?, ?, ?, ?)",
                    (roll_no, name, department, year)
                )
                db.commit()
                flash("Student added successfully.", "success")
                return redirect(url_for("students"))
            except sqlite3.IntegrityError:
                flash("That roll number already exists. Use a unique roll number.", "error")

    student_rows = db.execute("SELECT * FROM students ORDER BY roll_no").fetchall()
    return render_template("students.html", students=student_rows)


@app.route("/students/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    flash("Student and their attendance records were deleted.", "success")
    return redirect(url_for("students"))


@app.route("/subjects", methods=["GET", "POST"])
@login_required
def subjects():
    db = get_db()
    if request.method == "POST":
        code = request.form.get("subject_code", "").strip()
        name = request.form.get("subject_name", "").strip()
        if not code or not name:
            flash("Please enter both the subject code and name.", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO subjects (subject_code, subject_name) VALUES (?, ?)",
                    (code, name)
                )
                db.commit()
                flash("Subject added successfully.", "success")
                return redirect(url_for("subjects"))
            except sqlite3.IntegrityError:
                flash("That subject code already exists.", "error")
    subject_rows = db.execute("SELECT * FROM subjects ORDER BY subject_code").fetchall()
    return render_template("subjects.html", subjects=subject_rows)


@app.route("/subjects/delete/<int:subject_id>", methods=["POST"])
@login_required
def delete_subject(subject_id):
    db = get_db()
    db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    db.commit()
    flash("Subject and its attendance records were deleted.", "success")
    return redirect(url_for("subjects"))


@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    db = get_db()
    students_rows = db.execute("SELECT * FROM students ORDER BY roll_no").fetchall()
    subjects_rows = db.execute("SELECT * FROM subjects ORDER BY subject_code").fetchall()
    selected_date = request.values.get("attendance_date", date.today().isoformat())
    selected_subject = request.values.get("subject_id", "")

    if request.method == "POST":
        if not students_rows or not subjects_rows:
            flash("Add at least one student and one subject before marking attendance.", "error")
            return redirect(url_for("attendance"))
        try:
            subject_id = int(request.form.get("subject_id", ""))
            attendance_date = request.form.get("attendance_date", date.today().isoformat())
            date.fromisoformat(attendance_date)
        except (ValueError, TypeError):
            flash("Please choose a valid subject and date.", "error")
            return redirect(url_for("attendance"))

        valid_subject = db.execute("SELECT id FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if not valid_subject:
            flash("Please choose a valid subject.", "error")
            return redirect(url_for("attendance"))

        for student in students_rows:
            status = request.form.get(f"status_{student['id']}")
            if status not in ("Present", "Absent"):
                continue
            db.execute("""
                INSERT INTO attendance (student_id, subject_id, attendance_date, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_id, subject_id, attendance_date)
                DO UPDATE SET status = excluded.status
            """, (student["id"], subject_id, attendance_date, status))
        db.commit()
        flash("Attendance saved successfully.", "success")
        return redirect(url_for("attendance", subject_id=subject_id, attendance_date=attendance_date))

    existing = {}
    if selected_subject:
        try:
            existing_rows = db.execute(
                "SELECT student_id, status FROM attendance WHERE subject_id = ? AND attendance_date = ?",
                (int(selected_subject), selected_date)
            ).fetchall()
            existing = {row["student_id"]: row["status"] for row in existing_rows}
        except ValueError:
            selected_subject = ""

    return render_template(
        "attendance.html",
        students=students_rows,
        subjects=subjects_rows,
        selected_date=selected_date,
        selected_subject=str(selected_subject),
        existing=existing
    )


@app.route("/reports", methods=["GET", "POST"])
@login_required
def reports():
    db = get_db()
    students_rows = db.execute("SELECT * FROM students ORDER BY roll_no").fetchall()
    subjects_rows = db.execute("SELECT * FROM subjects ORDER BY subject_code").fetchall()
    selected_subject = request.values.get("subject_id", "")
    report_rows = []
    if selected_subject:
        try:
            subject_id = int(selected_subject)
            report_rows = db.execute("""
                SELECT s.id, s.roll_no, s.name, s.department, s.year,
                       COUNT(a.id) AS total_classes,
                       SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                       SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count
                FROM students s
                LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = ?
                GROUP BY s.id
                ORDER BY s.roll_no
            """, (subject_id,)).fetchall()
        except ValueError:
            selected_subject = ""
    return render_template(
        "reports.html",
        students=students_rows,
        subjects=subjects_rows,
        selected_subject=str(selected_subject),
        report_rows=report_rows
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
