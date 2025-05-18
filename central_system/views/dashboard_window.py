from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGridLayout, QScrollArea, QFrame,
                               QLineEdit, QTextEdit, QComboBox, QMessageBox,
                               QSplitter, QApplication, QSizePolicy)
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

        # Set fixed width and minimum height for consistent card size
        # Increased width to accommodate longer faculty names
        self.setFixedWidth(280)
        self.setMinimumHeight(180)

        # Set size policy to prevent stretching
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        # Add drop shadow effect for card-like appearance
        self.setGraphicsEffect(self._create_shadow_effect())

        # Set styling based on faculty status
        self.update_style()

        # Main layout with proper margins for card-like appearance
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        main_layout.setAlignment(Qt.AlignCenter)

        # Faculty info layout (image + text)
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)

        # Faculty image - reduced size with improved styling
        image_label = QLabel()
        image_label.setFixedSize(60, 60)
        image_label.setStyleSheet("""
            border: 1px solid #ddd;
            border-radius: 30px;
            background-color: white;
            padding: 2px;
        """)
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
        text_layout.setAlignment(Qt.AlignLeft)
        text_layout.setSpacing(4)  # Increased spacing between name and department
        text_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to maximize text space

        # Faculty name - improved styling for better readability
        name_label = QLabel(self.faculty.name)
        name_label.setStyleSheet("""
            font-size: 15pt;
            font-weight: bold;
            padding: 0;
            margin: 0;
        """)
        name_label.setAlignment(Qt.AlignLeft)
        name_label.setWordWrap(True)
        name_label.setMinimumWidth(180)  # Ensure enough width for text
        name_label.setMaximumWidth(200)  # Limit maximum width
        text_layout.addWidget(name_label)

        # Department - improved styling
        dept_label = QLabel(self.faculty.department)
        dept_label.setStyleSheet("""
            font-size: 11pt;
            color: #666;
            padding: 0;
            margin: 0;
        """)
        dept_label.setAlignment(Qt.AlignLeft)
        dept_label.setWordWrap(True)
        dept_label.setMinimumWidth(180)  # Ensure enough width for text
        dept_label.setMaximumWidth(200)  # Limit maximum width
        text_layout.addWidget(dept_label)

        info_layout.addLayout(text_layout)
        main_layout.addLayout(info_layout)

        # Add a horizontal line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #ddd; max-height: 1px;")
        main_layout.addWidget(separator)

        # Status indicator - improved layout and styling
        status_layout = QHBoxLayout()
        status_layout.setAlignment(Qt.AlignLeft)
        status_layout.setSpacing(4)

        status_icon = QLabel("●")
        if self.faculty.status:
            # No border on status icon, reduced font size
            status_icon.setStyleSheet("font-size: 12pt; color: #4caf50; border: none;")
            status_text = QLabel("Available")
            # No border on status text, reduced font size
            status_text.setStyleSheet("font-size: 11pt; color: #4caf50; border: none;")
        else:
            status_icon.setStyleSheet("font-size: 12pt; color: #f44336; border: none;")
            status_text = QLabel("Unavailable")
            status_text.setStyleSheet("font-size: 11pt; color: #f44336; border: none;")

        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # Request consultation button - more compact with improved styling
        request_button = QPushButton("Request Consultation")
        request_button.setEnabled(self.faculty.status)
        request_button.setStyleSheet("""
            QPushButton {
                font-size: 10pt;
                padding: 6px;
                border-radius: 4px;
                background-color: #2196F3;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #B0BEC5;
                color: #ECEFF1;
            }
        """)
        request_button.clicked.connect(self.request_consultation)
        main_layout.addWidget(request_button)

    def _create_shadow_effect(self):
        """
        Create a shadow effect for the card.
        """
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        return shadow

    def update_style(self):
        """
        Update the card styling based on faculty status.
        """
        if self.faculty.status:
            self.setStyleSheet('''
                QFrame {
                    background-color: #e8f5e9;
                    border: 1px solid #4caf50;
                    border-radius: 8px;
                }
            ''')
        else:
            self.setStyleSheet('''
                QFrame {
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 8px;
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

    def init_ui(self):
        """
        Initialize the dashboard UI.
        """
        # Main layout with splitter
        main_layout = QVBoxLayout()

        # Header with welcome message and student info
        header_layout = QHBoxLayout()

        if self.student:
            welcome_label = QLabel(f"Welcome, {self.student.name}")
        else:
            welcome_label = QLabel("Welcome to ConsultEase")
        welcome_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        header_layout.addWidget(welcome_label)

        # Logout button - smaller size as per user preference
        logout_button = QPushButton("Logout")
        logout_button.setFixedSize(50, 22)  # Even smaller size
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 3px;
                font-size: 8pt;  /* Smaller font */
                font-weight: bold;
                padding: 1px 2px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a82315;
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

        # Faculty grid in a scroll area with improved spacing and alignment
        self.faculty_grid = QGridLayout()
        self.faculty_grid.setSpacing(20)  # Increased spacing between cards
        self.faculty_grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Align to top and center horizontally
        self.faculty_grid.setContentsMargins(15, 15, 15, 15)  # Add margins around the grid

        # Create a scroll area for the faculty grid
        faculty_scroll = QScrollArea()
        faculty_scroll.setWidgetResizable(True)
        faculty_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        faculty_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        faculty_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #f0f0f0;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Create a container widget for the faculty grid
        faculty_scroll_content = QWidget()
        faculty_scroll_content.setLayout(self.faculty_grid)
        faculty_scroll_content.setStyleSheet("background-color: transparent;")

        # Set the scroll area widget
        faculty_scroll.setWidget(faculty_scroll_content)

        # Ensure scroll area starts at the top
        faculty_scroll.verticalScrollBar().setValue(0)

        # Store the scroll area for later reference
        self.faculty_scroll = faculty_scroll

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

        # Save splitter state when it changes
        content_splitter.splitterMoved.connect(self.save_splitter_state)

        # Store the splitter for later reference
        self.content_splitter = content_splitter

        # Try to restore previous splitter state
        self.restore_splitter_state()

        # Add the splitter to the main layout
        main_layout.addWidget(content_splitter)

        # Schedule a scroll to top after the UI is fully loaded
        QTimer.singleShot(100, self._scroll_faculty_to_top)

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

        # Fixed card width (matches the width set in FacultyCard)
        card_width = 280  # Updated to match the increased FacultyCard width

        # Grid spacing (matches the spacing set in faculty_grid)
        spacing = 20

        # Get the actual width of the faculty grid container
        grid_container_width = self.faculty_grid.parentWidget().width()
        if grid_container_width <= 0:  # If not yet available, estimate based on screen
            grid_container_width = int(screen_width * 0.6)  # 60% of screen for faculty grid

        # Account for grid margins
        grid_container_width -= 30  # 15px left + 15px right margin

        # Calculate how many cards can fit in a row, accounting for spacing
        max_cols = max(1, int(grid_container_width / (card_width + spacing)))

        # Adjust for very small screens
        if screen_width < 800:
            max_cols = 1  # Force single column on very small screens

        # Add faculty cards to grid with centering containers
        row, col = 0, 0

        for faculty in faculties:
            # Create a container widget to center the card
            container = QWidget()
            container.setStyleSheet("background-color: transparent;")
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignCenter)

            # Create the faculty card
            card = FacultyCard(faculty)
            card.consultation_requested.connect(self.show_consultation_form)

            # Add card to container
            container_layout.addWidget(card)

            # Add container to grid
            self.faculty_grid.addWidget(container, row, col)

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
            self.faculty_grid.addWidget(no_results, 0, 0, 1, max_cols)  # Span all columns

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

            # Ensure scroll area starts at the top
            if hasattr(self, 'faculty_scroll') and self.faculty_scroll:
                self.faculty_scroll.verticalScrollBar().setValue(0)
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

            # Ensure scroll area starts at the top
            if hasattr(self, 'faculty_scroll') and self.faculty_scroll:
                self.faculty_scroll.verticalScrollBar().setValue(0)

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

    def save_splitter_state(self):
        """
        Save the current splitter state to settings.
        """
        try:
            # Import QSettings
            from PyQt5.QtCore import QSettings

            # Create settings object
            settings = QSettings("ConsultEase", "Dashboard")

            # Save splitter state
            settings.setValue("splitter_state", self.content_splitter.saveState())
            settings.setValue("splitter_sizes", self.content_splitter.sizes())

            logger.debug("Saved splitter state")
        except Exception as e:
            logger.error(f"Error saving splitter state: {e}")

    def restore_splitter_state(self):
        """
        Restore the splitter state from settings.
        """
        try:
            # Import QSettings
            from PyQt5.QtCore import QSettings

            # Create settings object
            settings = QSettings("ConsultEase", "Dashboard")

            # Restore splitter state if available
            if settings.contains("splitter_state"):
                state = settings.value("splitter_state")
                if state:
                    self.content_splitter.restoreState(state)
                    logger.debug("Restored splitter state")

            # Fallback to sizes if state restoration fails
            elif settings.contains("splitter_sizes"):
                sizes = settings.value("splitter_sizes")
                if sizes:
                    self.content_splitter.setSizes(sizes)
                    logger.debug("Restored splitter sizes")
        except Exception as e:
            logger.error(f"Error restoring splitter state: {e}")
            # Use default sizes as fallback
            screen_width = QApplication.desktop().screenGeometry().width()
            self.content_splitter.setSizes([int(screen_width * 0.6), int(screen_width * 0.4)])

    def logout(self):
        """
        Handle logout button click.
        """
        # Save splitter state before logout
        self.save_splitter_state()

        self.change_window.emit("login", None)

    def show_notification(self, message, message_type="info"):
        """
        Show a notification message to the user using the standardized notification system.

        Args:
            message (str): Message to display
            message_type (str): Type of message ('success', 'error', 'warning', or 'info')
        """
        try:
            # Import notification manager
            from ..utils.notification import NotificationManager

            # Map message types
            type_mapping = {
                "success": NotificationManager.SUCCESS,
                "error": NotificationManager.ERROR,
                "warning": NotificationManager.WARNING,
                "info": NotificationManager.INFO
            }

            # Get standardized message type
            std_type = type_mapping.get(message_type.lower(), NotificationManager.INFO)

            # Show notification using the manager
            title = message_type.capitalize()
            if message_type == "error":
                title = "Error"
            elif message_type == "success":
                title = "Success"
            elif message_type == "warning":
                title = "Warning"
            else:
                title = "Information"

            NotificationManager.show_message(self, title, message, std_type)

        except ImportError:
            # Fallback to basic message boxes if notification manager is not available
            logger.warning("NotificationManager not available, using basic message boxes")
            if message_type == "success":
                QMessageBox.information(self, "Success", message)
            elif message_type == "error":
                QMessageBox.warning(self, "Error", message)
            elif message_type == "warning":
                QMessageBox.warning(self, "Warning", message)
            else:
                QMessageBox.information(self, "Information", message)

    def _scroll_faculty_to_top(self):
        """
        Scroll the faculty grid to the top.
        This is called after the UI is fully loaded to ensure faculty cards are visible.
        """
        if hasattr(self, 'faculty_scroll') and self.faculty_scroll:
            self.faculty_scroll.verticalScrollBar().setValue(0)
            logger.debug("Scrolled faculty grid to top")

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