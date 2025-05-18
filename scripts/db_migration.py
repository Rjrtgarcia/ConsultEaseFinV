"""
Database migration script for ConsultEase.

This script performs the following migrations:
1. Updates all faculty members to set always_available=False
2. Updates faculty status based on BLE connection status
"""

import sys
import os
import logging
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

# Import models
from central_system.models import Faculty, init_db, get_db

def migrate_faculty_always_available():
    """
    Migrate faculty always_available flag to False for all faculty members.
    """
    try:
        # Initialize database
        init_db()
        
        # Get database connection
        db = get_db()
        
        # Get all faculty members
        faculty_list = db.query(Faculty).all()
        
        if not faculty_list:
            logger.info("No faculty members found")
            return True
        
        logger.info(f"Found {len(faculty_list)} faculty members")
        
        # Update each faculty member
        for faculty in faculty_list:
            logger.info(f"Processing faculty: {faculty.name} (ID: {faculty.id})")
            
            # Check if always_available is True
            if faculty.always_available:
                logger.info(f"  - Setting always_available=False for faculty: {faculty.name}")
                faculty.always_available = False
                
                # Keep current status for now
                logger.info(f"  - Current status: {faculty.status}")
            else:
                logger.info(f"  - Faculty {faculty.name} already has always_available=False")
        
        # Commit changes
        db.commit()
        logger.info("Successfully updated all faculty members")
        
        return True
    except Exception as e:
        logger.error(f"Error migrating faculty always_available: {str(e)}")
        return False

def main():
    """
    Main function to run migrations.
    """
    parser = argparse.ArgumentParser(description='ConsultEase Database Migration')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Performing dry run - no changes will be made")
        # TODO: Implement dry run functionality
        return
    
    # Run migrations
    logger.info("Starting database migrations")
    
    # Migrate faculty always_available
    logger.info("Migrating faculty always_available flag")
    if migrate_faculty_always_available():
        logger.info("Successfully migrated faculty always_available flag")
    else:
        logger.error("Failed to migrate faculty always_available flag")
        return
    
    logger.info("All migrations completed successfully")

if __name__ == "__main__":
    main()
