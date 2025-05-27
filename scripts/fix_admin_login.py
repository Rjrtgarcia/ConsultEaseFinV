#!/usr/bin/env python3
"""
Fix Admin Login Script for ConsultEase

This script diagnoses and fixes admin login issues by:
1. Checking if the database is properly initialized
2. Verifying if the admin account exists
3. Creating or resetting the admin account if needed
4. Testing the login credentials

Run this script if you're having trouble logging in with admin credentials.
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if we can connect to the database."""
    try:
        from central_system.models.base import get_db, engine
        
        # Test database connection
        db = get_db()
        result = db.execute("SELECT 1 as test")
        test_value = result.fetchone()
        db.close()
        
        if test_value and test_value[0] == 1:
            logger.info("✅ Database connection successful")
            return True
        else:
            logger.error("❌ Database connection test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False

def check_admin_table():
    """Check if the admin table exists and has the correct structure."""
    try:
        from central_system.models.base import get_db
        from central_system.models.admin import Admin
        
        db = get_db()
        
        # Check if admin table exists
        admin_count = db.query(Admin).count()
        logger.info(f"✅ Admin table exists with {admin_count} records")
        
        # List all admin users
        admins = db.query(Admin).all()
        for admin in admins:
            logger.info(f"   Admin found: {admin.username} (active: {admin.is_active}, force_change: {admin.force_password_change})")
        
        db.close()
        return True, admin_count
        
    except Exception as e:
        logger.error(f"❌ Error checking admin table: {e}")
        return False, 0

def create_default_admin():
    """Create the default admin account."""
    try:
        from central_system.models.base import get_db
        from central_system.models.admin import Admin
        
        db = get_db()
        
        # Check if admin already exists
        existing_admin = db.query(Admin).filter(Admin.username == "admin").first()
        if existing_admin:
            logger.info("Admin user already exists, updating password...")
            
            # Update the existing admin with the correct password
            password_hash, salt = Admin.hash_password("TempPass123!")
            existing_admin.password_hash = password_hash
            existing_admin.salt = salt
            existing_admin.is_active = True
            existing_admin.force_password_change = True
            
            db.commit()
            logger.info("✅ Updated existing admin account")
        else:
            logger.info("Creating new admin account...")
            
            # Create new admin
            password_hash, salt = Admin.hash_password("TempPass123!")
            new_admin = Admin(
                username="admin",
                password_hash=password_hash,
                salt=salt,
                email="admin@consultease.com",
                is_active=True,
                force_password_change=True
            )
            
            db.add(new_admin)
            db.commit()
            logger.info("✅ Created new admin account")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating admin account: {e}")
        return False

def test_admin_login():
    """Test the admin login credentials."""
    try:
        from central_system.controllers.admin_controller import AdminController
        
        admin_controller = AdminController()
        
        # Test login
        result = admin_controller.authenticate("admin", "TempPass123!")
        
        if result:
            logger.info("✅ Admin login test successful!")
            logger.info(f"   Username: admin")
            logger.info(f"   Password: TempPass123!")
            logger.info(f"   Requires password change: {result.get('requires_password_change', False)}")
            return True
        else:
            logger.error("❌ Admin login test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing admin login: {e}")
        return False

def initialize_database():
    """Initialize the database and create tables."""
    try:
        from central_system.models.base import init_db
        
        logger.info("Initializing database...")
        init_db()
        logger.info("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False

def main():
    """Main function to diagnose and fix admin login issues."""
    logger.info("🔧 ConsultEase Admin Login Fix Tool")
    logger.info("=" * 50)
    
    # Step 1: Check database connection
    logger.info("Step 1: Checking database connection...")
    if not check_database_connection():
        logger.error("Cannot proceed without database connection. Please check your database configuration.")
        return False
    
    # Step 2: Initialize database
    logger.info("\nStep 2: Initializing database...")
    if not initialize_database():
        logger.error("Failed to initialize database.")
        return False
    
    # Step 3: Check admin table
    logger.info("\nStep 3: Checking admin table...")
    table_exists, admin_count = check_admin_table()
    if not table_exists:
        logger.error("Admin table does not exist or is not accessible.")
        return False
    
    # Step 4: Create or fix admin account
    logger.info("\nStep 4: Creating/fixing admin account...")
    if not create_default_admin():
        logger.error("Failed to create or fix admin account.")
        return False
    
    # Step 5: Test login
    logger.info("\nStep 5: Testing admin login...")
    if not test_admin_login():
        logger.error("Admin login test failed.")
        return False
    
    # Success!
    logger.info("\n" + "=" * 50)
    logger.info("🎉 ADMIN LOGIN FIX COMPLETED SUCCESSFULLY!")
    logger.info("=" * 50)
    logger.info("")
    logger.info("✅ Default admin account is ready:")
    logger.info("   Username: admin")
    logger.info("   Password: TempPass123!")
    logger.info("")
    logger.info("⚠️  IMPORTANT SECURITY NOTICE:")
    logger.info("   - This is a TEMPORARY password")
    logger.info("   - You MUST change it on first login")
    logger.info("   - The system will force a password change")
    logger.info("")
    logger.info("🚀 You can now log in to the ConsultEase system!")
    
    return True

def reset_admin_password():
    """Reset admin password to default (for emergency use)."""
    try:
        from central_system.models.base import get_db
        from central_system.models.admin import Admin
        
        db = get_db()
        admin = db.query(Admin).filter(Admin.username == "admin").first()
        
        if admin:
            # Reset to default password
            password_hash, salt = Admin.hash_password("TempPass123!")
            admin.password_hash = password_hash
            admin.salt = salt
            admin.force_password_change = True
            admin.is_active = True
            
            db.commit()
            db.close()
            
            logger.info("✅ Admin password reset to default: TempPass123!")
            return True
        else:
            logger.error("❌ Admin user not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error resetting admin password: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix ConsultEase admin login issues")
    parser.add_argument("--reset-password", action="store_true", 
                       help="Reset admin password to default (emergency use)")
    
    args = parser.parse_args()
    
    if args.reset_password:
        logger.info("🔄 Resetting admin password to default...")
        if reset_admin_password():
            logger.info("✅ Password reset successful. Use admin/TempPass123! to login.")
        else:
            logger.error("❌ Password reset failed.")
    else:
        success = main()
        sys.exit(0 if success else 1)
