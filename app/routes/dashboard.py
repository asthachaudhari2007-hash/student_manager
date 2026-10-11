from datetime import date

from flask import Blueprint, render_template
from sqlalchemy import func, case

from app import db
from app.models.student import Student
from app.models.attendance import Attendance
from app.models.result import Result

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():
    today = date.today()

    total_students = Student.query.count()
    total_attendance = Attendance.query.count()
    total_results = Result.query.count()

    present_today = Attendance.query.filter_by(date=today, status="Present").count()
    absent_today = Attendance.query.filter_by(date=today, status="Absent").count()
    attendance_today = Attendance.query.filter_by(date=today).count()
    attendance_percentage = round(present_today / total_students * 100, 2) if total_students else 0

    # ---- Attendance overall (all time) ----
    present_all = Attendance.query.filter_by(status="Present").count()
    absent_all = Attendance.query.filter_by(status="Absent").count()

    # ---- Attendance % per subject ----
    rows = (db.session.query(
                Attendance.subject,
                func.count(Attendance.id),
                func.sum(case((Attendance.status == "Present", 1), else_=0)))
            .group_by(Attendance.subject).all())
    subj_labels = [r[0] or "N/A" for r in rows]
    subj_pct = [round((r[2] or 0) / r[1] * 100, 1) if r[1] else 0 for r in rows]

    # ---- Result trends ----
    pct_expr = func.avg(Result.marks * 100.0 / Result.max_marks)
    by_exam = (db.session.query(Result.exam_type, pct_expr)
               .filter(Result.max_marks > 0).group_by(Result.exam_type).all())
    by_subject = (db.session.query(Result.subject, pct_expr)
                  .filter(Result.max_marks > 0).group_by(Result.subject).all())

    chart_data = {
        "attendance": {"present": present_all, "absent": absent_all},
        "attendance_subject": {"labels": subj_labels, "values": subj_pct},
        "results_exam": {"labels": [r[0] or "N/A" for r in by_exam],
                         "values": [round(r[1] or 0, 1) for r in by_exam]},
        "results_subject": {"labels": [r[0] or "N/A" for r in by_subject],
                            "values": [round(r[1] or 0, 1) for r in by_subject]},
    }

    return render_template(
        "dashboard/dashboard.html",
        total_students=total_students,
        total_attendance=total_attendance,
        total_results=total_results,
        attendance_today=attendance_today,
        present_today=present_today,
        absent_today=absent_today,
        attendance_percentage=attendance_percentage,
        recent_students=Student.query.order_by(Student.id.desc()).limit(5).all(),
        recent_attendance=Attendance.query.order_by(Attendance.id.desc()).limit(5).all(),
        recent_results=Result.query.order_by(Result.id.desc()).limit(5).all(),
        chart_data=chart_data,
    )


@dashboard_bp.route("/students")
def students():
    return render_template("students/students.html")


@dashboard_bp.route("/attendance")
def attendance():
    return render_template("attendance/attendance.html")


# NOTE: the old "/results" placeholder is removed; results_bp now owns /results/

# NOTE: the old "/feedback" placeholder is removed; feedback_bp now owns /feedback/