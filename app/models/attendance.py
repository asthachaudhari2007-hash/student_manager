from datetime import date

from app import db


class Attendance(db.Model):

    __tablename__ = "attendance"

    # ======================================================
    # Table Constraints
    # ======================================================
    # Prevents marking the same student for the same subject
    # on the same date more than once.

    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "subject", "date",
            name="uq_attendance_student_subject_date"
        ),
    )

    # ======================================================
    # Primary Key
    # ======================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ======================================================
    # Foreign Key
    # ======================================================

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    # ======================================================
    # Attendance Information
    # ======================================================
    # NOTE: the .student attribute is provided automatically by
    # Student.attendance's backref="student" in student.py.
    # Do NOT redefine it here — that would raise a SQLAlchemy
    # ArgumentError for a duplicate 'student' property.
    # ======================================================

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    date = db.Column(
        db.Date,
        default=date.today,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Present"
    )

    remarks = db.Column(
        db.String(255),
        nullable=True
    )

    # ======================================================
    # Timestamp
    # ======================================================

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # ======================================================
    # String Representation
    # ======================================================

    def __repr__(self):
        return f"<Attendance StudentID={self.student_id} Date={self.date} Status={self.status}>"