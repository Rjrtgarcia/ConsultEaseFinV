from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGridLayout, QScrollArea, QFrame,
                               QLineEdit, QTextEdit, QComboBox, QMessageBox,
                               QSplitter, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QColor, QPixmap

import os
import logging
from .base_window import BaseWindow
from .consultation_panel import ConsultationPanel

# Set up logging
logger = logging.getLogger(__name__)

class FacultyCard(QFrame):
    """
    Widget to display faculty information and status.
    """
    consultation_requested = pyqtSignal(object)

    def __init__(self, faculty, parent=None):
        super().__init__(parent)
        self.faculty = faculty
        self.init_ui()

    def init_ui(self):
        """
        Initialize the faculty card UI.
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(300, 250)  # Increased height to accommodate image

        # Set styling based on faculty status
        self.update_style()

        # Main layout
        main_layout = QVBoxLayout(self)

        # Faculty info layout (image + text)
        info_layout = QHBoxLayout()

        # Faculty image
        image_label = QLabel()
        image_label.setFixedSize(80, 80)
        image_label.setStyleSheet("border: 1px solid #ddd; border-radius: 40px; background-color: white;")
        image_label.setScaledContents(True)

        # Try to load faculty image
        if hasattr(self.faculty, 'get_image_path') and self.faculty.image_path:
            try:
                image_path = self.faculty.get_image_path()
                if image_path and os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        # Create circular mask for the image
                        image_label.setPixmap(pixmap)
                    else:
                        logger.warning(f"Could not load image for faculty {self.faculty.name}: {image_path}")
                else:
                    logger.warning(f"Image path not found for faculty {self.faculty.name}: {image_path}")
            except Exception as e:
                logger.error(f"Error loading faculty image: {str(e)}")

        info_layout.addWidget(image_label)

        # Faculty text info
        text_layout = QVBoxLayout()

        # Faculty name
        name_label = QLabel(self.faculty.name)
        name_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        text_layout.addWidget(name_label)

        # Department
        dept_label = QLabel(self.faculty.department)
        dept_label.setStyleSheet("font-size: 12pt; color: #666;")
        text_layout.addWidget(dept_label)

        info_layout.addLayout(text_layout)
        main_layout.addLayout(info_layout)

        # Status indicator
        status_layout = QHBoxLayout()
        status_icon = QLabel("●")
        if self.faculty.status:
            status_icon.setStyleSheet("font-size: 16pt; color: #4caf50;")
            status_text = QLabel("Available")
            status_text.setStyleSheet("font-size: 14pt; color: #4caf50;")
        else:
            status_icon.setStyleSheet("font-size: 16pt; color: #f44336;")
            status_text = QLabel("Unavailable")
            status_text.setStyleSheet("font-size: 14pt; color: #f44336;")

        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # Request consultation button
        request_button = QPushButton("Request Consultation")
        request_button.setEnabled(self.faculty.status)
        request_button.clicked.connect(self.request_consultation)
        main_layout.addWidget(request_button)

    def update_style(self):
        """
        Update the card styling based on faculty status.
        """
        if self.faculty.status:
            self.setStyleSheet('''
                QFrame {
                    background-color: #e8f5e9;
                    border: 2px solid #4caf50;
                    border-radius: 10px;
                }
            ''')
        else:
            self.setStyleSheet('''
                QFrame {
                    background-color: #ffebee;
                    border: 2px solid #f44336;
                    border-radius: 10px;
                }
            ''')

    def update_faculty(self, faculty):
        """
        Update the faculty information.
        """
        self.faculty = faculty
        self.update_style()
        # Refresh the UI
        self.setParent(None)
        self.init_ui()

    def request_consultation(self):
        """
        Emit signal to request a consultation with this faculty.
        """
        self.consultation_requested.emit(self.faculty)

class ConsultationRequestForm(QFrame):
    """
    Form to request a consultation with a faculty member.
    """
    request_submitted = pyqtSignal(object, str, str)

    def __init__(self, faculty=None, parent=None):
        super().__init__(parent)
        self.faculty = faculty
        self.init_ui()

    def init_ui(self):
        """
        Initialize the consultation request form UI.
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 10px;
            }
        ''')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Form title
        title_label = QLabel("Request Consultation")
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Faculty information
        if self.faculty:
            # Create a layout for faculty info with image
            faculty_info_layout = QHBoxLayout()

            # Faculty image
            image_label = QLabel()
            image_label.setFixedSize(60, 60)
            image_label.setStyleSheet("border: 1px solid #ddd; border-radius: 30px; background-color: white;")
            image_label.setScaledContents(True)

            # Try to load faculty image
            if hasattr(self.faculty, 'get_image_path') and self.faculty.image_path:
                try:
                    image_path = self.faculty.get_image_path()
                    if image_path and os.path.exists(image_path):
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            image_label.setPixmap(pixmap)
                except Exception as e:
                    logger.error(f"Error loading faculty image in consultation form: {str(e)}")

            faculty_info_layout.addWidget(image_label)

            # Faculty text info
            faculty_info = QLabel(f"Faculty: {self.faculty.name} ({self.faculty.department})")
            faculty_info.setStyleSheet("font-size: 14pt;")
            faculty_info_layout.addWidget(faculty_info)
            faculty_info_layout.addStretch()

            main_layout.addLayout(faculty_info_layout)
        else:
            # If no faculty is selected, show a dropdown
            faculty_label = QLabel("Select Faculty:")
            faculty_label.setStyleSheet("font-size: 14pt;")
            main_layout.addWidget(faculty_label)

            self.faculty_combo = QComboBox()
            self.faculty_combo.setStyleSheet("font-size: 14pt; padding: 8px;")
            # Faculty options would be populated separately
            main_layout.addWidget(self.faculty_combo)

        # Course code input
        course_label = QLabel("Course Code (optional):")
        course_label.setStyleSheet("font-size: 14pt;")
        main_layout.addWidget(course_label)

        self.course_input = QLineEdit()
        self.course_input.setStyleSheet("font-size: 14pt; padding: 8px;")
        main_layout.addWidget(self.course_input)

        # Message input
        message_label = QLabel("Consultation Details:")
        message_label.setStyleSheet("font-size: 14pt;")
        main_layout.addWidget(message_label)

        self.message_input = QTextEdit()
        self.message_input.setStyleSheet("font-size: 14pt; padding: 8px;")
        self.message_input.setMinimumHeight(150)
        main_layout.addWidget(self.message_input)

        # Submit button
        button_layout = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet('''
            QPushButton {
                background-color: #f44336;
                min-width: 120px;
            }
        ''')
        cancel_button.clicked.connect(self.cancel_request)

        submit_button = QPushButton("Submit Request")
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #4caf50;
                min-width: 120px;
            }
        ''')
        submit_button.clicked.connect(self.submit_request)

        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(submit_button)

        main_layout.addLayout(button_layout)

    def set_faculty(self, faculty):
        """
        Set the faculty for the consultation request.
        """
        self.faculty = faculty
        self.init_ui()

    def set_faculty_options(self, faculties):
        """
        Set the faculty options for the dropdown.
        Only show available faculty members.
        """
        if hasattr(self, 'faculty_combo'):
            self.faculty_combo.clear()
            available_count = 0

            for faculty in faculties:
                # Only add available faculty to the dropdown
                if hasattr(faculty, 'status') and faculty.status:
                    self.faculty_combo.addItem(f"{faculty.name} ({faculty.department})", faculty)
                    available_count += 1

            # Show a message if no faculty is available
            if available_count == 0:
                self.faculty_combo.addItem("No faculty members are currently available", None)

    def get_selected_faculty(self):
        """
        Get the selected faculty from the dropdown.
        """
        if hasattr(self, 'faculty_combo') and self.faculty_combo.count() > 0:
            return self.faculty_combo.currentData()
        return self.faculty

    def submit_request(self):
        """
        Handle the submission of the consultation request.
        """
        faculty = self.get_selected_faculty()
        if not faculty:
            QMessageBox.warning(self, "Consultation Request", "Please select a faculty member.")
            return

        # Check if faculty is available
        if hasattr(faculty, 'status') and not faculty.status:
            QMessageBox.warning(self, "Consultation Request",
                               f"Faculty {faculty.name} is currently unavailable. Please select an available faculty member.")
            return

        message = self.message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Consultation Request", "Please enter consultation details.")
            return

        course_code = self.course_input.text().strip()

        # Emit signal with the request details
        self.request_submitted.emit(faculty, message, course_code)

    def cancel_request(self):
        """
        Cancel the consultation request.
        """
        self.message_input.clear()
        self.course_input.clear()
        self.setVisible(False)

