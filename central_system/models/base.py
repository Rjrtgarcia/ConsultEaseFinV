from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import os
import urllib.parse
import getpass
import logging
import time
import functools

# Set up logging (configuration handled centrally in main.py)
logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Custom exception for database connection failures."""
    pass


class DatabaseOperationError(Exception):
    """Custom exception for database operation failures."""
    pass


# Import configuration system
from ..config import get_config

# Get configuration
config = get_config()

# Database connection settings
DB_TYPE = config.get('database.type', 'sqlite')  # Default to SQLite for development

if DB_TYPE.lower() == 'sqlite':
    # Use SQLite for development/testing
    DB_PATH = config.get('database.path', 'consultease.db')
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    logger.info(f"Connecting to SQLite database: {DB_PATH}")
else:
    # Get current username - this will match PostgreSQL's peer authentication on Linux
    current_user = getpass.getuser()

    # PostgreSQL connection settings
    DB_USER = config.get('database.user', current_user)
    DB_PASSWORD = config.get('database.password', '')  # Empty password for peer authentication
    DB_HOST = config.get('database.host', 'localhost')
    DB_PORT = config.get('database.port', 5432)  # Default PostgreSQL port
    DB_NAME = config.get('database.name', 'consultease')

    # Create PostgreSQL connection URL
    if DB_HOST == 'localhost' and not DB_PASSWORD:
        # Use Unix socket connection for peer authentication
        DATABASE_URL = f"postgresql+psycopg2://{DB_USER}@/{DB_NAME}"
        logger.info(f"Connecting to PostgreSQL database: {DB_NAME} as {DB_USER} using peer authentication")
    else:
        # Use TCP connection with password
        encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
        DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        logger.info(f"Connecting to PostgreSQL database: {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}")

# Configure connection pooling options with sensible defaults
pool_size = config.get('database.pool_size', 5)
max_overflow = config.get('database.max_overflow', 10)
pool_timeout = config.get('database.pool_timeout', 30)
pool_recycle = config.get('database.pool_recycle', 1800)  # Recycle connections after 30 minutes

# Create engine with connection pooling
if DB_TYPE.lower() == 'sqlite':
    # SQLite doesn't support the same level of connection pooling
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Allow SQLite to be used across threads
    )
    logger.info("Created SQLite engine with thread safety enabled")
else:
    # PostgreSQL with full connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True  # Check connection validity before using it
    )
    logger.info(f"Created PostgreSQL engine with connection pooling (size={pool_size}, max_overflow={max_overflow})")

# Create session factory with thread safety
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(session_factory)

# Create base class for models
Base = declarative_base()

def get_db(force_new=False, max_retries=3):
    """
    Get database session from the connection pool with enhanced error handling.

    Args:
        force_new (bool): If True, create a new session even if one exists
        max_retries (int): Maximum number of retry attempts for connection failures

    Returns:
        SQLAlchemy session: A database session from the connection pool

    Raises:
        DatabaseConnectionError: When unable to establish database connection
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            # Get a session from the pool
            db = SessionLocal()

            # Enhanced connection test with health check
            try:
                result = db.execute("SELECT 1 as health_check")
                health_check = result.fetchone()
                if not health_check or health_check[0] != 1:
                    raise DatabaseConnectionError("Health check failed")
                logger.debug(f"Database connection test successful (attempt {attempt + 1})")
            except Exception as test_error:
                db.close()
                logger.warning(f"Database connection test failed: {test_error}")

                # Implement exponential backoff for retries
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 30)  # Max 30 seconds
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    raise DatabaseConnectionError(f"Database connection test failed after {max_retries} attempts: {test_error}")

            # If force_new is True, ensure we're getting fresh data
            if force_new:
                # Expire all objects in the session to force a refresh from the database
                db.expire_all()

            # Log connection acquisition for debugging
            logger.debug(f"Acquired database connection from pool (attempt {attempt + 1})")

            return db

        except Exception as e:
            last_error = e
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {str(e)}")

            # If we got a session but there was an error, make sure to close it
            if 'db' in locals():
                try:
                    db.close()
                except:
                    pass  # Ignore errors during cleanup

            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 10)  # Max 10 seconds
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

    # All retries failed
    error_msg = f"Failed to establish database connection after {max_retries} attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise DatabaseConnectionError(error_msg)

def close_db():
    """
    Remove the current session and return the connection to the pool.
    This should be called when the session is no longer needed.
    """
    try:
        SessionLocal.remove()
        logger.debug("Released database connection back to pool")
    except Exception as e:
        logger.error(f"Error releasing database connection: {str(e)}")

