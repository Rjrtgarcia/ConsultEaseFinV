"""
Consultation panel module.
Contains the consultation request form and consultation history panel.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QGridLayout, QScrollArea, QFrame,
                            QLineEdit, QTextEdit, QComboBox, QMessageBox,
                            QTabWidget, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSplitter, QDialog, QFormLayout,
                            QSpacerItem, QSizePolicy, QProgressBar,
                            QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from PyQt5.QtCore import (Qt, pyqtSignal, QTimer, QSize, QDateTime,
                         QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup)
from PyQt5.QtGui import QIcon, QColor, QPixmap, QFont

import os
import logging
import datetime

# Set up logging
logger = logging.getLogger(__name__)

class ConsultationRequestForm(QFrame):
    """
    Form to request a consultation with a faculty member.
    """
    request_submitted = pyqtSignal(object, str, str)

    def __init__(self, faculty=None, parent=None):
        super().__init__(parent)
        self.faculty = faculty
        self.faculty_options = []
        self.init_ui()

    def init_ui(self):
        """
        Initialize the consultation request form UI with improved styling and layout.
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                font-size: 12pt;
                color: #2c3e50;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                font-size: 12pt;
                selection-background-color: #3498db;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #3498db;
            }
            QPushButton {
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12pt;
                font-weight: bold;
                color: white;
                min-height: 40px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        ''')

        # Add shadow effect for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Form title with improved styling
        title_label = QLabel("Request Consultation")
        title_label.setStyleSheet("font-size: 22pt; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Add a subtitle/instruction
        subtitle = QLabel("Fill out the form below to request a consultation with a faculty member")
        subtitle.setStyleSheet("font-size: 11pt; color: #7f8c8d; margin-bottom: 15px;")
        main_layout.addWidget(subtitle)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #ddd; max-height: 1px; margin: 10px 0;")
        main_layout.addWidget(separator)

        # Faculty selection with improved layout
        faculty_layout = QHBoxLayout()
        faculty_label = QLabel("Faculty:")
        faculty_label.setFixedWidth(120)
        faculty_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.faculty_combo = QComboBox()
        self.faculty_combo.setMinimumWidth(300)
        self.faculty_combo.setMinimumHeight(40)
        faculty_layout.addWidget(faculty_label)
        faculty_layout.addWidget(self.faculty_combo)
        main_layout.addLayout(faculty_layout)

        # Course code input with improved layout
        course_layout = QHBoxLayout()
        course_label = QLabel("Course Code:")
        course_label.setFixedWidth(120)
        course_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.course_input = QLineEdit()
        self.course_input.setPlaceholderText("e.g., CS101 (optional)")
        self.course_input.setMinimumHeight(40)
        course_layout.addWidget(course_label)
        course_layout.addWidget(self.course_input)
        main_layout.addLayout(course_layout)

        # Message input with improved layout
        message_layout = QVBoxLayout()
        message_label = QLabel("Consultation Details:")
        message_label.setStyleSheet("font-size: 12pt; font-weight: bold; margin-top: 10px;")
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Describe what you'd like to discuss...")
        self.message_input.setMinimumHeight(180)
        message_layout.addWidget(message_label)
        message_layout.addWidget(self.message_input)
        main_layout.addLayout(message_layout)

        # Character count with visual indicator
        char_count_frame = QFrame()
        char_count_layout = QVBoxLayout(char_count_frame)
        char_count_layout.setContentsMargins(0, 0, 0, 0)
        char_count_layout.setSpacing(2)

        # Label and progress bar in a horizontal layout
        count_indicator_layout = QHBoxLayout()
        count_indicator_layout.setContentsMargins(0, 0, 0, 0)

        self.char_count_label = QLabel("0/500 characters")
        self.char_count_label.setAlignment(Qt.AlignLeft)
        self.char_count_label.setStyleSheet("color: #7f8c8d; font-size: 10pt;")

        # Add a small info label about the limit
        char_limit_info = QLabel("(500 character limit)")
        char_limit_info.setStyleSheet("color: #7f8c8d; font-size: 9pt; font-style: italic;")
        char_limit_info.setAlignment(Qt.AlignRight)

        count_indicator_layout.addWidget(self.char_count_label)
        count_indicator_layout.addStretch()
        count_indicator_layout.addWidget(char_limit_info)

        char_count_layout.addLayout(count_indicator_layout)

        # Add progress bar for visual feedback
        self.char_count_progress = QProgressBar()
        self.char_count_progress.setRange(0, 500)
        self.char_count_progress.setValue(0)
        self.char_count_progress.setTextVisible(False)
        self.char_count_progress.setFixedHeight(5)
        self.char_count_progress.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #7f8c8d;
                border-radius: 2px;
            }
        """)

        char_count_layout.addWidget(self.char_count_progress)
        main_layout.addWidget(char_count_frame)

        # Connect text changed signal to update character count
        self.message_input.textChanged.connect(self.update_char_count)

        # Buttons with improved styling
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet('''
            QPushButton {
                background-color: #e74c3c;
                min-width: 140px;
                min-height: 45px;
                font-size: 13pt;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        ''')
        cancel_button.clicked.connect(self.cancel_request)

        submit_button = QPushButton("Submit Request")
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #2ecc71;
                min-width: 180px;
                min-height: 45px;
                font-size: 13pt;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219653;
            }
        ''')
        submit_button.clicked.connect(self.submit_request)

        # Add shadow effects to buttons for depth
        for btn in [cancel_button, submit_button]:
            btn_shadow = QGraphicsDropShadowEffect()
            btn_shadow.setBlurRadius(10)
            btn_shadow.setColor(QColor(0, 0, 0, 50))
            btn_shadow.setOffset(2, 2)
            btn.setGraphicsEffect(btn_shadow)

        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(submit_button)

        main_layout.addLayout(button_layout)

    def update_char_count(self):
        """
        Update the character count label and progress bar.
        """
        count = len(self.message_input.toPlainText())
        color = "#7f8c8d"  # Default gray
        progress_color = "#7f8c8d"  # Default gray

        if count > 400:
            color = "#f39c12"  # Warning yellow
            progress_color = "#f39c12"
        if count > 500:
            color = "#e74c3c"  # Error red
            progress_color = "#e74c3c"

        self.char_count_label.setText(f"{count}/500 characters")
        self.char_count_label.setStyleSheet(f"color: {color}; font-size: 10pt;")

        # Update progress bar
        self.char_count_progress.setValue(count)
        self.char_count_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #f0f0f0;
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {progress_color};
                border-radius: 2px;
            }}
        """)

    def set_faculty(self, faculty):
        """
        Set the faculty for the consultation request.
        """
        self.faculty = faculty

        # Update the combo box
        if self.faculty and self.faculty_combo.count() > 0:
            for i in range(self.faculty_combo.count()):
                faculty_id = self.faculty_combo.itemData(i)
                if faculty_id == self.faculty.id:
                    self.faculty_combo.setCurrentIndex(i)
                    break

    def set_faculty_options(self, faculty_list):
        """
        Set the available faculty options in the dropdown.
        """
        self.faculty_options = faculty_list
        self.faculty_combo.clear()

        for faculty in faculty_list:
            self.faculty_combo.addItem(f"{faculty.name} ({faculty.department})", faculty.id)

        # If we have a selected faculty, select it in the dropdown
        if self.faculty:
            for i in range(self.faculty_combo.count()):
                faculty_id = self.faculty_combo.itemData(i)
                if faculty_id == self.faculty.id:
                    self.faculty_combo.setCurrentIndex(i)
                    break

    def get_selected_faculty(self):
        """
        Get the selected faculty from the dropdown.
        """
        if self.faculty_combo.count() == 0:
            return self.faculty

        faculty_id = self.faculty_combo.currentData()

        for faculty in self.faculty_options:
            if faculty.id == faculty_id:
                return faculty

        return None

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

        # Check message length
        if len(message) > 500:
            QMessageBox.warning(self, "Consultation Request", "Consultation details are too long. Please limit to 500 characters.")
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

class ConsultationHistoryPanel(QFrame):
    """
    Panel to display consultation history.
    """
    consultation_selected = pyqtSignal(object)
    consultation_cancelled = pyqtSignal(int)

    def __init__(self, student=None, parent=None):
        super().__init__(parent)
        self.student = student
        self.consultations = []
        self.init_ui()

    def init_ui(self):
        """
        Initialize the consultation history panel UI with improved styling.
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 15px;
            }
            QTableWidget {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #e9ecef;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f1f1;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton {
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12pt;
                font-weight: bold;
                color: white;
                min-height: 35px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        ''')

        # Add shadow effect for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # Title with improved styling
        title_layout = QHBoxLayout()

        title_label = QLabel("My Consultation History")
        title_label.setStyleSheet("font-size: 22pt; font-weight: bold; color: #2c3e50;")
        title_layout.addWidget(title_label)

        # Add a counter badge showing number of consultations
        self.consultation_count = QLabel("0")
        self.consultation_count.setStyleSheet('''
            background-color: #3498db;
            color: white;
            border-radius: 15px;
            padding: 5px 10px;
            font-size: 12pt;
            font-weight: bold;
            min-width: 30px;
            text-align: center;
        ''')
        self.consultation_count.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.consultation_count)
        title_layout.addStretch()

        main_layout.addLayout(title_layout)

        # Add a subtitle/instruction
        subtitle = QLabel("View and manage your consultation requests")
        subtitle.setStyleSheet("font-size: 11pt; color: #7f8c8d; margin-bottom: 15px;")
        main_layout.addWidget(subtitle)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #ddd; max-height: 1px; margin: 10px 0;")
        main_layout.addWidget(separator)

        # Consultation table with improved styling
        table_container = QFrame()
        table_container.setStyleSheet('''
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        ''')
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(5, 5, 5, 5)

        self.consultation_table = QTableWidget()
        self.consultation_table.setColumnCount(5)
        self.consultation_table.setHorizontalHeaderLabels(["Faculty", "Course", "Status", "Date", "Actions"])
        self.consultation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.consultation_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.consultation_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.consultation_table.setSelectionMode(QTableWidget.SingleSelection)
        self.consultation_table.setAlternatingRowColors(True)
        self.consultation_table.setShowGrid(False)
        self.consultation_table.verticalHeader().setVisible(False)
        self.consultation_table.setStyleSheet('''
            QTableWidget {
                border: none;
            }
        ''')

        table_layout.addWidget(self.consultation_table)
        main_layout.addWidget(table_container)

        # Refresh button with improved styling
        button_layout = QHBoxLayout()

        # Add a "No consultations" message that will be shown when table is empty
        self.no_consultations_label = QLabel("You don't have any consultation requests yet.")
        self.no_consultations_label.setStyleSheet('''
            color: #7f8c8d;
            font-size: 12pt;
            font-style: italic;
        ''')
        self.no_consultations_label.setAlignment(Qt.AlignCenter)
        self.no_consultations_label.setVisible(False)
        button_layout.addWidget(self.no_consultations_label)

        button_layout.addStretch()

        refresh_button = QPushButton("Refresh")
        refresh_button.setStyleSheet('''
            QPushButton {
                background-color: #3498db;
                min-width: 140px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2471a3;
            }
        ''')

        # Add shadow effect to button
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(10)
        btn_shadow.setColor(QColor(0, 0, 0, 50))
        btn_shadow.setOffset(2, 2)
        refresh_button.setGraphicsEffect(btn_shadow)

        refresh_button.clicked.connect(self.refresh_consultations)
        button_layout.addWidget(refresh_button)

        main_layout.addLayout(button_layout)

    def set_student(self, student):
        """
        Set the student for the consultation history.
        """
        self.student = student
        self.refresh_consultations()

    def refresh_consultations(self):
        """
        Refresh the consultation history from the database.
        """
        if not self.student:
            return

        try:
            # Import consultation controller
            from ..controllers import ConsultationController

            # Get consultation controller
            consultation_controller = ConsultationController()

            # Get consultations for this student
            self.consultations = consultation_controller.get_consultations(student_id=self.student.id)

            # Update the table
            self.update_consultation_table()
        except Exception as e:
            logger.error(f"Error refreshing consultations: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to refresh consultation history: {str(e)}")

    def update_consultation_table(self):
        """
        Update the consultation table with the current consultations.
        """
        # Clear the table
        self.consultation_table.setRowCount(0)

        # Update consultation count badge
        self.consultation_count.setText(str(len(self.consultations)))

        # Show/hide "no consultations" message
        if not self.consultations:
            self.no_consultations_label.setVisible(True)
            return
        else:
            self.no_consultations_label.setVisible(False)

        # Add consultations to the table with improved styling
        for consultation in self.consultations:
            row_position = self.consultation_table.rowCount()
            self.consultation_table.insertRow(row_position)

            # Faculty name with improved styling
            faculty_item = QTableWidgetItem(consultation.faculty.name)
            faculty_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.consultation_table.setItem(row_position, 0, faculty_item)

            # Course code with improved styling
            course_item = QTableWidgetItem(consultation.course_code if consultation.course_code else "N/A")
            course_item.setTextAlignment(Qt.AlignCenter)
            self.consultation_table.setItem(row_position, 1, course_item)

            # Status with improved color coding and styling
            status_text = consultation.status.value.capitalize()
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)

            # Create a custom status cell with pill-shaped background
            status_cell = QWidget()
            status_layout = QHBoxLayout(status_cell)
            status_layout.setContentsMargins(5, 2, 5, 2)
            status_layout.setAlignment(Qt.AlignCenter)

            status_label = QLabel(status_text)
            status_label.setAlignment(Qt.AlignCenter)

            # Set color based on status
            if consultation.status.value == "pending":
                status_color = "#f39c12"  # Orange
                bg_color = "#fff3e0"
            elif consultation.status.value == "accepted":
                status_color = "#2ecc71"  # Green
                bg_color = "#e8f5e9"
            elif consultation.status.value == "completed":
                status_color = "#3498db"  # Blue
                bg_color = "#e3f2fd"
            elif consultation.status.value == "cancelled":
                status_color = "#e74c3c"  # Red
                bg_color = "#ffebee"
            else:
                status_color = "#7f8c8d"  # Gray
                bg_color = "#f5f5f5"

            # Apply styling to the status label
            status_label.setStyleSheet(f"""
                background-color: {bg_color};
                color: {status_color};
                border: 1px solid {status_color};
                border-radius: 10px;
                padding: 3px 10px;
                font-weight: bold;
            """)

            status_layout.addWidget(status_label)
            self.consultation_table.setCellWidget(row_position, 2, status_cell)

            # Date with improved formatting
            date_str = consultation.requested_at.strftime("%b %d, %Y %H:%M")
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.consultation_table.setItem(row_position, 3, date_item)

            # Actions with improved styling
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(8)
            actions_layout.setAlignment(Qt.AlignCenter)

            # View details button with improved styling
            view_button = QPushButton("View")
            view_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                    min-width: 70px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            view_button.clicked.connect(lambda checked=False, c=consultation: self.view_consultation_details(c))
            actions_layout.addWidget(view_button)

            # Cancel button (only for pending consultations) with improved styling
            if consultation.status.value == "pending":
                cancel_button = QPushButton("Cancel")
                cancel_button.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        border-radius: 5px;
                        padding: 5px 10px;
                        font-weight: bold;
                        min-width: 70px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                cancel_button.clicked.connect(lambda checked=False, c=consultation: self.cancel_consultation(c))
                actions_layout.addWidget(cancel_button)

            self.consultation_table.setCellWidget(row_position, 4, actions_cell)

        # Adjust row heights for better readability
        for row in range(self.consultation_table.rowCount()):
            self.consultation_table.setRowHeight(row, 50)

    def view_consultation_details(self, consultation):
        """
        Show consultation details in a dialog.
        """
        dialog = ConsultationDetailsDialog(consultation, self)
        dialog.exec_()

    def cancel_consultation(self, consultation):
        """
        Cancel a pending consultation.
        """
        reply = QMessageBox.question(
            self,
            "Cancel Consultation",
            f"Are you sure you want to cancel your consultation request with {consultation.faculty.name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Emit signal to cancel the consultation
            self.consultation_cancelled.emit(consultation.id)

class ConsultationDetailsDialog(QDialog):
    """
    Dialog to display consultation details.
    """
    def __init__(self, consultation, parent=None):
        super().__init__(parent)
        self.consultation = consultation
        self.init_ui()

    def init_ui(self):
        """
        Initialize the dialog UI with improved styling and layout.
        """
        self.setWindowTitle("Consultation Details")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setStyleSheet('''
            QDialog {
                background-color: #f8f9fa;
            }
            QLabel {
                font-size: 12pt;
                color: #2c3e50;
            }
            QLabel[heading="true"] {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            QLabel[subheading="true"] {
                font-size: 14pt;
                font-weight: bold;
                color: #3498db;
                margin-top: 15px;
            }
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
                padding: 15px;
            }
            QPushButton {
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12pt;
                font-weight: bold;
                color: white;
                background-color: #3498db;
                min-width: 120px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        ''')

        # Add shadow effect for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Title with improved styling
        title_layout = QHBoxLayout()

        title_label = QLabel("Consultation Details")
        title_label.setProperty("heading", "true")
        title_layout.addWidget(title_label)

        # Add status badge
        status_text = self.consultation.status.value.capitalize()
        status_badge = QLabel(status_text)

        # Set color based on status
        if self.consultation.status.value == "pending":
            status_color = "#f39c12"  # Orange
            bg_color = "#fff3e0"
        elif self.consultation.status.value == "accepted":
            status_color = "#2ecc71"  # Green
            bg_color = "#e8f5e9"
        elif self.consultation.status.value == "completed":
            status_color = "#3498db"  # Blue
            bg_color = "#e3f2fd"
        elif self.consultation.status.value == "cancelled":
            status_color = "#e74c3c"  # Red
            bg_color = "#ffebee"
        else:
            status_color = "#7f8c8d"  # Gray
            bg_color = "#f5f5f5"

        # Apply styling to the status badge
        status_badge.setStyleSheet(f"""
            background-color: {bg_color};
            color: {status_color};
            border: 1px solid {status_color};
            border-radius: 10px;
            padding: 5px 15px;
            font-weight: bold;
            font-size: 12pt;
        """)

        title_layout.addStretch()
        title_layout.addWidget(status_badge)

        layout.addLayout(title_layout)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #ddd; max-height: 1px; margin: 10px 0;")
        layout.addWidget(separator)

        # Details frame with improved styling
        details_frame = QFrame()
        details_layout = QFormLayout(details_frame)
        details_layout.setSpacing(15)
        details_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        details_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Add shadow to details frame
        frame_shadow = QGraphicsDropShadowEffect()
        frame_shadow.setBlurRadius(10)
        frame_shadow.setColor(QColor(0, 0, 0, 20))
        frame_shadow.setOffset(1, 1)
        details_frame.setGraphicsEffect(frame_shadow)

        # Faculty with improved styling
        faculty_label = QLabel("Faculty:")
        faculty_value = QLabel(self.consultation.faculty.name)
        faculty_value.setStyleSheet("font-weight: bold; font-size: 13pt;")
        details_layout.addRow(faculty_label, faculty_value)

        # Department with improved styling
        dept_label = QLabel("Department:")
        dept_value = QLabel(self.consultation.faculty.department)
        dept_value.setStyleSheet("color: #34495e;")
        details_layout.addRow(dept_label, dept_value)

        # Course with improved styling
        course_label = QLabel("Course:")
        course_value = QLabel(self.consultation.course_code if self.consultation.course_code else "N/A")
        course_value.setStyleSheet("color: #34495e;")
        details_layout.addRow(course_label, course_value)

        # Add a separator within the form
        form_separator = QFrame()
        form_separator.setFrameShape(QFrame.HLine)
        form_separator.setFrameShadow(QFrame.Sunken)
        form_separator.setStyleSheet("background-color: #eee; max-height: 1px; margin: 5px 0;")
        details_layout.addRow("", form_separator)

        # Requested date with improved formatting
        requested_label = QLabel("Requested:")
        requested_value = QLabel(self.consultation.requested_at.strftime("%B %d, %Y at %I:%M %p"))
        requested_value.setStyleSheet("color: #34495e;")
        details_layout.addRow(requested_label, requested_value)

        # Accepted date (if applicable) with improved formatting
        if self.consultation.accepted_at:
            accepted_label = QLabel("Accepted:")
            accepted_value = QLabel(self.consultation.accepted_at.strftime("%B %d, %Y at %I:%M %p"))
            accepted_value.setStyleSheet("color: #2ecc71; font-weight: bold;")
            details_layout.addRow(accepted_label, accepted_value)

        # Completed date (if applicable) with improved formatting
        if self.consultation.completed_at:
            completed_label = QLabel("Completed:")
            completed_value = QLabel(self.consultation.completed_at.strftime("%B %d, %Y at %I:%M %p"))
            completed_value.setStyleSheet("color: #3498db; font-weight: bold;")
            details_layout.addRow(completed_label, completed_value)

        layout.addWidget(details_frame)

        # Message section with improved styling
        message_label = QLabel("Consultation Details:")
        message_label.setProperty("subheading", "true")
        layout.addWidget(message_label)

        message_frame = QFrame()
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(15, 15, 15, 15)

        # Add shadow to message frame
        msg_shadow = QGraphicsDropShadowEffect()
        msg_shadow.setBlurRadius(10)
        msg_shadow.setColor(QColor(0, 0, 0, 20))
        msg_shadow.setOffset(1, 1)
        message_frame.setGraphicsEffect(msg_shadow)

        message_text = QLabel(self.consultation.request_message)
        message_text.setWordWrap(True)
        message_text.setStyleSheet("font-size: 13pt; line-height: 1.4;")
        message_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_layout.addWidget(message_text)

        layout.addWidget(message_frame)

        # Close button with improved styling
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")

        # Add shadow to button
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(10)
        btn_shadow.setColor(QColor(0, 0, 0, 50))
        btn_shadow.setOffset(2, 2)
        close_button.setGraphicsEffect(btn_shadow)

        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

class ConsultationPanel(QTabWidget):
    """
    Main consultation panel with request form and history tabs.
    Improved with better transitions and user feedback.
    """
    consultation_requested = pyqtSignal(object, str, str)
    consultation_cancelled = pyqtSignal(int)

    def __init__(self, student=None, parent=None):
        super().__init__(parent)
        self.student = student
        self.init_ui()

        # Set up auto-refresh timer for history panel
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_history)
        self.refresh_timer.start(60000)  # Refresh every minute

        # Connect tab change signal
        self.currentChanged.connect(self.on_tab_changed)

    def init_ui(self):
        """
        Initialize the consultation panel UI with improved styling and transitions.
        """
        self.setStyleSheet('''
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 10px;
                background-color: #f8f9fa;
                padding: 8px;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 3px;
                font-size: 13pt;
                min-width: 150px;
                text-align: center;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d0d0d0;
            }
            QTabBar {
                alignment: center;
            }
        ''')

        # Add shadow effect for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        # Request form tab with icon
        self.request_form = ConsultationRequestForm()
        self.request_form.request_submitted.connect(self.handle_consultation_request)
        self.addTab(self.request_form, "Request Consultation")

        # Set tab icon if available
        try:
            request_icon = QIcon("resources/icons/request.png")
            if not request_icon.isNull():
                self.setTabIcon(0, request_icon)
        except:
            # If icon not available, continue without it
            pass

        # History tab with icon
        self.history_panel = ConsultationHistoryPanel(self.student)
        self.history_panel.consultation_cancelled.connect(self.handle_consultation_cancel)
        self.addTab(self.history_panel, "Consultation History")

        # Set tab icon if available
        try:
            history_icon = QIcon("resources/icons/history.png")
            if not history_icon.isNull():
                self.setTabIcon(1, history_icon)
        except:
            # If icon not available, continue without it
            pass

        # Set minimum size for better usability
        self.setMinimumSize(800, 600)

        # Center the tab bar
        self.tabBar().setExpanding(True)

    def set_student(self, student):
        """
        Set the student for the consultation panel.
        """
        self.student = student
        self.history_panel.set_student(student)

        # Update window title with student name
        if student and hasattr(self.parent(), 'setWindowTitle'):
            self.parent().setWindowTitle(f"ConsultEase - {student.name}")

    def set_faculty(self, faculty):
        """
        Set the faculty for the consultation request.
        """
        self.request_form.set_faculty(faculty)

        # Animate transition to request form tab
        self.animate_tab_change(0)

    def set_faculty_options(self, faculty_list):
        """
        Set the available faculty options in the dropdown.
        """
        self.request_form.set_faculty_options(faculty_list)

        # Update status message if no faculty available
        if not faculty_list:
            QMessageBox.information(
                self,
                "No Faculty Available",
                "There are no faculty members available at this time. Please try again later."
            )

    def handle_consultation_request(self, faculty, message, course_code):
        """
        Handle consultation request submission.
        """
        try:
            # Emit signal to controller
            self.consultation_requested.emit(faculty, message, course_code)

            # Show success message
            QMessageBox.information(
                self,
                "Consultation Request Submitted",
                f"Your consultation request with {faculty.name} has been submitted successfully."
            )

            # Clear form fields
            self.request_form.message_input.clear()
            self.request_form.course_input.clear()

            # Refresh history
            self.history_panel.refresh_consultations()

            # Animate transition to history tab
            self.animate_tab_change(1)

        except Exception as e:
            logger.error(f"Error submitting consultation request: {str(e)}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to submit consultation request: {str(e)}"
            )

    def handle_consultation_cancel(self, consultation_id):
        """
        Handle consultation cancellation.
        """
        try:
            # Emit signal to controller
            self.consultation_cancelled.emit(consultation_id)

            # Show success message
            QMessageBox.information(
                self,
                "Consultation Cancelled",
                "Your consultation request has been cancelled successfully."
            )

            # Refresh history
            self.history_panel.refresh_consultations()

        except Exception as e:
            logger.error(f"Error cancelling consultation: {str(e)}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to cancel consultation: {str(e)}"
            )

    def animate_tab_change(self, tab_index):
        """
        Animate the transition to a different tab with smooth effects.

        Args:
            tab_index (int): The index of the tab to switch to
        """
        # Create fade-out effect for current widget
        current_widget = self.currentWidget()
        current_index = self.currentIndex()

        if current_index == tab_index:
            # No need to animate if we're already on the target tab
            return

        # Create opacity effect for fade animation
        opacity_effect = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(opacity_effect)

        # Create fade-out animation
        fade_out = QPropertyAnimation(opacity_effect, b"opacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.5)
        fade_out.setEasingCurve(QEasingCurve.OutQuad)

        # Function to execute after fade out
        def change_tab():
            # Set the current tab
            self.setCurrentIndex(tab_index)

            # Get the new current widget
            new_widget = self.currentWidget()

            # Create opacity effect for fade-in animation
            new_opacity_effect = QGraphicsOpacityEffect(new_widget)
            new_opacity_effect.setOpacity(0.5)
            new_widget.setGraphicsEffect(new_opacity_effect)

            # Create fade-in animation
            fade_in = QPropertyAnimation(new_opacity_effect, b"opacity")
            fade_in.setDuration(200)
            fade_in.setStartValue(0.5)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.InOutQuad)
            fade_in.start()

            # Highlight the tab
            self.highlight_tab(tab_index)

        # Connect the finished signal to change tab
        fade_out.finished.connect(change_tab)

        # Start the animation
        fade_out.start()

    def highlight_tab(self, tab_index):
        """
        Highlight a tab with a subtle animation effect.

        Args:
            tab_index (int): The index of the tab to highlight
        """
        # Store original text color
        current_style = self.tabBar().tabTextColor(tab_index)

        # Create a timer to reset the color after a brief flash
        def reset_color():
            self.tabBar().setTabTextColor(tab_index, current_style)

        # Set highlight color
        self.tabBar().setTabTextColor(tab_index, QColor("#2980b9"))

        # Reset after a short delay
        QTimer.singleShot(500, reset_color)

    def on_tab_changed(self, index):
        """
        Handle tab change events.

        Args:
            index (int): The index of the newly selected tab
        """
        # Refresh history when switching to history tab
        if index == 1:  # History tab
            self.history_panel.refresh_consultations()

    def auto_refresh_history(self):
        """
        Automatically refresh the history panel periodically.
        """
        # Only refresh if the history tab is visible
        if self.currentIndex() == 1:
            self.history_panel.refresh_consultations()

    def refresh_history(self):
        """
        Refresh the consultation history.
        """
        self.history_panel.refresh_consultations()