class DashboardWindow(BaseWindow):
    """
    Main dashboard window with faculty availability display and consultation request functionality.
    """
    # Signal to handle consultation request
    consultation_requested = pyqtSignal(object, str, str)

    def __init__(self, student=None, parent=None):
        self.student = student
        super().__init__(parent)
        self.init_ui()

        # Set up auto-refresh timer for faculty status
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_faculty_status)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

        # Log student info for debugging
        if student:
            logger.info(f"Dashboard initialized with student: ID={student.id}, Name={student.name}, RFID={student.rfid_uid}")
        else:
            logger.warning("Dashboard initialized without student information")

    def update_student(self, new_student):
        """
        Update the dashboard with a new student's information.
        This method should be called when a different student logs in.

        Args:
            new_student (Student): The new student object
        """
        # Check if this is actually a different student
        if self.student and new_student and self.student.id == new_student.id:
            logger.info(f"Student unchanged, not updating dashboard: ID={new_student.id}")
            return

        # Log the student change
        old_student_id = self.student.id if self.student else None
        new_student_id = new_student.id if new_student else None
        logger.info(f"Updating dashboard student from ID={old_student_id} to ID={new_student_id}")

        # Update the student reference
        self.student = new_student

        # Update the welcome message
        if hasattr(self, 'welcome_label'):
            if self.student:
                self.welcome_label.setText(f"Welcome, {self.student.name}")
            else:
                self.welcome_label.setText("Welcome to ConsultEase")

        # Update the consultation panel with the new student
        if hasattr(self, 'consultation_panel'):
            self.consultation_panel.set_student(new_student)
            logger.info(f"Updated consultation panel with new student: ID={new_student_id}")

        # Update window title
        if self.student:
            self.setWindowTitle(f"ConsultEase - {self.student.name}")
        else:
            self.setWindowTitle("ConsultEase")

        # Refresh the faculty grid to ensure it's up to date
        try:
            # Import faculty controller
            from ..controllers import FacultyController

            # Get faculty controller
            faculty_controller = FacultyController()

            # Get all faculty
            faculties = faculty_controller.get_all_faculty()

            # Update the grid
            self.populate_faculty_grid(faculties)
            logger.info("Refreshed faculty grid after student update")
        except Exception as e:
            logger.error(f"Error refreshing faculty grid after student update: {str(e)}")

        logger.info(f"Dashboard successfully updated with new student: ID={new_student_id}, Name={new_student.name if new_student else 'None'}")

    def init_ui(self):
        """
        Initialize the dashboard UI.
        """
        # Main layout with splitter
        main_layout = QVBoxLayout()

        # Header with welcome message and student info
        header_layout = QHBoxLayout()

        # Create welcome label and store a reference to it for later updates
        if self.student:
            self.welcome_label = QLabel(f"Welcome, {self.student.name}")
            # Set window title with student name
            self.setWindowTitle(f"ConsultEase - {self.student.name}")
        else:
            self.welcome_label = QLabel("Welcome to ConsultEase")
            self.setWindowTitle("ConsultEase")
        self.welcome_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        header_layout.addWidget(self.welcome_label)

        # Logout button - smaller size
        logout_button = QPushButton("Logout")
        logout_button.setFixedSize(80, 30)
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)

        main_layout.addLayout(header_layout)

        # Main content with faculty grid and consultation form
        content_splitter = QSplitter(Qt.Horizontal)

        # Get screen size to set proportional initial sizes
        screen_size = QApplication.desktop().screenGeometry()
        screen_width = screen_size.width()

        # Faculty availability grid
        faculty_widget = QWidget()
        faculty_layout = QVBoxLayout(faculty_widget)

        # Search and filter controls in a more touch-friendly layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Search input with icon and better styling
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 2px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(5, 0, 5, 0)
        search_layout.setSpacing(5)

        search_icon = QLabel()
        try:
            search_icon_pixmap = QPixmap("resources/icons/search.png")
            if not search_icon_pixmap.isNull():
                search_icon.setPixmap(search_icon_pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            # If icon not available, use text
            search_icon.setText("🔍")

        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or department")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 5px;
                font-size: 12pt;
            }
        """)
        self.search_input.textChanged.connect(self.filter_faculty)
        search_layout.addWidget(self.search_input)

        filter_layout.addWidget(search_frame, 3)  # Give search more space

        # Filter dropdown with better styling
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 2px;
            }
        """)
        filter_inner_layout = QHBoxLayout(filter_frame)
        filter_inner_layout.setContentsMargins(5, 0, 5, 0)
        filter_inner_layout.setSpacing(5)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-size: 12pt;")
        filter_inner_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All", None)
        self.filter_combo.addItem("Available Only", True)
        self.filter_combo.addItem("Unavailable Only", False)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                border: none;
                padding: 5px;
                font-size: 12pt;
            }
            QComboBox::drop-down {
                width: 20px;
            }
        """)
        self.filter_combo.currentIndexChanged.connect(self.filter_faculty)
        filter_inner_layout.addWidget(self.filter_combo)

        filter_layout.addWidget(filter_frame, 2)  # Give filter less space

        faculty_layout.addLayout(filter_layout)

        # Faculty grid in a scroll area
        self.faculty_grid = QGridLayout()
        self.faculty_grid.setSpacing(20)

        faculty_scroll = QScrollArea()
        faculty_scroll.setWidgetResizable(True)
        faculty_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        faculty_scroll_content = QWidget()
        faculty_scroll_content.setLayout(self.faculty_grid)
        faculty_scroll.setWidget(faculty_scroll_content)

        faculty_layout.addWidget(faculty_scroll)

        # Consultation panel with request form and history
        self.consultation_panel = ConsultationPanel(self.student)
        self.consultation_panel.consultation_requested.connect(self.handle_consultation_request)
        self.consultation_panel.consultation_cancelled.connect(self.handle_consultation_cancel)

        # Add widgets to splitter
        content_splitter.addWidget(faculty_widget)
        content_splitter.addWidget(self.consultation_panel)

        # Set splitter sizes proportionally to screen width
        content_splitter.setSizes([int(screen_width * 0.6), int(screen_width * 0.4)])

        main_layout.addWidget(content_splitter)

        # Set the main layout to a widget and make it the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def populate_faculty_grid(self, faculties):
        """
        Populate the faculty grid with faculty cards.

        Args:
            faculties (list): List of faculty objects
        """
        # Clear existing grid
        while self.faculty_grid.count():
            item = self.faculty_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Calculate optimal number of columns based on screen width
        screen_width = QApplication.desktop().screenGeometry().width()
        card_width = 250  # Approximate width of a faculty card
        spacing = 20  # Grid spacing

        # Calculate how many cards can fit in a row
        available_width = screen_width * 0.6  # 60% of screen for faculty grid
        max_cols = max(1, int(available_width / (card_width + spacing)))

        # Add faculty cards to grid
        row, col = 0, 0

        for faculty in faculties:
            card = FacultyCard(faculty)
            card.consultation_requested.connect(self.show_consultation_form)
            self.faculty_grid.addWidget(card, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # If no faculty found, show a message
        if not faculties:
            no_results = QLabel("No faculty members found matching your criteria")
            no_results.setStyleSheet("""
                font-size: 14pt;
                color: #7f8c8d;
                padding: 20px;
                background-color: #f5f5f5;
                border-radius: 10px;
            """)
            no_results.setAlignment(Qt.AlignCenter)
            self.faculty_grid.addWidget(no_results, 0, 0)

    def filter_faculty(self):
        """
        Filter faculty grid based on search text and filter selection.
        """
        try:
            # Import faculty controller
            from ..controllers import FacultyController

            # Get search text and filter value
            search_text = self.search_input.text().strip()
            filter_available = self.filter_combo.currentData()

            # Get faculty controller
            faculty_controller = FacultyController()

            # Get filtered faculty list
            faculties = faculty_controller.get_all_faculty(
                filter_available=filter_available,
                search_term=search_text
            )

            # Update the grid
            self.populate_faculty_grid(faculties)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error filtering faculty: {str(e)}")
            self.show_notification("Error filtering faculty list", "error")

    def refresh_faculty_status(self):
        """
        Refresh the faculty status from the server.
        """
        try:
            # Import faculty controller
            from ..controllers import FacultyController

            # Get current filter settings
            search_text = self.search_input.text().strip()
            filter_available = self.filter_combo.currentData()

            # Get faculty controller
            faculty_controller = FacultyController()

            # Get updated faculty list with current filters
            faculties = faculty_controller.get_all_faculty(
                filter_available=filter_available,
                search_term=search_text
            )

            # Update the grid
            self.populate_faculty_grid(faculties)

            # Also refresh consultation history if student is logged in
            if self.student:
                self.consultation_panel.refresh_history()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error refreshing faculty status: {str(e)}")
            self.show_notification("Error refreshing faculty status", "error")

    def show_consultation_form(self, faculty):
        """
        Show the consultation request form for a specific faculty.

        Args:
            faculty (object): Faculty object to request consultation with
        """
        # Check if faculty is available
        if not faculty.status:
            self.show_notification(
                f"Faculty {faculty.name} is currently unavailable for consultation.",
                "error"
            )
            return

        # Also populate the dropdown with all available faculty
        try:
            from ..controllers import FacultyController
            faculty_controller = FacultyController()
            available_faculty = faculty_controller.get_all_faculty(filter_available=True)

            # Set the faculty and faculty options in the consultation panel
            self.consultation_panel.set_faculty(faculty)
            self.consultation_panel.set_faculty_options(available_faculty)
        except Exception as e:
            logger.error(f"Error loading available faculty for consultation form: {str(e)}")

    def handle_consultation_request(self, faculty, message, course_code):
        """
        Handle consultation request submission.

        Args:
            faculty (object): Faculty object
            message (str): Consultation request message
            course_code (str): Optional course code
        """
        try:
            # Import consultation controller
            from ..controllers import ConsultationController

            # Get consultation controller
            consultation_controller = ConsultationController()

            # Create consultation
            if self.student:
                consultation = consultation_controller.create_consultation(
                    student_id=self.student.id,
                    faculty_id=faculty.id,
                    request_message=message,
                    course_code=course_code
                )

                if consultation:
                    # Show confirmation
                    QMessageBox.information(
                        self,
                        "Consultation Request",
                        f"Your consultation request with {faculty.name} has been submitted."
                    )

                    # Refresh the consultation history
                    self.consultation_panel.refresh_history()
                else:
                    QMessageBox.warning(
                        self,
                        "Consultation Request",
                        f"Failed to submit consultation request. Please try again."
                    )
            else:
                # No student logged in
                QMessageBox.warning(
                    self,
                    "Consultation Request",
                    "You must be logged in to submit a consultation request."
                )
        except Exception as e:
            logger.error(f"Error creating consultation: {str(e)}")
            QMessageBox.warning(
                self,
                "Consultation Request",
                f"An error occurred while submitting your consultation request: {str(e)}"
            )

    def handle_consultation_cancel(self, consultation_id):
        """
        Handle consultation cancellation.

        Args:
            consultation_id (int): ID of the consultation to cancel
        """
        try:
            # Import consultation controller
            from ..controllers import ConsultationController

            # Get consultation controller
            consultation_controller = ConsultationController()

            # Cancel consultation
            consultation = consultation_controller.cancel_consultation(consultation_id)

            if consultation:
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Consultation Cancelled",
                    f"Your consultation request has been cancelled."
                )

                # Refresh the consultation history
                self.consultation_panel.refresh_history()
            else:
                QMessageBox.warning(
                    self,
                    "Consultation Cancellation",
                    f"Failed to cancel consultation request. Please try again."
                )
        except Exception as e:
            logger.error(f"Error cancelling consultation: {str(e)}")
            QMessageBox.warning(
                self,
                "Consultation Cancellation",
                f"An error occurred while cancelling your consultation request: {str(e)}"
            )

    def logout(self):
        """
        Handle logout button click.
        """
        self.change_window.emit("login", None)

    def show_notification(self, message, message_type="info"):
        """
        Show a notification message to the user.

        Args:
            message (str): Message to display
            message_type (str): Type of message ('success', 'error', or 'info')
        """
        if message_type == "success":
            QMessageBox.information(self, "Success", message)
        elif message_type == "error":
            QMessageBox.warning(self, "Error", message)
        else:
            QMessageBox.information(self, "Information", message)

    def simulate_consultation_request(self):
        """
        Simulate a consultation request for testing purposes.
        This method finds an available faculty and shows the consultation form.
        """
        try:
            # Import faculty controller
            from ..controllers import FacultyController

            # Get faculty controller
            faculty_controller = FacultyController()

            # Get available faculty
            available_faculty = faculty_controller.get_all_faculty(filter_available=True)

            if available_faculty:
                # Use the first available faculty
                faculty = available_faculty[0]
                logger.info(f"Simulating consultation request with faculty: {faculty.name}")

                # Show the consultation form
                self.show_consultation_form(faculty)
            else:
                logger.warning("No available faculty found for simulation")
                self.show_notification("No available faculty found. Please try again later.", "error")
        except Exception as e:
            logger.error(f"Error simulating consultation request: {str(e)}")
            self.show_notification("Error simulating consultation request", "error")