"""
students.py
----------------------------------------------------
Student Management Routes

CampusFlow AI
"""

import os

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
from app.forms.student_form import StudentForm
from app.utils.file_utils import allowed_pdf

# AI Modules
from app.ai.pdf_loader import PDFLoader
from app.ai.student_extractor import StudentExtractor


students_bp = Blueprint(
    "students",
    __name__,
    url_prefix="/students",
)


# ==========================================================
# Student List
# ==========================================================

@students_bp.route("/")
def student_list():

    students = Student.query.order_by(
        Student.id.desc()
    ).all()

    return render_template(
        "students/students.html",
        students=students,
    )


# ==========================================================
# Add Student
# ==========================================================

@students_bp.route("/add", methods=["GET", "POST"])
def add_student():

    form = StudentForm()

    if form.validate_on_submit():

        student = Student(

            enrollment_no=form.enrollment_no.data.strip(),

            roll_no=form.roll_no.data.strip()
            if form.roll_no.data
            else "",

            first_name=form.first_name.data.strip(),

            last_name=form.last_name.data.strip()
            if form.last_name.data
            else "",

            email=form.email.data.strip()
            if form.email.data
            else "",

            phone=form.phone.data.strip()
            if form.phone.data
            else "",

            gender=form.gender.data,

            department=form.department.data.strip(),

            semester=form.semester.data,

            section=form.section.data.strip()
            if form.section.data
            else "",

            admission_year=form.admission_year.data,
        )

        try:

            db.session.add(student)
            db.session.commit()

            flash(
                "Student added successfully.",
                "success",
            )

            return redirect(
                url_for("students.student_list")
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Enrollment Number, Roll Number or Email already exists.",
                "danger",
            )

        except Exception as e:

            db.session.rollback()

            current_app.logger.exception(e)

            flash(
                "Unable to add student.",
                "danger",
            )

    return render_template(
        "students/student_form.html",
        form=form,
        edit=False,
    )


# ==========================================================
# Edit Student
# ==========================================================

@students_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    student = Student.query.get_or_404(id)

    form = StudentForm(obj=student)

    if form.validate_on_submit():

        student.enrollment_no = form.enrollment_no.data.strip()

        student.roll_no = form.roll_no.data.strip() \
            if form.roll_no.data else ""

        student.first_name = form.first_name.data.strip()

        student.last_name = form.last_name.data.strip() \
            if form.last_name.data else ""

        student.email = form.email.data.strip() \
            if form.email.data else ""

        student.phone = form.phone.data.strip() \
            if form.phone.data else ""

        student.gender = form.gender.data

        student.department = form.department.data.strip()

        student.semester = form.semester.data

        student.section = form.section.data.strip() \
            if form.section.data else ""

        student.admission_year = form.admission_year.data

        try:

            db.session.commit()

            flash(
                "Student updated successfully.",
                "success",
            )

            return redirect(
                url_for("students.student_list")
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Enrollment Number, Roll Number or Email already exists.",
                "danger",
            )

        except Exception as e:

            db.session.rollback()

            current_app.logger.exception(e)

            flash(
                "Unable to update student.",
                "danger",
            )

    return render_template(
        "students/student_form.html",
        form=form,
        edit=True,
        student=student,
    )


# ==========================================================
# Delete Student
# ==========================================================

