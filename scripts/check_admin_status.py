#!/usr/bin/env python3
"""
Check Admin Status Script for ConsultEase

This script checks the current status of admin accounts in the database
and provides detailed information about login credentials.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def check_admin_status():
    """Check the current admin status in the database."""
    try:
        from central_system.models.base import get_db
        from central_system.models.admin import Admin
        
        print("🔍 Checking ConsultEase Admin Status")
        print("=" * 40)
        
        db = get_db()
        
        # Get all admin users
        admins = db.query(Admin).all()
        
        if not admins:
            print("❌ No admin users found in database!")
            print("\nTo fix this, run:")
            print("   python3 scripts/fix_admin_login.py")
            return False
        
        print(f"✅ Found {len(admins)} admin user(s):")
        print()
        
        for i, admin in enumerate(admins, 1):
            print(f"Admin {i}:")
            print(f"   Username: {admin.username}")
            print(f"   Active: {'Yes' if admin.is_active else 'No'}")
            print(f"   Force Password Change: {'Yes' if admin.force_password_change else 'No'}")
            print(f"   Last Password Change: {admin.last_password_change}")
            print(f"   Created: {admin.created_at}")
            
            # Test if this is the default admin
            if admin.username == "admin":
                print(f"   🔑 This appears to be the default admin account")
                
                # Test the default password
                if admin.check_password("TempPass123!"):
                    print(f"   ✅ Default password (TempPass123!) works")
                else:
                    print(f"   ❌ Default password (TempPass123!) does NOT work")
                    
                    # Try alternative passwords
                    alt_passwords = ["Admin123!", "admin123", "password", "admin"]
                    for alt_pass in alt_passwords:
                        if admin.check_password(alt_pass):
                            print(f"   ✅ Alternative password ({alt_pass}) works")
                            break
                    else:
                        print(f"   ❌ None of the common passwords work")
            
            print()
        
        db.close()
        
        # Provide login instructions
        print("🚀 LOGIN INSTRUCTIONS:")
        print("=" * 40)
        
        default_admin = next((admin for admin in admins if admin.username == "admin"), None)
        if default_admin and default_admin.is_active:
            if default_admin.check_password("TempPass123!"):
                print("✅ Use these credentials to log in:")
                print("   Username: admin")
                print("   Password: TempPass123!")
                print()
                print("⚠️  IMPORTANT:")
                print("   - This is a temporary password")
                print("   - You will be forced to change it on first login")
                print("   - Choose a strong password with uppercase, lowercase, numbers, and symbols")
            else:
                print("❌ Default password doesn't work. Run the fix script:")
                print("   python3 scripts/fix_admin_login.py")
        else:
            print("❌ No active default admin found. Run the fix script:")
            print("   python3 scripts/fix_admin_login.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking admin status: {e}")
        print("\nThis might indicate a database connection issue.")
        print("Make sure the ConsultEase system is properly installed.")
        return False

def test_login_credentials():
    """Test login with various credential combinations."""
    try:
        from central_system.controllers.admin_controller import AdminController
        
        print("\n🧪 Testing Login Credentials")
        print("=" * 40)
        
        admin_controller = AdminController()
        
        # Test combinations
        test_credentials = [
            ("admin", "TempPass123!"),
            ("admin", "Admin123!"),
            ("admin", "admin123"),
            ("admin", "password"),
            ("admin", "admin")
        ]
        
        for username, password in test_credentials:
            try:
                result = admin_controller.authenticate(username, password)
                if result:
                    print(f"✅ SUCCESS: {username} / {password}")
                    print(f"   Requires password change: {result.get('requires_password_change', False)}")
                    return username, password
                else:
                    print(f"❌ FAILED: {username} / {password}")
            except Exception as e:
                print(f"❌ ERROR: {username} / {password} - {e}")
        
        print("\n❌ No working credentials found!")
        return None, None
        
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return None, None

if __name__ == "__main__":
    print("ConsultEase Admin Status Checker")
    print("================================")
    print()
    
    # Check admin status
    if check_admin_status():
        # Test login credentials
        username, password = test_login_credentials()
        
        if username and password:
            print(f"\n🎉 WORKING CREDENTIALS FOUND!")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
        else:
            print(f"\n🔧 No working credentials found. Run the fix script:")
            print(f"   python3 scripts/fix_admin_login.py")
    else:
        print(f"\n🔧 Database issues detected. Run the fix script:")
        print(f"   python3 scripts/fix_admin_login.py")
