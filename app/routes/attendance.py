"""
attendance.py
----------------------------------------------------
Attendance Management Routes

CampusFlow AI
"""

import os
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)

from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.student import Student
from app.models.attendance import Attendance
from app.forms.attendance_form import AttendanceForm
from app.utils.file_utils import allowed_pdf

# AI Modules
from app.ai.pdf_loader import PDFLoader
from app.ai.attendance_extractor import AttendanceExtractor


attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/attendance"
)


# ==========================================================
# Attendance List
# ==========================================================

@attendance_bp.route("/")
def attendance_list():

    attendance = Attendance.query.order_by(
        Attendance.date.desc()
    ).all()

    return render_template(
        "attendance/attendance.html",
        attendance=attendance
    )


# ==========================================================
# Add Attendance
# ==========================================================

@attendance_bp.route("/add", methods=["GET", "POST"])
def add_attendance():

    students = Student.query.order_by(
        Student.first_name
    ).all()

    if not students:

        flash(
            "Please add students before marking attendance.",
            "warning"
        )

        return redirect(
            url_for("students.add_student")
        )

    form = AttendanceForm()

    form.student_id.choices = [
        (
            student.id,
            f"{student.enrollment_no} - {student.full_name}"
        )
        for student in students
    ]

    if form.validate_on_submit():

        attendance = Attendance(
            student_id=form.student_id.data,
            subject=form.subject.data.strip(),
            date=form.date.data,
            status=form.status.data,
            remarks=form.remarks.data.strip()
            if form.remarks.data else ""
        )

        try:

            db.session.add(attendance)
            db.session.commit()

            flash(
                "Attendance marked successfully.",
                "success"
            )

            return redirect(
                url_for("attendance.attendance_list")
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "This student already has an attendance record "
                "for that subject on that date.",
                "danger"
            )

        except Exception as e:

            db.session.rollback()
            current_app.logger.exception(e)

            flash(
                "Unable to save attendance.",
                "danger"
            )

    return render_template(
        "attendance/attendance_form.html",
        form=form,
        edit=False
    )


# ==========================================================
# Edit Attendance
# ==========================================================

@attendance_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_attendance(id):

    attendance = Attendance.query.get_or_404(id)

    form = AttendanceForm(obj=attendance)

    students = Student.query.order_by(
        Student.first_name
    ).all()

    form.student_id.choices = [
        (
            student.id,
            f"{student.enrollment_no} - {student.full_name}"
        )
        for student in students
    ]

    if form.validate_on_submit():

        attendance.student_id = form.student_id.data
        attendance.subject = form.subject.data.strip()
        attendance.date = form.date.data
        attendance.status = form.status.data
        attendance.remarks = (
            form.remarks.data.strip()
            if form.remarks.data else ""
        )

        try:

            db.session.commit()

            flash(
                "Attendance updated successfully.",
                "success"
            )

            return redirect(
                url_for("attendance.attendance_list")
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Another attendance record already exists for "
                "this student, subject and date.",
                "danger"
            )

        except Exception as e:

            db.session.rollback()

            current_app.logger.exception(e)

            flash(
                "Unable to update attendance.",
                "danger"
            )

    return render_template(
        "attendance/attendance_form.html",
        form=form,
        attendance=attendance,
        edit=True
    )


# ==========================================================
# Delete Attendance
# ==========================================================

