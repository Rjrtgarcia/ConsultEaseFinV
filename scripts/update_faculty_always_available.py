#!/usr/bin/env python3
"""
Script to update all faculty members to set always_available to False.
This is part of removing the "always on" functionality for faculty consultation availability.
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import from central_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from central_system.models import Faculty, get_db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_faculty_always_available():
    """
    Update all faculty members to set always_available to False.
    """
    try:
        db = get_db()
        
        # Get all faculty members
        faculties = db.query(Faculty).all()
        
        # Count of updated faculty members
        updated_count = 0
        
        # Update each faculty member
        for faculty in faculties:
            if faculty.always_available:
                faculty.always_available = False
                updated_count += 1
                logger.info(f"Updated faculty {faculty.name} (ID: {faculty.id}) to set always_available to False")
        
        # Commit changes
        db.commit()
        
        logger.info(f"Updated {updated_count} faculty members to set always_available to False")
        return updated_count
    except Exception as e:
        logger.error(f"Error updating faculty always_available: {str(e)}")
        return 0

if __name__ == "__main__":
    logger.info("Starting update of faculty always_available")
    update_faculty_always_available()
    logger.info("Finished update of faculty always_available")
