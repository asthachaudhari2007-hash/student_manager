from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import db
from app.models.result import Result
from app.models.student import Student
from app.utils.result_extractor import ResultExtractor

results_bp = Blueprint("results", __name__, url_prefix="/results")

EXAM_TYPES = ["Midterm", "Final", "Internal", "Practical", "Assignment"]


def _fill(result):
    """Copy + validate form data onto a Result. Returns error string or None."""
    try:
        result.student_id = int(request.form["student_id"])
        result.subject = request.form["subject"].strip()
        result.exam_type = request.form["exam_type"]
        result.marks = float(request.form["marks"])
        result.max_marks = float(request.form["max_marks"])
        result.semester = int(request.form["semester"])
    except (KeyError, ValueError):
        return "Please fill all fields with valid values."
    if not result.subject:
        return "Subject is required."
    if result.max_marks <= 0 or not (0 <= result.marks <= result.max_marks):
        return "Marks must be between 0 and max marks."
    return None


@results_bp.route("/")
def list_results():
    q = Result.query
    for field in ("semester", "exam_type", "student_id"):
        val = request.args.get(field)
        if val:
            q = q.filter(getattr(Result, field) == val)
    results = q.order_by(Result.id.desc()).all()
    return render_template(
        "results/list.html", results=results,
        students=Student.query.order_by(Student.first_name, Student.last_name).all(),
        exam_types=EXAM_TYPES,
    )


@results_bp.route("/add", methods=["GET", "POST"])
def add_result():
    if request.method == "POST":
        r = Result()
        err = _fill(r)
        if err:
            flash(err, "danger")
        else:
            db.session.add(r)
            db.session.commit()
            flash("Result added.", "success")
            return redirect(url_for("results.list_results"))
    return render_template(
        "results/form.html", result=None, form=request.form,
        students=Student.query.order_by(Student.first_name, Student.last_name).all(), exam_types=EXAM_TYPES,
    )


@results_bp.route("/upload-pdf", methods=["GET", "POST"])
def upload_pdf():
    if request.method == "POST":
        file = request.files.get("pdf")
        try:
            subject = request.form["subject"].strip()
            exam_type = request.form["exam_type"]
            semester = int(request.form["semester"])
            default_max = float(request.form["max_marks"])
        except (KeyError, ValueError):
            flash("Please fill all fields with valid values.", "danger")
            return redirect(url_for("results.upload_pdf"))

        if not subject or default_max <= 0:
            flash("Subject and a positive max marks are required.", "danger")
            return redirect(url_for("results.upload_pdf"))
        if not file or not file.filename.lower().endswith(".pdf"):
            flash("Please choose a PDF file.", "danger")
            return redirect(url_for("results.upload_pdf"))

        students = {s.enrollment_no.strip().upper(): s for s in Student.query.all() if s.enrollment_no}
        extractor = ResultExtractor(s.enrollment_no for s in students.values())

        try:
            rows = extractor.extract(file.stream)
        except Exception as exc:
            flash(f"Could not read the PDF: {exc}", "danger")
            return redirect(url_for("results.upload_pdf"))

        if not rows:
            flash("No student rows found. Check that the PDF contains enrollment numbers that exist in Students.", "warning")
            return redirect(url_for("results.upload_pdf"))

        imported = duplicates = invalid = 0
        seen = set()
        for row in rows:
            student = students.get(row["enrollment_no"].strip().upper())
            max_marks = row["max_marks"] or default_max
            marks = row["marks"]

            if student is None:
                continue
            if max_marks <= 0 or not (0 <= marks <= max_marks):
                invalid += 1
                continue

            key = student.id
            exists = Result.query.filter_by(
                student_id=student.id, subject=subject,
                exam_type=exam_type, semester=semester,
            ).first()
            if key in seen or exists:
                duplicates += 1
                continue
            seen.add(key)

            db.session.add(Result(
                student_id=student.id, subject=subject, exam_type=exam_type,
                semester=semester, marks=marks, max_marks=max_marks,
            ))
            imported += 1

        db.session.commit()
        msg = f"{imported} result(s) imported, {duplicates} duplicate(s) skipped"
        if invalid:
            msg += f", {invalid} row(s) skipped (marks above max marks)"
        flash(msg + ".", "success" if imported else "warning")
        return redirect(url_for("results.list_results"))

    return render_template("results/upload_pdf.html", exam_types=EXAM_TYPES)


@results_bp.route("/<int:id>")
def view_result(id):
    return render_template("results/view.html", result=Result.query.get_or_404(id))


@results_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_result(id):
    r = Result.query.get_or_404(id)
    if request.method == "POST":
        err = _fill(r)
        if err:
            flash(err, "danger")
            db.session.rollback()
        else:
            db.session.commit()
            flash("Result updated.", "success")
            return redirect(url_for("results.list_results"))
    return render_template(
        "results/form.html", result=r, form=request.form,
        students=Student.query.order_by(Student.first_name, Student.last_name).all(), exam_types=EXAM_TYPES,
    )


@results_bp.route("/<int:id>/delete", methods=["POST"])
def delete_result(id):
    r = Result.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    flash("Result deleted.", "success")
    return redirect(url_for("results.list_results"))


@results_bp.route("/report-card/<int:student_id>")
def report_card(student_id):
    student = Student.query.get_or_404(student_id)
    results = (Result.query.filter_by(student_id=student_id)
               .order_by(Result.semester, Result.subject, Result.exam_type).all())
    by_sem = {}
    for r in results:
        by_sem.setdefault(r.semester, []).append(r)
    total = sum(r.marks or 0 for r in results)
    maximum = sum(r.max_marks or 0 for r in results)
    overall = round(total / maximum * 100, 2) if maximum else 0
    return render_template(
        "results/report_card.html", student=student, by_sem=by_sem,
        total=total, maximum=maximum, overall=overall,
    )