#!/usr/bin/env python3
"""
Test script to manually test the admin account creation dialog.

Usage:
    python test_admin_dialog.py

Author: ConsultEase Development Team
"""

import sys
import os

# Add the central_system directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'central_system'))

def test_admin_dialog():
    """Test the admin account creation dialog directly."""
    print("🧪 Testing AdminAccountCreationDialog...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            print("✅ QApplication created")
            
            # Import the dialog
            from views.admin_account_creation_dialog import AdminAccountCreationDialog
            print("✅ AdminAccountCreationDialog imported")
            
            # Create dialog
            dialog = AdminAccountCreationDialog()
            print("✅ AdminAccountCreationDialog created")
            
            # Connect signal for testing
            def on_account_created(admin_info):
                print(f"🎉 Account created: {admin_info}")
                dialog.accept()
            
            dialog.account_created.connect(on_account_created)
            print("✅ Signal connected")
            
            # Show dialog
            print("📱 Showing dialog...")
            print("   Please create an admin account in the dialog")
            print("   Or click Cancel to close")
            
            result = dialog.exec_()
            
            if result == dialog.Accepted:
                print("✅ Dialog completed successfully")
            else:
                print("❌ Dialog was cancelled")
            
            return True
            
        except ImportError as e:
            print(f"⚠️  PyQt5 not available: {e}")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ Dialog test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_database_state():
    """Test the current database state."""
    print("\n🔍 Testing database state...")
    
    try:
        from models.base import get_db
        from models.admin import Admin
        
        db = get_db()
        admin_count = db.query(Admin).count()
        
        print(f"📊 Admin accounts in database: {admin_count}")
        
        if admin_count == 0:
            print("✅ No admin accounts - first-time setup should work")
        else:
            print("⚠️  Admin accounts exist - first-time setup may not trigger")
            
            # Show existing accounts
            admins = db.query(Admin).all()
            for admin in admins:
                print(f"   - {admin.username} (Active: {admin.is_active})")
        
        db.close()
        return admin_count
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return -1

def test_admin_controller():
    """Test the admin controller."""
    print("\n🧪 Testing AdminController...")
    
    try:
        from controllers.admin_controller import AdminController
        
        controller = AdminController()
        print("✅ AdminController created")
        
        # Test methods
        accounts_exist = controller.check_admin_accounts_exist()
        print(f"📋 check_admin_accounts_exist(): {accounts_exist}")
        
        is_first_time = controller.is_first_time_setup()
        print(f"📋 is_first_time_setup(): {is_first_time}")
        
        return is_first_time
        
    except Exception as e:
        print(f"❌ AdminController test failed: {e}")
        return False

def clear_admin_accounts():
    """Clear admin accounts for testing."""
    print("\n🗑️  Clearing admin accounts...")
    
    try:
        from models.base import get_db
        from models.admin import Admin
        
        db = get_db()
        count_before = db.query(Admin).count()
        
        db.query(Admin).delete()
        db.commit()
        
        count_after = db.query(Admin).count()
        
        print(f"📊 Deleted {count_before - count_after} admin accounts")
        print(f"📊 Remaining admin accounts: {count_after}")
        
        db.close()
        return count_after == 0
        
    except Exception as e:
        print(f"❌ Failed to clear admin accounts: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Admin Account Creation Dialog Test")
    print("=" * 50)
    
    # Check database state
    admin_count = test_database_state()
    
    # Test admin controller
    is_first_time = test_admin_controller()
    
    # Analysis
    print("\n📊 ANALYSIS")
    print("=" * 20)
    
    if admin_count > 0:
        print(f"⚠️  {admin_count} admin account(s) exist")
        print("   This may prevent first-time setup from triggering")
        
        response = input("\n❓ Clear admin accounts to test first-time setup? (y/N): ")
        if response.lower() == 'y':
            if clear_admin_accounts():
                print("✅ Admin accounts cleared")
                # Re-test
                is_first_time = test_admin_controller()
            else:
                print("❌ Failed to clear admin accounts")
    
    if is_first_time:
        print("✅ First-time setup should work")
    else:
        print("❌ First-time setup will not trigger")
    
    # Test the dialog
    print("\n🧪 TESTING DIALOG")
    print("=" * 20)
    
    response = input("❓ Test the admin account creation dialog? (y/N): ")
    if response.lower() == 'y':
        success = test_admin_dialog()
        if success:
            print("✅ Dialog test completed")
        else:
            print("❌ Dialog test failed")
    
    print("\n🎯 RECOMMENDATIONS")
    print("=" * 20)
    
    if admin_count == 0 and is_first_time:
        print("✅ Everything looks good for first-time setup")
        print("   Try running: python central_system/main.py")
        print("   Then click 'Admin Login' - the dialog should appear")
    elif admin_count > 0:
        print("⚠️  Admin accounts exist - first-time setup won't trigger")
        print("   Options:")
        print("   1. Clear admin accounts and test first-time setup")
        print("   2. Use existing admin credentials to login")
        print("   3. Test the dialog manually (as done above)")
    else:
        print("❌ Something is wrong with the first-time setup detection")
        print("   Check the logs for errors")

if __name__ == "__main__":
    main()
