"""
Script to update the Jeysibn faculty member to be always available.
This script should be run after updating the database schema.
"""

import sys
import os
import logging

# Add parent directory to path to help with imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import models
from central_system.models import Faculty, init_db, get_db
from central_system.controllers import FacultyController

def update_jeysibn_faculty():
    """
    Update the Jeysibn faculty member to be always available.
    """
    try:
        # Initialize database
        init_db()
        
        # Get database connection
        db = get_db()
        
        # Check if faculty with name "Jeysibn" exists
        faculty = db.query(Faculty).filter(Faculty.name == "Jeysibn").first()
        
        if faculty:
            logger.info(f"Faculty 'Jeysibn' found with ID: {faculty.id}")
            
            # Update always_available flag
            faculty.always_available = True
            faculty.status = True  # Set to available
            db.commit()
            
            logger.info(f"Updated faculty 'Jeysibn' to be always available")
            return faculty
        else:
            logger.info("Faculty 'Jeysibn' not found, creating new faculty")
            
            # Create faculty controller
            faculty_controller = FacultyController()
            
            # Create new faculty
            faculty = faculty_controller.add_faculty(
                name="Jeysibn",
                department="Computer Science",
                email="jeysibn@university.edu",
                ble_id="4fafc201-1fb5-459e-8fcc-c5c9c331914b",  # Match the SERVICE_UUID in the faculty desk unit code
                always_available=True  # Set to always available
            )
            
            if faculty:
                logger.info(f"Created faculty 'Jeysibn' with ID: {faculty.id}")
            else:
                logger.error("Failed to create faculty 'Jeysibn'")
            
            return faculty
    except Exception as e:
        logger.error(f"Error updating faculty: {str(e)}")
        return None

if __name__ == "__main__":
    # Update Jeysibn faculty
    faculty = update_jeysibn_faculty()
    
    if faculty:
        logger.info("Successfully updated Jeysibn faculty to be always available.")
        logger.info(f"Faculty: {faculty.name} (ID: {faculty.id})")
        logger.info(f"Always Available: {faculty.always_available}")
        logger.info(f"Status: {faculty.status}")
    else:
        logger.error("Failed to update Jeysibn faculty.")
