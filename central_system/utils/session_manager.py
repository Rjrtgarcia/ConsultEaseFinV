"""
Session management utilities for ConsultEase system.
Provides secure session handling with timeout, lockout, and security features.
"""

import time
import secrets
import hashlib
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Secure session manager with timeout, lockout, and security features.
    """
    
    def __init__(self, timeout_minutes: int = 30, lockout_threshold: int = 5, lockout_duration: int = 900):
        """
        Initialize the session manager.
        
        Args:
            timeout_minutes: Session timeout in minutes
            lockout_threshold: Number of failed attempts before lockout
            lockout_duration: Lockout duration in seconds
        """
        self.timeout_seconds = timeout_minutes * 60
        self.lockout_threshold = lockout_threshold
        self.lockout_duration = lockout_duration
        
        # Session storage
        self.sessions: Dict[str, dict] = {}
        
        # Failed login attempts tracking
        self.failed_attempts: Dict[str, dict] = {}
        
        # Security settings
        self.secure_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
        }
        
        logger.info(f"Session manager initialized with {timeout_minutes}min timeout, {lockout_threshold} attempt threshold")
    
    def create_session(self, user_id: str, user_type: str = 'student', additional_data: dict = None) -> str:
        """
        Create a new secure session.
        
        Args:
            user_id: User identifier
            user_type: Type of user (student, admin)
            additional_data: Additional session data
            
        Returns:
            str: Session ID
        """
        # Generate cryptographically secure session ID
        session_id = secrets.token_urlsafe(32)
        
        # Create session data
        session_data = {
            'user_id': user_id,
            'user_type': user_type,
            'created': time.time(),
            'last_activity': time.time(),
            'ip_address': None,  # To be set by web interface
            'user_agent': None,  # To be set by web interface
            'csrf_token': secrets.token_urlsafe(32)
        }
        
        if additional_data:
            session_data.update(additional_data)
        
        self.sessions[session_id] = session_data
        
        logger.info(f"Created session for {user_type} {user_id}: {session_id[:8]}...")
        return session_id
    
    def validate_session(self, session_id: str, update_activity: bool = True) -> Tuple[bool, Optional[dict]]:
        """
        Validate a session and optionally update last activity.
        
        Args:
            session_id: Session ID to validate
            update_activity: Whether to update last activity timestamp
            
        Returns:
            Tuple of (is_valid, session_data)
        """
        if not session_id or session_id not in self.sessions:
            return False, None
        
        session = self.sessions[session_id]
        current_time = time.time()
        
        # Check if session has expired
        if current_time - session['last_activity'] > self.timeout_seconds:
            logger.info(f"Session expired: {session_id[:8]}...")
            self.invalidate_session(session_id)
            return False, None
        
        # Update last activity if requested
        if update_activity:
            session['last_activity'] = current_time
        
        return True, session
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session.
        
        Args:
            session_id: Session ID to invalidate
            
        Returns:
            bool: True if session was found and invalidated
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            logger.info(f"Invalidated session for {session.get('user_type', 'unknown')} {session.get('user_id', 'unknown')}")
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_activity'] > self.timeout_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def record_failed_attempt(self, identifier: str, ip_address: str = None) -> bool:
        """
        Record a failed login attempt.
        
        Args:
            identifier: User identifier (username, email, etc.)
            ip_address: IP address of the attempt
            
        Returns:
            bool: True if user is now locked out
        """
        current_time = time.time()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time,
                'locked_until': None,
                'ip_addresses': set()
            }
        
        attempt_data = self.failed_attempts[identifier]
        
        # Check if user is currently locked out
        if attempt_data['locked_until'] and current_time < attempt_data['locked_until']:
            return True
        
        # Reset count if lockout period has passed
        if attempt_data['locked_until'] and current_time >= attempt_data['locked_until']:
            attempt_data['count'] = 0
            attempt_data['locked_until'] = None
        
        # Record the attempt
        attempt_data['count'] += 1
        attempt_data['last_attempt'] = current_time
        if ip_address:
            attempt_data['ip_addresses'].add(ip_address)
        
        # Check if lockout threshold is reached
        if attempt_data['count'] >= self.lockout_threshold:
            attempt_data['locked_until'] = current_time + self.lockout_duration
            logger.warning(f"User {identifier} locked out after {attempt_data['count']} failed attempts")
            return True
        
        logger.warning(f"Failed login attempt for {identifier} ({attempt_data['count']}/{self.lockout_threshold})")
        return False
    
    def is_locked_out(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """
        Check if a user is locked out.
        
        Args:
            identifier: User identifier
            
        Returns:
            Tuple of (is_locked_out, time_remaining_seconds)
        """
        if identifier not in self.failed_attempts:
            return False, None
        
        attempt_data = self.failed_attempts[identifier]
        current_time = time.time()
        
        if attempt_data['locked_until'] and current_time < attempt_data['locked_until']:
            time_remaining = attempt_data['locked_until'] - current_time
            return True, time_remaining
        
        return False, None
    
    def clear_failed_attempts(self, identifier: str) -> bool:
        """
        Clear failed attempts for a user (called on successful login).
        
        Args:
            identifier: User identifier
            
        Returns:
            bool: True if attempts were cleared
        """
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
            logger.info(f"Cleared failed attempts for {identifier}")
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session information without updating activity.
        
        Args:
            session_id: Session ID
            
        Returns:
            dict: Session information or None
        """
        is_valid, session_data = self.validate_session(session_id, update_activity=False)
        return session_data if is_valid else None
    
    def get_security_headers(self) -> dict:
        """
        Get security headers to be added to HTTP responses.
        
        Returns:
            dict: Security headers
        """
        return self.secure_headers.copy()
    
    def get_active_sessions_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            int: Number of active sessions
        """
        # Clean up expired sessions first
        self.cleanup_expired_sessions()
        return len(self.sessions)
    
    def get_session_stats(self) -> dict:
        """
        Get session statistics.
        
        Returns:
            dict: Session statistics
        """
        self.cleanup_expired_sessions()
        
        stats = {
            'active_sessions': len(self.sessions),
            'failed_attempts_tracked': len(self.failed_attempts),
            'locked_out_users': 0,
            'session_timeout_minutes': self.timeout_seconds // 60,
            'lockout_threshold': self.lockout_threshold,
            'lockout_duration_minutes': self.lockout_duration // 60
        }
        
        # Count locked out users
        current_time = time.time()
        for attempt_data in self.failed_attempts.values():
            if attempt_data['locked_until'] and current_time < attempt_data['locked_until']:
                stats['locked_out_users'] += 1
        
        return stats


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Returns:
        SessionManager: Global session manager
    """
    global _session_manager
    if _session_manager is None:
        # Load configuration from config
        from ..config import get_config
        config = get_config()
        
        security_config = config.get('security', {})
        timeout_minutes = security_config.get('session_timeout', 1800) // 60  # Convert seconds to minutes
        lockout_threshold = security_config.get('password_lockout_threshold', 5)
        lockout_duration = security_config.get('password_lockout_duration', 900)
        
        _session_manager = SessionManager(
            timeout_minutes=timeout_minutes,
            lockout_threshold=lockout_threshold,
            lockout_duration=lockout_duration
        )
    
    return _session_manager
