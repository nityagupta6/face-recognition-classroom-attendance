from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_wtf.file import FileField, FileAllowed
from flask import request


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    enrollment_number = StringField('Enrollment No.')
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message="Passwords must match.")])
    role = SelectField(
        'Role', choices=[('student', 'Student'), ('professor', 'Professor')])
    images = FileField('Upload Images', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])

    submit = SubmitField('Register')

    def validate(self, **kwargs):
        if not super(RegistrationForm, self).validate(**kwargs):
            return False

        # Conditional validation for students
        if self.role.data == 'student':
            if not self.enrollment_number.data:
                self.enrollment_number.errors.append(
                    'Enrollment number is required for students.')
                return False
            if len(self.enrollment_number.data) != 10:
                self.enrollment_number.errors.append(
                    'Enrollment number must be exactly 10 characters.')
                return False
            if not self.images.data or len(request.files.getlist("images")) != 5:
                self.images.errors.append(
                    'Students must upload exactly 5 images.')
                return False

        # Conditional validation for professors (no enrollment number required)
        elif self.role.data == 'professor':
            if self.enrollment_number.data:
                self.enrollment_number.errors.append(
                    'Enrollment number is not required for professors.')
                return False
            if not self.images.data or len(request.files.getlist("images")) != 1:
                self.images.errors.append(
                    'Professors must upload exactly 1 image.')
                return False

        return True


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ScheduleClassForm(FlaskForm):
    course = SelectField('Course', choices=[])  # Populate dynamically in route
    date = StringField('Date', validators=[DataRequired()])
    submit = SubmitField('Schedule')
