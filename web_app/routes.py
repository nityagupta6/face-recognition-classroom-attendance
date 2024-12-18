from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from web_app.extensions import db, bcrypt  # Import from extensions
from web_app.forms import RegistrationForm, LoginForm
from web_app.models import User, Attendance, Course, Classroom
import os
from web_app.config import Config
from werkzeug.utils import secure_filename
from web_app.faceDetection.mtcnn_webcam import start_face_detection, stop_face_detection


# Blueprint for routes
app_routes = Blueprint('app_routes', __name__)

# Define routes here...

# Homepage


@app_routes.route('/')
@app_routes.route('/home')
def home():
    return render_template('home.html')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Registration route where file upload is handled


@app_routes.route('/register', methods=['GET', 'POST'])
def register():
    print("Registration route hit")  # Debugging: Route hit

    if current_user.is_authenticated:
        print(
            f"User {current_user.name} is already authenticated with role {current_user.role}")
        return redirect(url_for('app_routes.student_dashboard' if current_user.role == 'student' else 'app_routes.professor_dashboard'))

    form = RegistrationForm()
    print("Form instantiated")  # Debugging: Form instantiated

    if form.validate_on_submit():
        print("Form validated successfully")  # Debugging: Form validated

        # Check for existing user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            # Debugging: Existing email
            print(f"User with email {form.email.data} already exists")
            flash(
                'Email already registered. Please choose a different one or log in.', 'danger')
            return redirect(url_for('app_routes.register'))

        # Hash the password for secure storage
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        # Debugging: Password hashed
        print(f"Password hashed for user {form.name.data}")

        # If the user is a student, enrollment_number is required
        if form.role.data == 'student':
            if not form.enrollment_number.data:
                flash('Enrollment number is required for students', 'danger')
                return redirect(url_for('app_routes.register'))

        # Create a new user object (student or professor)
        user = User(
            name=form.name.data,  # Storing full name
            # Enrollment number only for students
            enrollment_number=form.enrollment_number.data if form.role.data == 'student' else None,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        # Debugging: User added to DB
        print(
            f"User {form.name.data} with role {form.role.data} added to the database")

        # If the user is a student, handle image uploads
        if form.role.data == 'student' and 'images' in request.files:
            images = request.files.getlist('images')
            # Debugging: Images received
            print(f"Student role selected, {len(images)} images received")

            if len(images) < 5:
                # Debugging: Not enough images
                print("Fewer than 5 images uploaded for student")
                flash('Please upload at least 5 images for face recognition.', 'danger')
                return redirect(url_for('app_routes.register'))

            for image in images:
                if image.filename == '':
                    print("No image selected")  # Debugging: No image selected
                    flash('No image selected', 'danger')
                    return redirect(url_for('app_routes.register'))

                if not allowed_file(image.filename):
                    # Debugging: Invalid file type
                    print(f"Invalid file type: {image.filename}")
                    flash(
                        'Only image files (png, jpg, jpeg, gif) are allowed.', 'danger')
                    return redirect(url_for('app_routes.register'))

                # Secure the filename and save the image to the uploads folder
                filename = secure_filename(image.filename)
                image.save(os.path.join(Config.UPLOAD_FOLDER, filename))
                # Debugging: Image saved
                print(f"Image {filename} saved for student")

            flash('Registration successful! Images uploaded.', 'success')

        # For professors, handle the single image upload
        elif form.role.data == 'professor' and 'images' in request.files:
            images = request.files.getlist('images')
            # Debugging: Image received
            print(f"Professor role selected, {len(images)} image(s) received")

            if len(images) != 1:
                # Debugging: Wrong number of images
                print("Incorrect number of images uploaded for professor")
                flash('Professors must upload exactly 1 image.', 'danger')
                return redirect(url_for('app_routes.register'))

            image = images[0]  # Since professor uploads only one image
            if not allowed_file(image.filename):
                # Debugging: Invalid file type
                print(f"Invalid file type: {image.filename}")
                flash('Only image files (png, jpg, jpeg, gif) are allowed.', 'danger')
                return redirect(url_for('app_routes.register'))

            filename = secure_filename(image.filename)
            image.save(os.path.join(Config.UPLOAD_FOLDER, filename))
            # Debugging: Image saved
            print(f"Image {filename} saved for professor")

            flash('Registration successful! Image uploaded.', 'success')

        else:
            # Debugging: No images uploaded
            print("No images uploaded, proceeding without image upload")
            flash('Registration successful!', 'success')

        return redirect(url_for('app_routes.login'))

    print("Form did not validate")  # Debugging: Form validation failed
    print(form.errors)  # Debugging: Form errors
    return render_template('register.html', form=form)


# Login route


@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('app_routes.student_dashboard' if current_user.role == 'student' else 'app_routes.professor_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('app_routes.student_dashboard' if user.role == 'student' else 'app_routes.professor_dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html', form=form)

# Logout route


@app_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!', 'info')
    return redirect(url_for('app_routes.home'))


# Student Dashboard route

@app_routes.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    # Fetch all courses the student has ever attended
    courses = db.session.query(Course).join(Attendance).filter(
        Attendance.student_id == current_user.id).all()

    attendance_summary = []
    for course in courses:
        total_classes = db.session.query(Attendance).filter_by(
            course_id=course.id).count()

        attended_classes = db.session.query(Attendance).filter_by(
            course_id=course.id, student_id=current_user.id, status='Present').count()

        missed_classes = total_classes - attended_classes  # Calculate missed classes

        if total_classes > 0:
            attendance_percentage = (attended_classes / total_classes) * 100
        else:
            attendance_percentage = 0

        attendance_summary.append({
            'course': {
                'id': course.id,
                'name': course.name
            },
            'attended': attended_classes,
            'missed': missed_classes,
            'percentage': attendance_percentage
        })

    return render_template('student_dashboard.html', attendance_summary=attendance_summary)

# Route for viewing detailed attendance of a particular course


@app_routes.route('/course/<int:course_id>/attendance')
@login_required
def view_attendance(course_id):
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    course = Course.query.get_or_404(course_id)

    # Fetch attendance records for this course for the current user
    attendance_records = Attendance.query.filter_by(
        course_id=course_id, student_id=current_user.id).all()

    return render_template('course_attendance.html', course=course, attendance_records=attendance_records)


# Professor Dashboard

@app_routes.route('/professor_dashboard')
@login_required
def professor_dashboard():
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    # Fetch courses and classrooms from the database
    courses = Course.query.filter_by(professor_id=current_user.id).all()
    classrooms = Classroom.query.all()  # Fetch all classrooms

    return render_template('professor_dashboard.html', courses=courses, classrooms=classrooms)


# Route to schedule a class

@app_routes.route('/schedule_class', methods=['POST'])
@login_required
def schedule_class():
    # Ensure the user is a professor
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    # Get the selected course ID, classroom ID, and date from the form
    course_id = request.form.get('course')
    classroom_id = request.form.get('classroom')
    date = request.form.get('date')

    if not course_id or not classroom_id or not date:
        flash('All fields are required to schedule a class.', 'danger')
        return redirect(url_for('app_routes.professor_dashboard'))

    if course_id:
        # Trigger the face detection for the selected course
        start_face_detection(int(course_id))

        # Flash a success message
        flash(
            f'Class scheduled in classroom {classroom_id} for {date}!', 'success')

        # Redirect to the class details page for ending attendance
        return redirect(url_for('app_routes.view_class_details', course_id=course_id, date=date))

    flash('Error: Course ID is missing.', 'danger')
    return redirect(url_for('app_routes.professor_dashboard'))


@app_routes.route('/class_details/<int:course_id>/<date>', methods=['GET'])
@login_required
def view_class_details(course_id, date):
    # Ensure the user is a professor
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    # Retrieve the course details and classroom details (optional)
    course = Course.query.get(course_id)
    classroom = Classroom.query.filter_by(
        id=request.args.get('classroom')).first()

    if not course:
        flash('Course not found', 'danger')
        return redirect(url_for('app_routes.professor_dashboard'))

    # Pass course and other relevant details to the template
    return render_template('class_details.html', course=course, date=date, classroom=classroom)


# Route to end Attendance (Professor only)

@app_routes.route('/end_attendance/<int:course_id>', methods=['POST'])
@login_required
def end_attendance(course_id):
    # Ensure the user is a professor
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    # Stop the face detection process and update attendance
    # Pass course_id to stop and update attendance
    stop_face_detection(course_id)

    flash(f'Attendance ended for course {course_id}', 'success')
    return redirect(url_for('app_routes.professor_dashboard'))


# Route to view attendance report (Professor only)
@app_routes.route('/view_report', methods=['POST'])
@login_required
def view_report():
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    course_id = request.form.get('course')

    course = Course.query.get(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('app_routes.home'))

    students = User.query.filter_by(role='student').all()

    report_data = []
    for student in students:
        total_classes = Attendance.query.filter_by(
            course_id=course_id, student_id=student.id).count()

        classes_attended = Attendance.query.filter_by(
            course_id=course_id, student_id=student.id, status='Present').count()

        attendance_percentage = (
            classes_attended / total_classes) * 100 if total_classes > 0 else 0

        report_data.append({
            'id': student.id,
            'name': student.name,
            'roll_number': student.enrollment_number,
            'attendance_percentage': round(attendance_percentage, 2)
        })

    return render_template('attendance_report.html',
                           report_data=report_data,
                           course_name=course.name,
                           course_id=course_id)


# Route to view detailed attendance for a specific student in a course (Professor only)
@app_routes.route('/view_student_attendance/<int:course_id>/<int:student_id>', methods=['GET'])
@login_required
def view_student_attendance(course_id, student_id):
    if current_user.role != 'professor':
        flash('Access denied', 'danger')
        return redirect(url_for('app_routes.home'))

    # Fetch the student
    student = User.query.get(student_id)
    if not student or student.role != 'student':
        flash('Student not found.', 'danger')
        return redirect(url_for('app_routes.home'))

    # Fetch the course
    course = Course.query.get(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('app_routes.home'))

    # Fetch attendance records for the student in the course
    attendance_records = Attendance.query.filter_by(
        course_id=course_id, student_id=student_id).all()

    return render_template('student_attendance_details.html',
                           attendance_records=attendance_records,
                           student=student,
                           course_name=course.name)
