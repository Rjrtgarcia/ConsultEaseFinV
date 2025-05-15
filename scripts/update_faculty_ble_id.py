#!/usr/bin/env python3
"""
Script to update the BLE ID for faculty members to match the correct UUID.
This is part of fixing the BLE connection status updates.
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

def update_faculty_ble_id():
    """
    Update the BLE ID for faculty members to match the correct UUID.
    """
    try:
        db = get_db()
        
        # Get faculty with name "Jeysibn"
        faculty = db.query(Faculty).filter(Faculty.name == "Jeysibn").first()
        
        if faculty:
            # Update BLE ID to match the BLE beacon's UUID
            old_ble_id = faculty.ble_id
            new_ble_id = "91BAD35B-F3CB-4FC1-8603-88D5137892A6"
            
            faculty.ble_id = new_ble_id
            db.commit()
            
            logger.info(f"Updated faculty {faculty.name} (ID: {faculty.id}) BLE ID from {old_ble_id} to {new_ble_id}")
            return faculty
        else:
            logger.error("Faculty 'Jeysibn' not found in database")
            return None
    except Exception as e:
        logger.error(f"Error updating faculty BLE ID: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("Starting update of faculty BLE ID")
    faculty = update_faculty_ble_id()
    if faculty:
        logger.info(f"Successfully updated faculty BLE ID for {faculty.name} (ID: {faculty.id})")
    else:
        logger.error("Failed to update faculty BLE ID")
    logger.info("Finished update of faculty BLE ID")
