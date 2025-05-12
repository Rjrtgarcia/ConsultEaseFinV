"""
Script to update the faculty table schema to include the always_available field.
This script should be run after updating the code to ensure existing databases
are compatible with the new schema.
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

def update_sqlite_schema():
    """
    Update the SQLite database schema to include the always_available field.
    """
    try:
        import sqlite3
        from central_system.models.base import DB_PATH
        
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the always_available column already exists
        cursor.execute("PRAGMA table_info(faculty)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'always_available' not in column_names:
            logger.info("Adding always_available column to faculty table in SQLite database")
            cursor.execute("ALTER TABLE faculty ADD COLUMN always_available BOOLEAN DEFAULT 0")
            
            # Update Jeysibn to be always available
            cursor.execute("UPDATE faculty SET always_available = 1 WHERE name = 'Jeysibn'")
            
            conn.commit()
            logger.info("SQLite schema update completed successfully")
        else:
            logger.info("always_available column already exists in faculty table")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating SQLite schema: {str(e)}")
        return False

def update_postgresql_schema():
    """
    Update the PostgreSQL database schema to include the always_available field.
    """
    try:
        import psycopg2
        from central_system.models.base import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
        
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Check if the always_available column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'faculty' AND column_name = 'always_available'
        """)
        column_exists = cursor.fetchone() is not None
        
        if not column_exists:
            logger.info("Adding always_available column to faculty table in PostgreSQL database")
            cursor.execute("ALTER TABLE faculty ADD COLUMN always_available BOOLEAN DEFAULT FALSE")
            
            # Update Jeysibn to be always available
            cursor.execute("UPDATE faculty SET always_available = TRUE WHERE name = 'Jeysibn'")
            
            conn.commit()
            logger.info("PostgreSQL schema update completed successfully")
        else:
            logger.info("always_available column already exists in faculty table")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating PostgreSQL schema: {str(e)}")
        return False

def main():
    """
    Main function to update the database schema.
    """
    # Determine database type
    db_type = os.environ.get('DB_TYPE', 'sqlite').lower()
    
    if db_type == 'sqlite':
        logger.info("Updating SQLite database schema")
        success = update_sqlite_schema()
    else:
        logger.info("Updating PostgreSQL database schema")
        success = update_postgresql_schema()
    
    if success:
        logger.info("Database schema update completed successfully")
    else:
        logger.error("Database schema update failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