def db_operation_with_retry(max_retries=3, retry_delay=0.5):
    """
    Decorator for database operations with retry logic.

    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (float): Initial delay between retries in seconds (will increase exponentially)

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None

            while retries < max_retries:
                db = get_db()
                try:
                    # Call the original function with the db session and all arguments
                    result = func(db, *args, **kwargs)
                    db.commit()
                    return result
                except Exception as e:
                    db.rollback()
                    last_error = e
                    retries += 1

                    # Log the error
                    if retries < max_retries:
                        logger.warning(f"Database operation failed (attempt {retries}/{max_retries}): {e}")
                        # Exponential backoff
                        sleep_time = retry_delay * (2 ** (retries - 1))
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                finally:
                    db.close()

            # If we've exhausted all retries, raise the last error
            raise last_error

        return wrapper

    return decorator

def _create_performance_indexes():
    """
    Create database indexes for frequently queried fields to improve performance.
    This is especially important for Raspberry Pi deployment where query speed matters.
    """
    try:
        # Get database connection
        db = get_db()

        # Define indexes for performance optimization
        indexes = [
            # Student table indexes
            "CREATE INDEX IF NOT EXISTS idx_student_rfid_uid ON students(rfid_uid);",
            "CREATE INDEX IF NOT EXISTS idx_student_name ON students(name);",
            "CREATE INDEX IF NOT EXISTS idx_student_department ON students(department);",

            # Faculty table indexes
            "CREATE INDEX IF NOT EXISTS idx_faculty_ble_id ON faculty(ble_id);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_status ON faculty(status);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_department ON faculty(department);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_name ON faculty(name);",

            # Consultation table indexes
            "CREATE INDEX IF NOT EXISTS idx_consultation_student_id ON consultations(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_faculty_id ON consultations(faculty_id);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_status ON consultations(status);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_created_at ON consultations(created_at);",

            # Admin table indexes
            "CREATE INDEX IF NOT EXISTS idx_admin_username ON admins(username);",
            "CREATE INDEX IF NOT EXISTS idx_admin_is_active ON admins(is_active);",

            # Composite indexes for common query patterns
            "CREATE INDEX IF NOT EXISTS idx_consultation_student_status ON consultations(student_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_faculty_status ON consultations(faculty_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_status_department ON faculty(status, department);",
        ]

        # Execute index creation
        for index_sql in indexes:
            try:
                db.execute(index_sql)
                logger.debug(f"Created index: {index_sql.split()[5]}")  # Extract index name
            except Exception as e:
                # Log but don't fail - indexes might already exist
                logger.debug(f"Index creation skipped (likely already exists): {e}")

        db.commit()
        logger.info("Database performance indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating performance indexes: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()

def _ensure_admin_account_integrity():
    """
    Ensure admin account exists and is properly configured.
    This function performs comprehensive admin account validation and repair.

    Returns:
        bool: True if admin account is ready, False if there were unrecoverable errors
    """
    db = None
    try:
        # Import models here to avoid circular imports
        from .admin import Admin

        db = get_db()

        # Check for existing admin accounts
        admin_accounts = db.query(Admin).all()
        default_admin = db.query(Admin).filter(Admin.username == "admin").first()

        logger.info(f"Admin account integrity check: Found {len(admin_accounts)} admin account(s)")

        # Case 1: No admin accounts exist at all
        if len(admin_accounts) == 0:
            logger.warning("No admin accounts found - creating default admin account")
            return _create_default_admin(db)

        # Case 2: Default admin doesn't exist but other admins do
        elif not default_admin:
            logger.warning("Default 'admin' account not found - creating it")
            return _create_default_admin(db)

        # Case 3: Default admin exists - validate and fix if needed
        else:
            logger.info("Default admin account found - validating configuration")
            return _validate_and_fix_admin(db, default_admin)

    except Exception as e:
        logger.error(f"Critical error during admin account integrity check: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()

def _create_default_admin(db):
    """
    Create the default admin account with secure settings.

    Args:
        db: Database session

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from .admin import Admin

        # Create default admin with temporary password that must be changed
        password_hash, salt = Admin.hash_password("TempPass123!")
        default_admin = Admin(
            username="admin",
            password_hash=password_hash,
            salt=salt,
            email="admin@consultease.com",
            is_active=True,
            force_password_change=True  # Force password change on first login
        )

        db.add(default_admin)
        db.commit()

        logger.warning("✅ Created default admin account successfully")
        logger.warning("🔑 Default credentials: admin / TempPass123!")
        logger.warning("⚠️  SECURITY NOTICE: This password MUST be changed on first login!")

        # Verify the account was created correctly
        return _test_admin_login(default_admin, "TempPass123!")

    except Exception as e:
        logger.error(f"Failed to create default admin account: {e}")
        db.rollback()
        return False

