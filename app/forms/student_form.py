from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    IntegerField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    Email,
    Optional
)


class StudentForm(FlaskForm):

    enrollment_no = StringField(
        "Enrollment Number",
        validators=[DataRequired()]
    )

    roll_no = StringField(
        "Roll Number",
        validators=[Optional()]
    )

    first_name = StringField(
        "First Name",
        validators=[DataRequired()]
    )

    last_name = StringField(
        "Last Name",
        validators=[Optional()]
    )

    email = StringField(
        "Email",
        validators=[Optional(), Email()]
    )

    phone = StringField(
        "Phone",
        validators=[Optional()]
    )

    gender = StringField(
        "Gender",
        validators=[Optional()]
    )

    department = StringField(
        "Department",
        validators=[DataRequired()]
    )

    semester = IntegerField(
        "Semester",
        validators=[DataRequired()]
    )

    section = StringField(
        "Section",
        validators=[Optional()]
    )

    admission_year = IntegerField(
        "Admission Year",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Student")