@students_bp.route("/delete/<int:id>", methods=["POST"])
def delete_student(id):

    student = Student.query.get_or_404(id)

    try:
        db.session.delete(student)
        db.session.commit()

        flash(
            "Student deleted successfully.",
            "success",
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(e)

        flash(
            "Unable to delete student.",
            "danger",
        )

    return redirect(
        url_for("students.student_list")
    )


# ==========================================================
# Delete All Students
# ==========================================================

@students_bp.route("/delete-all", methods=["POST"])
def delete_all_students():

    try:

        total = Student.query.count()

        if total == 0:

            flash(
                "No students found.",
                "warning",
            )

            return redirect(
                url_for("students.student_list")
            )

        Student.query.delete()

        db.session.commit()

        flash(
            f"{total} students deleted successfully.",
            "success",
        )

    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(e)

        flash(
            "Unable to delete students.",
            "danger",
        )

    return redirect(
        url_for("students.student_list")
    )


# ==========================================================
# Upload Students PDF
# ==========================================================

@students_bp.route("/upload-pdf", methods=["GET", "POST"])
def upload_pdf():

    if request.method == "POST":

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
                current_app.config["STUDENT_PDF_FOLDER"],
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

            extractor = StudentExtractor()

            students = extractor.extract_students(
                full_text
            )

            students = extractor.get_valid_students(
                students
            )

            if not students:

                flash(
                    "No students detected.",
                    "warning",
                )

                return redirect(
                    url_for("students.student_list")
                )

            added = 0
            skipped = 0

            for s in students:

                enrollment = str(
                    s.get("enrollment_no", "")
                ).strip()

                email = str(
                    s.get("email", "")
                ).strip()

                if not enrollment:

                    skipped += 1
                    continue

                exists = Student.query.filter(
                    (Student.enrollment_no == enrollment)
                    |
                    (Student.email == email)
                ).first()

                if exists:

                    skipped += 1
                    continue

                semester = int(
                    s.get("semester", 0)
                ) if str(
                    s.get("semester", "")
                ).isdigit() else 0

                admission_year = int(
                    s.get("admission_year", 0)
                ) if str(
                    s.get("admission_year", "")
                ).isdigit() else 0

                student = Student(

                    enrollment_no=enrollment,

                    roll_no=str(
                        s.get("roll_no", "")
                    ).strip(),

                    first_name=str(
                        s.get("first_name", "")
                    ).strip(),

                    last_name=str(
                        s.get("last_name", "")
                    ).strip(),

                    email=email,

                    phone=str(
                        s.get("phone", "")
                    ).strip(),

                    gender=str(
                        s.get("gender", "")
                    ).strip(),

                    department=str(
                        s.get("department", "")
                    ).strip(),

                    semester=semester,

                    section=str(
                        s.get("section", "")
                    ).strip(),

                    admission_year=admission_year,

                )

                db.session.add(student)

                added += 1

            db.session.commit()

            flash(
                f"{added} students imported successfully. "
                f"{skipped} duplicate/invalid records skipped.",
                "success",
            )

            return redirect(
                url_for("students.student_list")
            )

        except IntegrityError:

            db.session.rollback()

            flash(
                "Duplicate student records found.",
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
        "students/upload_pdf.html"
    )


# ==========================================================
# View Student
# ==========================================================

@students_bp.route("/view/<int:id>")
def view_student(id):

    student = Student.query.get_or_404(id)

    return render_template(
        "students/student_view.html",
        student=student,
    )


# ==========================================================
# Search Students
# ==========================================================

@students_bp.route("/search")
def search_students():

    keyword = request.args.get("q", "").strip()

    if keyword:

        students = Student.query.filter(
            (Student.first_name.ilike(f"%{keyword}%")) |
            (Student.last_name.ilike(f"%{keyword}%")) |
            (Student.enrollment_no.ilike(f"%{keyword}%")) |
            (Student.roll_no.ilike(f"%{keyword}%")) |
            (Student.department.ilike(f"%{keyword}%"))
        ).order_by(
            Student.first_name
        ).all()

    else:

        students = Student.query.order_by(
            Student.first_name
        ).all()

    return render_template(
        "students/students.html",
        students=students,
        keyword=keyword,
    )


# ==========================================================
# Student Profile
# ==========================================================

@students_bp.route("/profile/<int:id>")
def student_profile(id):

    student = Student.query.get_or_404(id)

    return render_template(
        "students/profile.html",
        student=student,
    )