@attendance_bp.route("/delete/<int:id>", methods=["POST"])
def delete_attendance(id):

    attendance = Attendance.query.get_or_404(id)

    try:

        db.session.delete(attendance)
        db.session.commit()

        flash(
            "Attendance deleted successfully.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(e)

        flash(
            "Unable to delete attendance.",
            "danger"
        )

    return redirect(
        url_for("attendance.attendance_list")
    )


# ==========================================================
# Delete All Attendance
# ==========================================================

@attendance_bp.route("/delete-all", methods=["POST"])
def delete_all_attendance():

    try:

        total = Attendance.query.count()

        if total == 0:

            flash(
                "No attendance records found.",
                "warning"
            )

            return redirect(
                url_for("attendance.attendance_list")
            )

        Attendance.query.delete()

        db.session.commit()

        flash(
            f"{total} attendance records deleted successfully.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(e)

        flash(
            "Unable to delete attendance records.",
            "danger"
        )

    return redirect(
        url_for("attendance.attendance_list")
    )


# ==========================================================
# Upload Attendance PDF
# ==========================================================

@attendance_bp.route("/upload-pdf", methods=["GET", "POST"])
def upload_attendance_pdf():

    if request.method == "POST":

        subject = request.form.get("subject", "").strip()
        date_str = request.form.get("date", "").strip()

        if not subject:

            flash(
                "Please enter a subject.",
                "danger",
            )

            return redirect(request.url)

        if not date_str:

            flash(
                "Please select a date.",
                "danger",
            )

            return redirect(request.url)

        try:
            attendance_date = datetime.strptime(
                date_str, "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid date format.",
                "danger",
            )

            return redirect(request.url)

        if "pdf_file" not in request.files:

            flash(
                "Please choose a PDF file.",
                "danger",
            )

            return redirect(request.url)

        pdf = request.files["pdf_file"]

        if pdf.filename == "":

            flash(
                "Please choose a PDF file.",
                "warning",
            )

            return redirect(request.url)

        if not allowed_pdf(pdf.filename):

            flash(
                "Only PDF files are allowed.",
                "danger",
            )

            return redirect(request.url)

        pdf_path = None

        try:

            filename = secure_filename(pdf.filename)

            pdf_path = os.path.join(
                current_app.config["ATTENDANCE_PDF_FOLDER"],
                filename,
            )

            pdf.save(pdf_path)

            # ---------------------------------------
            # Read PDF
            # ---------------------------------------

            loader = PDFLoader()

            documents = loader.load_pdf(pdf_path)

            if not documents:

                flash(
                    "No readable text found in PDF.",
                    "warning",
                )

                return redirect(request.url)

            full_text = "\n".join(
                doc.page_content
                for doc in documents
            )

            extractor = AttendanceExtractor()

            records = extractor.extract_attendance(
                full_text
            )

            if not records:

                flash(
                    "No attendance rows detected.",
                    "warning",
                )

                return redirect(
                    url_for("attendance.attendance_list")
                )

            added = 0
            skipped_duplicate = 0
            skipped_unmatched = 0

            for r in records:

                enrollment = r.get("enrollment_no", "")
                status = r.get("status", "")

                student = Student.query.filter_by(
                    enrollment_no=enrollment
                ).first()

                if not student:

                    skipped_unmatched += 1
                    continue

                exists = Attendance.query.filter_by(
                    student_id=student.id,
                    subject=subject,
                    date=attendance_date,
                ).first()

                if exists:

                    skipped_duplicate += 1
                    continue

                attendance = Attendance(
                    student_id=student.id,
                    subject=subject,
                    date=attendance_date,
                    status=status,
                    remarks="",
                )

                db.session.add(attendance)

                added += 1

            db.session.commit()

            flash(
                f"{added} attendance records imported successfully. "
                f"{skipped_duplicate} duplicate record(s) skipped. "
                f"{skipped_unmatched} unmatched enrollment number(s) skipped.",
                "success",
            )

            return redirect(
                url_for("attendance.attendance_list")
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Duplicate attendance records found.",
                "danger",
            )

        except Exception as e:

            db.session.rollback()

            current_app.logger.exception(e)

            flash(
                f"Import Error: {str(e)}",
                "danger",
            )

        finally:

            if pdf_path and os.path.exists(pdf_path):

                try:
                    os.remove(pdf_path)
                except Exception:
                    pass

    return render_template(
        "attendance/upload_pdf.html"
    )


# ==========================================================
# View Attendance
# ==========================================================

@attendance_bp.route("/view/<int:id>")
def view_attendance(id):

    attendance = Attendance.query.get_or_404(id)

    return render_template(
        "attendance/attendance_view.html",
        attendance=attendance
    )