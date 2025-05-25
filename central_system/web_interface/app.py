"""
ConsultEase Web Interface

This module provides a web interface for the ConsultEase system, allowing users
to access the system from any device with a web browser.
"""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
from flask_socketio import SocketIO, emit
import threading
import sys

# Add parent directory to path to help with imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('web_interface.log')
    ]
)
logger = logging.getLogger(__name__)

# Import models and controllers
try:
    from central_system.models import init_db
    from central_system.controllers import (
        FacultyController,
        ConsultationController
    )
    from central_system.models.faculty import Faculty
    from central_system.models.student import Student
    from central_system.models.consultation import Consultation
    from central_system.utils.session_manager import get_session_manager
    logger.info("Successfully imported ConsultEase components")
except ImportError as e:
    logger.error(f"Failed to import ConsultEase components: {e}")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'consultease-web-interface')
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database
init_db()

# Initialize session manager
session_manager = get_session_manager()

# Initialize controllers
faculty_controller = FacultyController()
consultation_controller = ConsultationController()

# Start controllers
faculty_controller.start()

# Security middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    headers = session_manager.get_security_headers()
    for header, value in headers.items():
        response.headers[header] = value
    return response

@app.before_request
def cleanup_sessions():
    """Clean up expired sessions before each request."""
    session_manager.cleanup_expired_sessions()

# Register for faculty status updates
@faculty_controller.register_callback
def handle_faculty_status_update(faculty):
    """
    Handle faculty status updates and broadcast to connected clients.
    """
    logger.info(f"Faculty status update: {faculty.name} (ID: {faculty.id}) - Status: {faculty.status}")
    socketio.emit('faculty_status_update', {
        'id': faculty.id,
        'name': faculty.name,
        'status': faculty.status
    })

def validate_session_required():
    """
    Validate session and redirect to login if invalid.
    Returns student object if valid, None if invalid.
    """
    # Check if basic session data exists
    if 'student_id' not in session or 'session_id' not in session:
        return None

    # Validate secure session
    is_valid, session_data = session_manager.validate_session(session['session_id'])
    if not is_valid:
        # Clear invalid session
        session.clear()
        return None

    # Get student information
    student = Student.get_by_id(session['student_id'])
    if not student:
        # Clear session for non-existent student
        session_manager.invalidate_session(session['session_id'])
        session.clear()
        return None

    return student

@app.route('/')
def index():
    """
    Render the main page with secure session validation.
    """
    student = validate_session_required()
    if not student:
        return redirect(url_for('login'))

    # Get all faculty
    faculties = faculty_controller.get_all_faculty()

    return render_template('index.html', student=student, faculties=faculties)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login with secure session management.
    """
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        ip_address = request.remote_addr

        if not student_id:
            return render_template('login.html', error="Student ID is required")

        # Check if user is locked out
        is_locked, time_remaining = session_manager.is_locked_out(student_id)
        if is_locked:
            minutes_remaining = int(time_remaining // 60)
            return render_template('login.html',
                                 error=f"Account locked due to multiple failed attempts. Try again in {minutes_remaining} minutes.")

        # Get student by ID
        student = Student.get_by_id(student_id)

        if student:
            # Clear any failed attempts on successful login
            session_manager.clear_failed_attempts(student_id)

            # Create secure session
            session_id = session_manager.create_session(
                user_id=str(student.id),
                user_type='student',
                additional_data={
                    'student_name': student.name,
                    'ip_address': ip_address,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            )

            # Set session data
            session['session_id'] = session_id
            session['student_id'] = student.id
            session['student_name'] = student.name

            logger.info(f"Student {student.name} (ID: {student.id}) logged in from {ip_address}")
            return redirect(url_for('index'))
        else:
            # Record failed attempt
            session_manager.record_failed_attempt(student_id, ip_address)
            logger.warning(f"Failed login attempt for student ID: {student_id} from {ip_address}")
            return render_template('login.html', error="Invalid student ID")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Handle user logout with secure session invalidation.
    """
    # Invalidate secure session if it exists
    if 'session_id' in session:
        session_manager.invalidate_session(session['session_id'])
        logger.info(f"Session invalidated for user: {session.get('student_name', 'unknown')}")

    # Clear Flask session
    session.clear()

    # Create response with logout confirmation
    response = make_response(redirect(url_for('login')))
    return response

@app.route('/api/faculty')
def get_faculty():
    """
    API endpoint to get all faculty.
    """
    faculties = faculty_controller.get_all_faculty()

    # Convert to JSON-serializable format
    faculty_list = []
    for faculty in faculties:
        faculty_list.append({
            'id': faculty.id,
            'name': faculty.name,
            'department': faculty.department,
            'status': faculty.status
        })

    return jsonify(faculty_list)

@app.route('/api/faculty/<int:faculty_id>')
def get_faculty_by_id(faculty_id):
    """
    API endpoint to get faculty by ID.
    """
    faculty = Faculty.get_by_id(faculty_id)

    if not faculty:
        return jsonify({'error': 'Faculty not found'}), 404

    return jsonify({
        'id': faculty.id,
        'name': faculty.name,
        'department': faculty.department,
        'status': faculty.status
    })

@app.route('/api/consultations', methods=['POST'])
def create_consultation():
    """
    API endpoint to create a new consultation request with secure session validation.
    """
    student = validate_session_required()
    if not student:
        return jsonify({'error': 'Session invalid or expired'}), 401

    data = request.json
    faculty_id = data.get('faculty_id')
    message = data.get('message')
    course_code = data.get('course_code', '')

    if not faculty_id or not message:
        return jsonify({'error': 'Missing required fields'}), 400

    # Get faculty
    faculty = Faculty.get_by_id(faculty_id)

    if not faculty:
        return jsonify({'error': 'Invalid faculty ID'}), 400

    # Create consultation request
    consultation = consultation_controller.create_consultation(
        student_id=student.id,
        faculty_id=faculty.id,
        message=message,
        course_code=course_code
    )

    if consultation:
        # Notify faculty desk unit via MQTT
        consultation_controller.notify_faculty_desk_unit(consultation)

        return jsonify({
            'id': consultation.id,
            'student_id': consultation.student_id,
            'faculty_id': consultation.faculty_id,
            'message': consultation.message,
            'course_code': consultation.course_code,
            'status': consultation.status,
            'created_at': consultation.created_at.isoformat()
        })
    else:
        return jsonify({'error': 'Failed to create consultation request'}), 500

@app.route('/api/consultations')
def get_consultations():
    """
    API endpoint to get consultations for the current student with secure session validation.
    """
    student = validate_session_required()
    if not student:
        return jsonify({'error': 'Session invalid or expired'}), 401

    consultations = consultation_controller.get_consultations(student_id=student.id)

    # Convert to JSON-serializable format
    consultation_list = []
    for consultation in consultations:
        consultation_list.append({
            'id': consultation.id,
            'student_id': consultation.student_id,
            'faculty_id': consultation.faculty_id,
            'faculty_name': consultation.faculty.name,
            'message': consultation.message,
            'course_code': consultation.course_code,
            'status': consultation.status,
            'created_at': consultation.created_at.isoformat()
        })

    return jsonify(consultation_list)

if __name__ == '__main__':
    # Run the Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
