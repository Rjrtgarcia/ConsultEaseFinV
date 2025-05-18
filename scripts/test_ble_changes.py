"""
Test script for BLE functionality changes.

This script tests the BLE functionality changes in the ConsultEase system.
It verifies that faculty availability is correctly determined by BLE connection status.
"""

import sys
import os
import logging
import time
import argparse

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

# Import models and services
from central_system.models import Faculty, init_db, get_db
from central_system.services import get_mqtt_service
from central_system.controllers import FacultyController
from central_system.utils.mqtt_topics import MQTTTopics

def test_faculty_status_update():
    """
    Test faculty status update based on BLE connection.
    """
    try:
        # Initialize database
        init_db()
        
        # Get database connection
        db = get_db()
        
        # Get MQTT service
        mqtt_service = get_mqtt_service()
        
        # Connect to MQTT broker
        if not mqtt_service.is_connected:
            mqtt_service.connect()
            logger.info("Connected to MQTT broker")
        
        # Get all faculty members
        faculty_list = db.query(Faculty).all()
        
        if not faculty_list:
            logger.error("No faculty members found")
            return False
        
        logger.info(f"Found {len(faculty_list)} faculty members")
        
        # Test each faculty member
        for faculty in faculty_list:
            logger.info(f"Testing faculty: {faculty.name} (ID: {faculty.id})")
            
            # Verify always_available is False
            if faculty.always_available:
                logger.error(f"Faculty {faculty.name} has always_available=True")
                return False
            
            # Get current status
            current_status = faculty.status
            logger.info(f"  - Current status: {current_status}")
            
            # Test BLE connection (simulate keychain_connected)
            logger.info(f"  - Simulating BLE connection for faculty {faculty.name}")
            
            # Publish to faculty-specific topic
            topic = MQTTTopics.get_faculty_status_topic(faculty.id)
            mqtt_service.publish_raw(topic, "keychain_connected")
            
            # Also publish to legacy topic for backward compatibility
            mqtt_service.publish_raw(MQTTTopics.LEGACY_FACULTY_STATUS, "keychain_connected")
            
            # Wait for status update
            logger.info("  - Waiting for status update...")
            time.sleep(2)
            
            # Refresh faculty from database
            db.expire(faculty)
            faculty = db.query(Faculty).filter(Faculty.id == faculty.id).first()
            
            # Verify status is True
            if not faculty.status:
                logger.error(f"Faculty {faculty.name} status not updated to True after BLE connection")
                return False
            
            logger.info(f"  - Status after BLE connection: {faculty.status}")
            
            # Test BLE disconnection (simulate keychain_disconnected)
            logger.info(f"  - Simulating BLE disconnection for faculty {faculty.name}")
            
            # Publish to faculty-specific topic
            mqtt_service.publish_raw(topic, "keychain_disconnected")
            
            # Also publish to legacy topic for backward compatibility
            mqtt_service.publish_raw(MQTTTopics.LEGACY_FACULTY_STATUS, "keychain_disconnected")
            
            # Wait for status update
            logger.info("  - Waiting for status update...")
            time.sleep(2)
            
            # Refresh faculty from database
            db.expire(faculty)
            faculty = db.query(Faculty).filter(Faculty.id == faculty.id).first()
            
            # Verify status is False
            if faculty.status:
                logger.error(f"Faculty {faculty.name} status not updated to False after BLE disconnection")
                return False
            
            logger.info(f"  - Status after BLE disconnection: {faculty.status}")
            
            # Restore original status
            faculty.status = current_status
            db.commit()
            logger.info(f"  - Restored original status: {current_status}")
        
        logger.info("All faculty members tested successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing faculty status update: {str(e)}")
        return False

def main():
    """
    Main function to run tests.
    """
    parser = argparse.ArgumentParser(description='ConsultEase BLE Changes Test')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Run tests
    logger.info("Starting BLE changes tests")
    
    # Test faculty status update
    logger.info("Testing faculty status update based on BLE connection")
    if test_faculty_status_update():
        logger.info("Faculty status update test passed")
    else:
        logger.error("Faculty status update test failed")
        return
    
    logger.info("All tests passed successfully")

if __name__ == "__main__":
    main()
