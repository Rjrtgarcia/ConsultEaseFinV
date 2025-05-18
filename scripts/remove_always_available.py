"""
Script to remove the always_available mode from all faculty members.
This script should be run after updating the faculty desk unit config.
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

def remove_always_available_mode():
    """
    Remove the always_available mode from all faculty members.
    """
    try:
        # Initialize database
        init_db()
        
        # Get database connection
        db = get_db()
        
        # Get all faculty members with always_available=True
        faculty_list = db.query(Faculty).filter(Faculty.always_available == True).all()
        
        if not faculty_list:
            logger.info("No faculty members with always_available=True found")
            return True
        
        logger.info(f"Found {len(faculty_list)} faculty members with always_available=True")
        
        # Update each faculty member
        for faculty in faculty_list:
            logger.info(f"Updating faculty: {faculty.name} (ID: {faculty.id})")
            
            # Set always_available to False
            faculty.always_available = False
            
            # Status will now be determined by BLE connection
            # We'll keep the current status for now
            logger.info(f"  - always_available: {faculty.always_available}")
            logger.info(f"  - status: {faculty.status}")
        
        # Commit changes
        db.commit()
        logger.info("Successfully updated all faculty members")
        
        return True
    except Exception as e:
        logger.error(f"Error removing always_available mode: {str(e)}")
        return False

if __name__ == "__main__":
    # Remove always_available mode
    success = remove_always_available_mode()
    
    if success:
        logger.info("Successfully removed always_available mode from all faculty members.")
    else:
        logger.error("Failed to remove always_available mode.")
