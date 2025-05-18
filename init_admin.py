"""
Initialize the database and create a default admin user.
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to help with imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Set environment variables
os.environ['DB_TYPE'] = 'sqlite'
os.environ['DB_PATH'] = 'consultease.db'

# Import models and controllers
from central_system.models import init_db, Admin, get_db
from central_system.controllers import AdminController

def main():
    """Initialize the database and create a default admin user."""
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Create admin controller
        admin_controller = AdminController()
        
        # Check if admin exists
        db = get_db()
        admin_count = db.query(Admin).count()
        
        if admin_count > 0:
            logger.info(f"Found {admin_count} existing admin users")
            admins = db.query(Admin).all()
            for admin in admins:
                logger.info(f"Admin: {admin.username} (ID: {admin.id}, Active: {admin.is_active})")
        else:
            logger.info("No admin users found, creating default admin")
            
            # Create default admin
            default_username = "admin"
            default_password = "admin123"
            
            # Create admin
            admin = admin_controller.create_admin(default_username, default_password)
            
            if admin:
                logger.info(f"Created default admin: {admin.username} (ID: {admin.id})")
                logger.warning(
                    "Created default admin user with username 'admin' and password 'admin123'. "
                    "Please change this password immediately!"
                )
            else:
                logger.error("Failed to create default admin")
        
        # Close database connection
        db.close()
        
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
