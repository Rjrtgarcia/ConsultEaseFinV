from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
import bcrypt
import os
import logging
import re
import time
from .base import Base

# Set up logging
logger = logging.getLogger(__name__)

# Constants for password security
MIN_PASSWORD_LENGTH = 8
PASSWORD_LOCKOUT_THRESHOLD = 5  # Number of failed attempts before lockout
PASSWORD_LOCKOUT_DURATION = 15 * 60  # 15 minutes in seconds

# Store failed login attempts: {username: [(timestamp, ip_address), ...]}
failed_login_attempts = {}

class Admin(Base):
    """
    Admin model.
    Represents an administrator in the system.
    """
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Admin {self.username}>"

    @staticmethod
    def validate_password_strength(password):
        """
        Validate password strength.

        Args:
            password (str): Password to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        if not password or not isinstance(password, str):
            return False, "Password cannot be empty"

        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

        # Check for complexity requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password)

        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase letters, lowercase letters, and digits"

        if not has_special:
            return False, "Password must contain at least one special character"

        # Check for common patterns
        if re.search(r'123|abc|qwerty|password|admin', password.lower()):
            return False, "Password contains common patterns that are easy to guess"

        return True, "Password meets strength requirements"

    @staticmethod
    def hash_password(password, salt=None):
        """
        Hash a password using bcrypt with improved security.

        Args:
            password (str): The password to hash
            salt (str, optional): Not used with bcrypt, kept for backward compatibility

        Returns:
            tuple: (password_hash, salt) - salt is included in the hash with bcrypt
                   but we keep a separate salt field for backward compatibility

        Raises:
            ValueError: If password doesn't meet strength requirements
        """
        # Validate password strength
        is_valid, error_message = Admin.validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_message)

        try:
            # Generate a salt and hash the password
            password_bytes = password.encode('utf-8')
            salt_bytes = bcrypt.gensalt(rounds=12)  # Increased from default 10
            hashed = bcrypt.hashpw(password_bytes, salt_bytes)
            password_hash = hashed.decode('utf-8')
            salt = salt_bytes.decode('utf-8')

            return password_hash, salt
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}")
            raise ValueError(f"Error processing password: {str(e)}")

    def check_password(self, password):
        """
        Check if a password matches the stored hash using bcrypt.

        Args:
            password (str): The password to check

        Returns:
            bool: True if the password matches, False otherwise
        """
        try:
            # If the hash starts with $2b$, it's a bcrypt hash
            if self.password_hash.startswith('$2b$') or self.password_hash.startswith('$2a$'):
                password_bytes = password.encode('utf-8')
                hash_bytes = self.password_hash.encode('utf-8')
                return bcrypt.checkpw(password_bytes, hash_bytes)
            else:
                # Fallback for old-style hashes (SHA-256)
                import hashlib
                hash_obj = hashlib.sha256()
                hash_obj.update(self.salt.encode('utf-8'))
                hash_obj.update(password.encode('utf-8'))
                password_hash = hash_obj.hexdigest()
                return password_hash == self.password_hash
        except Exception as e:
            logger.error(f"Error checking password: {str(e)}")
            return False

    @classmethod
    def record_login_attempt(cls, username, ip_address, success):
        """
        Record a login attempt for the account lockout mechanism.

        Args:
            username (str): Username that was attempted
            ip_address (str): IP address of the client
            success (bool): Whether the login was successful

        Returns:
            tuple: (is_locked_out, lockout_remaining_seconds)
        """
        global failed_login_attempts

        # If login was successful, clear failed attempts
        if success:
            if username in failed_login_attempts:
                del failed_login_attempts[username]
            return False, 0

        # Record the failed attempt
        current_time = time.time()

        if username not in failed_login_attempts:
            failed_login_attempts[username] = []

        # Add the current failed attempt
        failed_login_attempts[username].append((current_time, ip_address))

        # Clean up old attempts (older than lockout duration)
        failed_login_attempts[username] = [
            attempt for attempt in failed_login_attempts[username]
            if current_time - attempt[0] < PASSWORD_LOCKOUT_DURATION
        ]

        # Check if account is locked out
        if len(failed_login_attempts[username]) >= PASSWORD_LOCKOUT_THRESHOLD:
            # Calculate remaining lockout time
            oldest_recent_attempt = failed_login_attempts[username][-PASSWORD_LOCKOUT_THRESHOLD]
            lockout_end_time = oldest_recent_attempt[0] + PASSWORD_LOCKOUT_DURATION
            remaining_seconds = max(0, lockout_end_time - current_time)

            if remaining_seconds > 0:
                logger.warning(f"Account '{username}' is locked out for {remaining_seconds:.0f} more seconds")
                return True, remaining_seconds

        return False, 0

    @classmethod
    def is_account_locked(cls, username):
        """
        Check if an account is currently locked out.

        Args:
            username (str): Username to check

        Returns:
            tuple: (is_locked_out, lockout_remaining_seconds)
        """
        if username not in failed_login_attempts:
            return False, 0

        # Check if there are enough recent failed attempts
        if len(failed_login_attempts[username]) < PASSWORD_LOCKOUT_THRESHOLD:
            return False, 0

        # Calculate remaining lockout time
        current_time = time.time()
        oldest_recent_attempt = failed_login_attempts[username][-PASSWORD_LOCKOUT_THRESHOLD]
        lockout_end_time = oldest_recent_attempt[0] + PASSWORD_LOCKOUT_DURATION
        remaining_seconds = max(0, lockout_end_time - current_time)

        if remaining_seconds > 0:
            return True, remaining_seconds

        return False, 0

    def to_dict(self):
        """
        Convert model instance to dictionary.
        """
        return {
            "id": self.id,
            "username": self.username,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }