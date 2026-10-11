from app import db


class Student(db.Model):
    __tablename__ = "students"

    # ======================================================
    # Primary Key
    # ======================================================

    id = db.Column(db.Integer, primary_key=True)

    # ======================================================
    # Academic Information
    # ======================================================

    enrollment_no = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    roll_no = db.Column(
        db.String(20),
        unique=True,
        nullable=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=True
    )

    gender = db.Column(
        db.String(10),
        nullable=True
    )

    # ======================================================
    # Contact Information
    # ======================================================

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True
    )

    phone = db.Column(
        db.String(15),
        nullable=True
    )

    # ======================================================
    # Academic Details
    # ======================================================

    department = db.Column(
        db.String(100),
        nullable=False
    )

    semester = db.Column(
        db.Integer,
        nullable=False
    )

    section = db.Column(
        db.String(10),
        nullable=True
    )

    admission_year = db.Column(
        db.Integer,
        nullable=False
    )

    # ======================================================
    # Student Status
    # ======================================================

    status = db.Column(
        db.String(20),
        default="Active",
        nullable=False
    )

    # ======================================================
    # Timestamps
    # ======================================================

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # ======================================================
    # Relationships
    # ======================================================

    attendance = db.relationship(
        "Attendance",
        backref="student",
        lazy=True,
        cascade="all, delete-orphan"
    )

    results = db.relationship(
        "Result",
        backref="student",
        lazy=True,
        cascade="all, delete-orphan"
    )

    feedback = db.relationship(
        "Feedback",
        backref="student",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # ======================================================
    # Helper Property
    # ======================================================

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    # ======================================================
    # String Representation
    # ======================================================

    def __repr__(self):
        return f"<Student {self.enrollment_no} - {self.full_name}>"