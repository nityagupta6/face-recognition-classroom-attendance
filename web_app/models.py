from datetime import datetime
from web_app.extensions import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func

# Association table for many-to-many relationship between User and Course
enrollment_table = db.Table(
    'enrollment',
    db.Column('user_id', db.Integer, db.ForeignKey(
        'user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey(
        'course.id'), primary_key=True),
    extend_existing=True  # Allow redefinition if the table already exists
)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Path or name of the file
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Image(User ID: {self.user_id}, Filename: {self.filename})"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    enrollment_number = db.Column(db.String(10), unique=True, nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    role = db.Column(db.String(10), nullable=False)

    attendance_records = db.relationship(
        'Attendance', backref='student', lazy=True)

    # Relationship to fetch courses for a student
    courses = db.relationship(
        'Course', secondary=enrollment_table, backref=db.backref('students', lazy=True), lazy=True
    )
    images = db.relationship('Image', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    professor_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Link to attendance records for this course
    attendance_records = db.relationship(
        'Attendance', backref='course', lazy=True)

    def __repr__(self):
        return f"Course('{self.name}', Professor ID: {self.professor_id})"


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=func.current_date())
    status = db.Column(db.String(10), nullable=False)  # "Present" or "Absent"
    student_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey(
        'course.id'), nullable=False)

    def __repr__(self):
        return f"Attendance(Student ID: {self.student_id}, Course ID: {self.course_id}, Status: {self.status})"


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # Optional: location of the classroom
    location = db.Column(db.String(100), nullable=True)
    # Optional: capacity of the classroom
    capacity = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"Classroom('{self.name}', Capacity: {self.capacity}, Location: {self.location}')"
