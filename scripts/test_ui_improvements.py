#!/usr/bin/env python3
"""
ConsultEase - UI Improvements Test Script

This script tests the improved UI components, particularly the transitions and
consultation panel improvements.

Usage:
    python test_ui_improvements.py
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer

# Add parent directory to path so we can import from central_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import ConsultEase components
try:
    from central_system.utils.transitions import WindowTransitionManager
    from central_system.views.consultation_panel import ConsultationPanel
    from central_system.models.faculty import Faculty
    from central_system.models.student import Student
    logger.info("Successfully imported ConsultEase components")
except ImportError as e:
    logger.error(f"Failed to import ConsultEase components: {e}")
    sys.exit(1)

class TestWindow(QMainWindow):
    """Test window for UI improvements."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Create transition manager
        self.transition_manager = WindowTransitionManager()
        
        # Create test data
        self.create_test_data()
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("ConsultEase UI Improvements Test")
        self.setGeometry(100, 100, 1000, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("ConsultEase UI Improvements Test")
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Test buttons
        self.test_transitions_button = QPushButton("Test Transitions")
        self.test_transitions_button.clicked.connect(self.test_transitions)
        self.test_transitions_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14pt;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        main_layout.addWidget(self.test_transitions_button)
        
        self.test_consultation_panel_button = QPushButton("Test Consultation Panel")
        self.test_consultation_panel_button.clicked.connect(self.test_consultation_panel)
        self.test_consultation_panel_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-size: 14pt;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        main_layout.addWidget(self.test_consultation_panel_button)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 12pt; color: #7f8c8d;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Set spacing
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(50, 50, 50, 50)
    
    def create_test_data(self):
        """Create test data for the UI components."""
        # Create test faculty
        self.test_faculty = [
            Faculty(id=1, name="Dr. John Smith", department="Computer Science", status=True),
            Faculty(id=2, name="Dr. Jane Doe", department="Mathematics", status=True),
            Faculty(id=3, name="Prof. Bob Johnson", department="Physics", status=False)
        ]
        
        # Create test student
        self.test_student = Student(id=1, name="Test Student", email="test@example.com")
    
    def test_transitions(self):
        """Test the improved transitions."""
        self.status_label.setText("Testing transitions...")
        
        # Create test windows
        window1 = QWidget()
        window1.setWindowTitle("Window 1")
        window1.setStyleSheet("background-color: #3498db;")
        window1.resize(600, 400)
        
        window2 = QWidget()
        window2.setWindowTitle("Window 2")
        window2.setStyleSheet("background-color: #2ecc71;")
        window2.resize(600, 400)
        
        # Show first window
        window1.show()
        
        # Schedule transition to second window
        QTimer.singleShot(2000, lambda: self.transition_to_window2(window1, window2))
    
    def transition_to_window2(self, window1, window2):
        """Transition from window1 to window2."""
        self.status_label.setText("Transitioning to Window 2...")
        self.transition_manager.fade_out_in(window1, window2)
        
        # Schedule transition back to window1
        QTimer.singleShot(2000, lambda: self.transition_to_window1(window2, window1))
    
    def transition_to_window1(self, window2, window1):
        """Transition from window2 to window1."""
        self.status_label.setText("Transitioning to Window 1...")
        self.transition_manager.fade_out_in(window2, window1)
        
        # Schedule closing of windows
        QTimer.singleShot(2000, lambda: self.close_test_windows(window1, window2))
    
    def close_test_windows(self, window1, window2):
        """Close the test windows."""
        window1.close()
        window2.close()
        self.status_label.setText("Transition test completed")
    
    def test_consultation_panel(self):
        """Test the improved consultation panel."""
        self.status_label.setText("Testing consultation panel...")
        
        # Create consultation panel
        panel = ConsultationPanel(self.test_student)
        panel.setWindowTitle("Consultation Panel Test")
        panel.resize(800, 600)
        
        # Set faculty options
        panel.set_faculty_options(self.test_faculty)
        
        # Show the panel
        panel.show()

def main():
    """Main function."""
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