def _validate_and_fix_admin(db, admin):
    """
    Validate and fix the existing default admin account.

    Args:
        db: Database session
        admin: Admin account object

    Returns:
        bool: True if admin is valid/fixed, False otherwise
    """
    try:
        issues_found = []
        fixes_applied = []

        # Check if account is active
        if not admin.is_active:
            issues_found.append("Account is inactive")
            admin.is_active = True
            fixes_applied.append("Activated account")

        # Test if the default password works
        if not admin.check_password("TempPass123!"):
            issues_found.append("Default password doesn't work")
            # Reset to default password
            password_hash, salt = admin.hash_password("TempPass123!")
            admin.password_hash = password_hash
            admin.salt = salt
            admin.force_password_change = True
            fixes_applied.append("Reset password to default")

        # Ensure password change is forced for security
        if not admin.force_password_change:
            admin.force_password_change = True
            fixes_applied.append("Enabled forced password change")

        # Apply fixes if any were needed
        if fixes_applied:
            db.commit()
            logger.warning(f"🔧 Fixed admin account issues: {', '.join(fixes_applied)}")
            logger.warning("🔑 Admin credentials: admin / TempPass123!")
            logger.warning("⚠️  SECURITY NOTICE: Password must be changed on first login!")
        else:
            logger.info("✅ Default admin account is properly configured")

        # Final verification
        return _test_admin_login(admin, "TempPass123!")

    except Exception as e:
        logger.error(f"Failed to validate/fix admin account: {e}")
        db.rollback()
        return False

def _test_admin_login(admin, password):
    """
    Test admin login functionality to ensure it works.

    Args:
        admin: Admin account object
        password: Password to test

    Returns:
        bool: True if login test successful, False otherwise
    """
    try:
        # Test password verification
        if admin.check_password(password):
            logger.info("✅ Admin login test successful")
            return True
        else:
            logger.error("❌ Admin login test failed - password verification failed")
            return False

    except Exception as e:
        logger.error(f"❌ Admin login test failed with error: {e}")
        return False

def init_db():
    """
    Initialize database tables, create indexes, and ensure system integrity.
    This includes comprehensive admin account validation and automatic repair.
    """
    logger.info("🚀 Initializing ConsultEase database...")

    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")

    # Create performance indexes for frequently queried fields
    _create_performance_indexes()
    logger.info("✅ Performance indexes created/verified")

    # Ensure admin account integrity (critical for system access)
    logger.info("🔐 Performing admin account integrity check...")
    admin_ready = _ensure_admin_account_integrity()

    if not admin_ready:
        logger.error("❌ CRITICAL: Admin account setup failed!")
        logger.error("❌ System may not be accessible through admin interface!")
        # Don't fail completely - continue with other initialization
    else:
        logger.info("✅ Admin account is ready for use")

    # Check if we need to create default data
    db = get_db()
    try:
        # Import models here to avoid circular imports
        from .admin import Admin
        from .faculty import Faculty
        from .student import Student

        # Check if faculty table is empty
        faculty_count = db.query(Faculty).count()
        if faculty_count == 0:
            # Create sample faculty for nRF51822 beacon integration
            # Note: BLE IDs will be updated with actual beacon MAC addresses during configuration
            sample_faculty = [
                Faculty(
                    name="Dr. John Smith",
                    department="Computer Science",
                    email="john.smith@university.edu",
                    ble_id="00:00:00:00:00:01",  # Placeholder - will be updated with actual beacon MAC
                    status=False  # Will be updated by beacon detection
                ),
                Faculty(
                    name="Dr. Jane Doe",
                    department="Mathematics",
                    email="jane.doe@university.edu",
                    ble_id="00:00:00:00:00:02",  # Placeholder - will be updated with actual beacon MAC
                    status=False  # Will be updated by beacon detection
                ),
                Faculty(
                    name="Prof. Robert Chen",
                    department="Computer Science",
                    email="robert.chen@university.edu",
                    ble_id="00:00:00:00:00:03",  # Placeholder - will be updated with actual beacon MAC
                    status=False  # Will be updated by beacon detection
                ),
                Faculty(
                    name="Jeysibn",
                    department="Computer Science",
                    email="jeysibn@university.edu",
                    ble_id="00:00:00:00:00:04",  # Placeholder - will be updated with actual beacon MAC
                    status=False  # Will be updated by beacon detection
                ),
                Faculty(
                    name="Dr. Maria Santos",
                    department="Information Technology",
                    email="maria.santos@university.edu",
                    ble_id="00:00:00:00:00:05",  # Placeholder - will be updated with actual beacon MAC
                    status=False  # Will be updated by beacon detection
                )
            ]
            db.add_all(sample_faculty)
            logger.info("✅ Created sample faculty data")

        # Check if student table is empty
        student_count = db.query(Student).count()
        if student_count == 0:
            # Create some sample students
            sample_students = [
                Student(
                    name="Alice Johnson",
                    department="Computer Science",
                    rfid_uid="TESTCARD123"
                ),
                Student(
                    name="Bob Williams",
                    department="Mathematics",
                    rfid_uid="TESTCARD456"
                )
            ]
            db.add_all(sample_students)
            logger.info("✅ Created sample student data")

        db.commit()
        logger.info("✅ Database initialization completed successfully")

    except Exception as e:
        logger.error(f"❌ Error creating default data: {str(e)}")
        db.rollback()
    finally:
        db.close()
        close_db()  # Return the connection to the pool