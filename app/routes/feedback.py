import csv
import io
import os
from datetime import datetime

from flask import (Blueprint, Response, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from googleapiclient.errors import HttpError

from app import db
from app.models.feedback_form import FeedbackForm
from app.models.student import Student
from app.services import google_forms as gf

feedback_bp = Blueprint("feedback", __name__, url_prefix="/feedback")


def _api_error(exc):
    """Short readable message from a Google API error."""
    if isinstance(exc, HttpError):
        try:
            return exc.error_details[0]["message"] if exc.error_details else exc._get_reason()
        except Exception:
            return str(exc)
    return str(exc)


# ----------------------------------------------------------------------
# Main page
# ----------------------------------------------------------------------
AUTO_CHECK_SECONDS = 30      # don't ask Google more often than this on page loads


def _refresh_all(form_rows):
    """Ask Google for the response count of every form. Returns (failed, last_error)."""
    service = gf.get_service()                      # may raise GoogleNotConnected
    now = datetime.utcnow()
    failed, last_error = 0, None
    for f in form_rows:
        try:
            count, latest = gf.get_response_summary(service, f.form_id)
        except Exception as exc:
            failed += 1
            last_error = _api_error(exc)
            continue
        f.response_count = count
        f.last_response_at = latest
        f.last_checked_at = now
    db.session.commit()
    return failed, last_error


@feedback_bp.route("/")
def index():
    students = Student.query.order_by(Student.first_name, Student.last_name).all()
    connected = gf.has_client_secret() and gf.is_connected()

    # ---- automatic check every time the page is opened ----
    form_rows = FeedbackForm.query.all()
    if connected and form_rows:
        newest = max((f.last_checked_at for f in form_rows if f.last_checked_at), default=None)
        if newest is None or (datetime.utcnow() - newest).total_seconds() > AUTO_CHECK_SECONDS:
            try:
                failed, err = _refresh_all(form_rows)
                if failed:
                    flash(f"{failed} form(s) could not be checked: {err}", "warning")
            except Exception as exc:
                flash(f"Could not check responses automatically: {_api_error(exc)}", "warning")

    forms = {f.student_id: f for f in form_rows}

    total = len(forms)
    filled = sum(1 for f in forms.values() if f.is_filled)
    stats = {
        "students": len(students),
        "forms": total,
        "filled": filled,
        "pending": total - filled,
        "no_form": len(students) - len([s for s in students if s.id in forms]),
        "rate": round(filled / total * 100) if total else 0,
    }
    last_checked = max((f.last_checked_at for f in forms.values() if f.last_checked_at), default=None)

    return render_template(
        "feedback/index.html",
        students=students, forms=forms, stats=stats, last_checked=last_checked,
        connected=connected,
        has_secret=gf.has_client_secret(),
    )


# ----------------------------------------------------------------------
# Google connection (OAuth)
# ----------------------------------------------------------------------
@feedback_bp.route("/google/connect")
def google_connect():
    if not gf.has_client_secret():
        flash("client_secret.json not found in the project folder.", "danger")
        return redirect(url_for("feedback.index"))

    if request.scheme == "http":            # local development only
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

    flow = gf.make_flow(url_for("feedback.google_callback", _external=True))
    auth_url, state = flow.authorization_url(
        access_type="offline", prompt="consent", include_granted_scopes="true"
    )
    session["google_state"] = state
    session["google_code_verifier"] = getattr(flow, "code_verifier", None)
    return redirect(auth_url)


@feedback_bp.route("/google/callback")
def google_callback():
    if request.args.get("error"):
        flash(f"Google sign-in cancelled: {request.args['error']}", "warning")
        return redirect(url_for("feedback.index"))
    if request.args.get("state") != session.get("google_state"):
        flash("Google sign-in failed (state mismatch). Please try again.", "danger")
        return redirect(url_for("feedback.index"))

    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1") if request.scheme == "http" else None
    os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

    flow = gf.make_flow(url_for("feedback.google_callback", _external=True))
    if session.get("google_code_verifier"):
        flow.code_verifier = session["google_code_verifier"]
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as exc:
        flash(f"Google sign-in failed: {exc}", "danger")
        return redirect(url_for("feedback.index"))

    gf.save_credentials(flow.credentials)
    flash("Google account connected.", "success")
    return redirect(url_for("feedback.index"))


@feedback_bp.route("/google/disconnect", methods=["POST"])
def google_disconnect():
    gf.disconnect()
    flash("Google account disconnected.", "info")
    return redirect(url_for("feedback.index"))


# ----------------------------------------------------------------------
# Generate forms
# ----------------------------------------------------------------------
@feedback_bp.route("/generate", methods=["POST"])
def generate():
    title_base = request.form.get("title", "").strip() or "Course Feedback"
    student_id = request.form.get("student_id")

    if student_id:
        targets = Student.query.filter_by(id=int(student_id)).all()
    else:
        existing = {f.student_id for f in FeedbackForm.query.all()}
        targets = [s for s in Student.query.order_by(Student.id).all() if s.id not in existing]

    if not targets:
        flash("Every student already has a feedback form.", "info")
        return redirect(url_for("feedback.index"))

    try:
        service = gf.get_service()
    except gf.GoogleNotConnected:
        flash("Connect your Google account first.", "warning")
        return redirect(url_for("feedback.index"))

    created, errors = 0, []
    for s in targets:
        if FeedbackForm.query.filter_by(student_id=s.id).first():
            continue
        name = f"{s.first_name} {s.last_name}".strip()
        title = f"{title_base} - {name} ({s.enrollment_no})"
        try:
            info = gf.create_feedback_form(service, title)
        except Exception as exc:
            errors.append(f"{name}: {_api_error(exc)}")
            break                      # same cause usually affects every student
        db.session.add(FeedbackForm(
            student_id=s.id, title=title, form_id=info["form_id"],
            responder_url=info["responder_url"], edit_url=info["edit_url"],
            response_count=0,
        ))
        db.session.commit()            # keep progress even if a later one fails
        created += 1

    if created:
        flash(f"{created} feedback form(s) created.", "success")
    if errors:
        flash("Stopped on error - " + errors[0], "danger")
    return redirect(url_for("feedback.index"))


# ----------------------------------------------------------------------
# Check who has filled the form
# ----------------------------------------------------------------------
@feedback_bp.route("/refresh", methods=["POST"])
def refresh():
    form_rows = FeedbackForm.query.all()
    if not form_rows:
        flash("No feedback forms yet.", "info")
        return redirect(url_for("feedback.index"))

    try:
        failed, err = _refresh_all(form_rows)
    except gf.GoogleNotConnected:
        flash("Connect your Google account first.", "warning")
        return redirect(url_for("feedback.index"))
    except Exception as exc:
        flash(f"Could not check responses: {_api_error(exc)}", "danger")
        return redirect(url_for("feedback.index"))

    filled = sum(1 for f in form_rows if f.is_filled)
    flash(f"Updated: {filled} of {len(form_rows)} student(s) have filled the form.", "success")
    if failed:
        flash(f"{failed} form(s) could not be checked: {err}", "warning")
    return redirect(url_for("feedback.index"))


# ----------------------------------------------------------------------
# Small actions
# ----------------------------------------------------------------------
@feedback_bp.route("/<int:id>/sent", methods=["POST"])
def mark_sent(id):
    f = FeedbackForm.query.get_or_404(id)
    f.sent_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("feedback.index"))


