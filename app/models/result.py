from app import db


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject = db.Column(db.String(100))
    exam_type = db.Column(db.String(50))   # Midterm / Final
    marks = db.Column(db.Float)
    max_marks = db.Column(db.Float)
    semester = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    

    @property
    def percentage(self):
        if not self.max_marks:
            return 0.0
        return round((self.marks or 0) / self.max_marks * 100, 2)

    @property
    def grade(self):
        p = self.percentage
        if p >= 90: return "A+"
        if p >= 80: return "A"
        if p >= 70: return "B"
        if p >= 60: return "C"
        if p >= 50: return "D"
        return "F"