from app import db


class FeedbackForm(db.Model):
    """One Google Form per student, plus how many responses it has received."""

    __tablename__ = "feedback_forms"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    title = db.Column(db.String(200))
    form_id = db.Column(db.String(200), unique=True, nullable=False)   # Google's form id
    responder_url = db.Column(db.String(500))                           # link to send to the student
    edit_url = db.Column(db.String(500))                                # link for the teacher

    response_count = db.Column(db.Integer, default=0)
    last_response_at = db.Column(db.DateTime)      # when the student last submitted
    last_checked_at = db.Column(db.DateTime)       # when we last asked Google
    sent_at = db.Column(db.DateTime)               # teacher clicked "Mark as sent"
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    student = db.relationship("Student")

    @property
    def is_filled(self):
        return (self.response_count or 0) > 0
