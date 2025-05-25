import logging
from ..models import Admin, get_db
from ..utils.config_manager import validate_password

# Set up logging
logger = logging.getLogger(__name__)

class AdminController:
    """
    Controller for handling admin authentication and management.
    """

    def __init__(self):
        """
        Initialize the admin controller.
        """
        self.current_admin = None

    def authenticate(self, username, password):
        """
        Authenticate an admin user.

        Args:
            username (str): Admin username
            password (str): Admin password

        Returns:
            Admin: Admin object if authenticated, None otherwise
        """
        try:
            db = get_db()
            admin = db.query(Admin).filter(Admin.username == username, Admin.is_active == True).first()

            if not admin:
                logger.warning(f"Admin not found or inactive: {username}")
                return None

            if admin.check_password(password):
                logger.info(f"Admin authenticated: {username}")
                self.current_admin = admin
                return admin
            else:
                logger.warning(f"Invalid password for admin: {username}")
                return None
        except Exception as e:
            logger.error(f"Error authenticating admin: {str(e)}")
            return None

    def create_admin(self, username, password):
        """
        Create a new admin user with password validation.

        Args:
            username (str): Admin username
            password (str): Admin password

        Returns:
            tuple: (Admin object or None, list of validation errors)
        """
        try:
            # Validate password
            is_valid, validation_errors = validate_password(password)
            if not is_valid:
                logger.warning(f"Password validation failed for admin {username}: {validation_errors}")
                return None, validation_errors

            db = get_db()

            # Check if username already exists
            existing = db.query(Admin).filter(Admin.username == username).first()
            if existing:
                error_msg = f"Admin with username {username} already exists"
                logger.error(error_msg)
                return None, [error_msg]

            # Hash password
            password_hash, salt = Admin.hash_password(password)

            # Create new admin
            admin = Admin(
                username=username,
                password_hash=password_hash,
                salt=salt,
                is_active=True
            )

            db.add(admin)
            db.commit()

            logger.info(f"Created new admin: {admin.username} (ID: {admin.id})")

            return admin, []
        except Exception as e:
            error_msg = f"Error creating admin: {str(e)}"
            logger.error(error_msg)
            return None, [error_msg]

    def get_all_admins(self):
        """
        Get all admin users.

        Returns:
            list: List of Admin objects
        """
        try:
            db = get_db()
            admins = db.query(Admin).all()
            return admins
        except Exception as e:
            logger.error(f"Error getting admins: {str(e)}")
            return []

    def change_password(self, admin_id, old_password, new_password):
        """
        Change an admin user's password with validation.

        Args:
            admin_id (int): Admin ID
            old_password (str): Current password
            new_password (str): New password

        Returns:
            tuple: (bool success, list of validation errors)
        """
        try:
            # Validate new password
            is_valid, validation_errors = validate_password(new_password)
            if not is_valid:
                logger.warning(f"New password validation failed for admin {admin_id}: {validation_errors}")
                return False, validation_errors

            db = get_db()
            admin = db.query(Admin).filter(Admin.id == admin_id).first()

            if not admin:
                error_msg = f"Admin not found: {admin_id}"
                logger.error(error_msg)
                return False, [error_msg]

            # Verify old password
            if not admin.check_password(old_password):
                error_msg = f"Invalid old password for admin: {admin.username}"
                logger.warning(error_msg)
                return False, [error_msg]

            # Hash new password
            password_hash, salt = Admin.hash_password(new_password)

            # Update admin
            admin.password_hash = password_hash
            admin.salt = salt

            db.commit()

            logger.info(f"Changed password for admin: {admin.username}")

            return True, []
        except Exception as e:
            error_msg = f"Error changing admin password: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]

    def change_username(self, admin_id, password, new_username):
        """
        Change an admin user's username.

        Args:
            admin_id (int): Admin ID
            password (str): Current password for verification
            new_username (str): New username

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            admin = db.query(Admin).filter(Admin.id == admin_id).first()

            if not admin:
                logger.error(f"Admin not found: {admin_id}")
                return False

            # Verify password
            if not admin.check_password(password):
                logger.warning(f"Invalid password for admin: {admin.username}")
                return False

            # Check if new username already exists
            existing = db.query(Admin).filter(Admin.username == new_username).first()
            if existing and existing.id != admin_id:
                logger.error(f"Admin with username {new_username} already exists")
                return False

            # Store old username for logging
            old_username = admin.username

            # Update admin
            admin.username = new_username

            db.commit()

            logger.info(f"Changed username for admin from {old_username} to {new_username}")

            return True
        except Exception as e:
            logger.error(f"Error changing admin username: {str(e)}")
            return False

    def deactivate_admin(self, admin_id):
        """
        Deactivate an admin user.

        Args:
            admin_id (int): Admin ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            admin = db.query(Admin).filter(Admin.id == admin_id).first()

            if not admin:
                logger.error(f"Admin not found: {admin_id}")
                return False

            # Check if this is the last active admin
            active_count = db.query(Admin).filter(Admin.is_active == True).count()
            if active_count <= 1 and admin.is_active:
                logger.error(f"Cannot deactivate the last active admin: {admin.username}")
                return False

            admin.is_active = False
            db.commit()

            logger.info(f"Deactivated admin: {admin.username}")

            return True
        except Exception as e:
            logger.error(f"Error deactivating admin: {str(e)}")
            return False

    def activate_admin(self, admin_id):
        """
        Activate an admin user.

        Args:
            admin_id (int): Admin ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            admin = db.query(Admin).filter(Admin.id == admin_id).first()

            if not admin:
                logger.error(f"Admin not found: {admin_id}")
                return False

            admin.is_active = True
            db.commit()

            logger.info(f"Activated admin: {admin.username}")

            return True
        except Exception as e:
            logger.error(f"Error activating admin: {str(e)}")
            return False

    def is_authenticated(self):
        """
        Check if an admin is currently authenticated.

        Returns:
            bool: True if authenticated, False otherwise
        """
        return self.current_admin is not None

    def logout(self):
        """
        Log out the current admin.
        """
        self.current_admin = None
        logger.info("Admin logged out")

    def ensure_default_admin(self):
        """
        Ensure that at least one admin user exists in the system.
        Creates a default admin if none exist.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            admin_count = db.query(Admin).count()

            if admin_count == 0:
                logger.info("No admin users found, creating default admin")

                # Create default admin with stronger password
                default_username = "admin"
                default_password = "Admin123!"  # Meets password requirements

                admin, errors = self.create_admin(default_username, default_password)

                if admin:
                    logger.warning(
                        "Created default admin user with username 'admin' and password 'Admin123!'. "
                        "Please change this password immediately!"
                    )
                else:
                    logger.error(f"Failed to create default admin: {errors}")
                    return False

                return True

            return False
        except Exception as e:
            logger.error(f"Error ensuring default admin: {str(e)}")
            return False