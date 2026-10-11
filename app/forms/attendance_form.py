"""
attendance_form.py
-------------------------------------------------------
Attendance Form

Used for adding and editing attendance records.

CampusFlow AI
"""

from flask_wtf import FlaskForm

from wtforms import (
    SelectField,
    StringField,
    DateField,
    TextAreaField,
    SubmitField,
)

from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
)


class AttendanceForm(FlaskForm):

    # ==========================================
    # Student
    # ==========================================

    student_id = SelectField(
        "Student",
        coerce=int,
        validators=[DataRequired()],
    )

    # ==========================================
    # Subject
    # ==========================================

    subject = StringField(
        "Subject",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )

    # ==========================================
    # Attendance Date
    # ==========================================

    date = DateField(
        "Attendance Date",
        format="%Y-%m-%d",
        validators=[DataRequired()],
        render_kw={"type": "date"},
    )

    # ==========================================
    # Status
    # ==========================================

    status = SelectField(
        "Status",
        choices=[
            ("Present", "Present"),
            ("Absent", "Absent"),
        ],
        validators=[DataRequired()],
    )

    # ==========================================
    # Remarks
    # ==========================================

    remarks = TextAreaField(
        "Remarks",
        validators=[
            Optional(),
            Length(max=300),
        ],
        render_kw={
            "rows": 3,
            "placeholder": "Optional remarks...",
        },
    )

    # ==========================================
    # Submit
    # ==========================================

    submit = SubmitField("Save Attendance")