@feedback_bp.route("/<int:id>/delete", methods=["POST"])
def delete_form(id):
    """Removes the record here only (the Google Form stays in your Drive)."""
    f = FeedbackForm.query.get_or_404(id)
    db.session.delete(f)
    db.session.commit()
    flash("Feedback record removed. You can generate a new form for this student.", "info")
    return redirect(url_for("feedback.index"))


@feedback_bp.route("/export.csv")
def export_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Enrollment", "Name", "Email", "Form link", "Filled", "Responses", "Last response (UTC)"])
    for f in FeedbackForm.query.all():
        s = f.student
        w.writerow([
            s.enrollment_no, f"{s.first_name} {s.last_name}", s.email, f.responder_url,
            "Yes" if f.is_filled else "No", f.response_count or 0,
            f.last_response_at.strftime("%Y-%m-%d %H:%M") if f.last_response_at else "",
        ])
    return Response(
        out.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback_links.csv"},
    )


# ----------------------------------------------------------------------
# Diagnostics: shows exactly what Google returns for one student's form
# ----------------------------------------------------------------------
@feedback_bp.route("/debug/<int:id>")
def debug_form(id):
    f = FeedbackForm.query.get_or_404(id)
    out = {
        "student": f"{f.student.first_name} {f.student.last_name}",
        "stored_form_id": f.form_id,
        "stored_responder_url": f.responder_url,
        "stored_response_count": f.response_count,
    }
    try:
        service = gf.get_service()
    except gf.GoogleNotConnected:
        out["error"] = "Google not connected"
        return jsonify(out)

    try:
        data = service.forms().responses().list(formId=f.form_id).execute()
        out["google_response_count"] = len(data.get("responses", []))
        out["google_responses"] = [          # answers left out on purpose
            {k: r.get(k) for k in ("responseId", "createTime", "lastSubmittedTime")}
            for r in data.get("responses", [])
        ]
        out["google_raw_keys"] = sorted(data.keys())
    except Exception as exc:
        out["responses_error"] = _api_error(exc)

    try:
        form = service.forms().get(formId=f.form_id).execute()
        out["google_form"] = {k: form.get(k) for k in ("formId", "responderUri", "publishSettings")}
        out["google_form"]["title"] = form.get("info", {}).get("title")
        out["google_form"]["question_count"] = len(form.get("items", []))
    except Exception as exc:
        out["form_error"] = _api_error(exc)

    return jsonify(out)