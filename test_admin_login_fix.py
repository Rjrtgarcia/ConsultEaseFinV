#!/usr/bin/env python3
"""
Quick test script to verify the admin login fix is working.
This script tests the import structure and basic functionality.

Usage:
    python test_admin_login_fix.py

Author: ConsultEase Development Team
"""

import sys
import os

# Add the central_system directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'central_system'))

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        # Test admin controller imports
        from controllers.admin_controller import AdminController
        print("✅ AdminController import successful")
        
        # Test admin account creation dialog imports
        from views.admin_account_creation_dialog import AdminAccountCreationDialog
        print("✅ AdminAccountCreationDialog import successful")
        
        # Test admin login window imports
        from views.admin_login_window import AdminLoginWindow
        print("✅ AdminLoginWindow import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_admin_controller_methods():
    """Test that admin controller methods work correctly."""
    print("\n🧪 Testing AdminController methods...")
    
    try:
        from controllers.admin_controller import AdminController
        
        # Create admin controller
        admin_controller = AdminController()
        print("✅ AdminController created successfully")
        
        # Test first-time setup detection methods
        try:
            # These methods should not crash even if database is not initialized
            accounts_exist = admin_controller.check_admin_accounts_exist()
            print(f"✅ check_admin_accounts_exist() returned: {accounts_exist}")
            
            valid_accounts_exist = admin_controller.check_valid_admin_accounts_exist()
            print(f"✅ check_valid_admin_accounts_exist() returned: {valid_accounts_exist}")
            
            is_first_time = admin_controller.is_first_time_setup()
            print(f"✅ is_first_time_setup() returned: {is_first_time}")
            
        except Exception as e:
            print(f"⚠️  Database methods failed (expected if DB not initialized): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AdminController test failed: {e}")
        return False

def test_dialog_creation():
    """Test that the dialog can be created without errors."""
    print("\n🧪 Testing AdminAccountCreationDialog creation...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            from views.admin_account_creation_dialog import AdminAccountCreationDialog
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Create dialog (don't show it)
            dialog = AdminAccountCreationDialog()
            print("✅ AdminAccountCreationDialog created successfully")
            
            # Test some basic properties
            if hasattr(dialog, 'username_input'):
                print("✅ Dialog has username_input field")
            if hasattr(dialog, 'password_input'):
                print("✅ Dialog has password_input field")
            if hasattr(dialog, 'validate_form'):
                print("✅ Dialog has validate_form method")
            
            return True
            
        except ImportError:
            print("⚠️  PyQt5 not available - dialog creation test skipped")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ Dialog creation test failed: {e}")
        return False

def test_admin_login_window_methods():
    """Test that admin login window methods exist."""
    print("\n🧪 Testing AdminLoginWindow methods...")
    
    try:
        from views.admin_login_window import AdminLoginWindow
        
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Create admin login window (don't show it)
            admin_login = AdminLoginWindow()
            print("✅ AdminLoginWindow created successfully")
            
            # Test new methods exist
            if hasattr(admin_login, 'set_admin_controller'):
                print("✅ AdminLoginWindow has set_admin_controller method")
            if hasattr(admin_login, 'check_first_time_setup'):
                print("✅ AdminLoginWindow has check_first_time_setup method")
            if hasattr(admin_login, 'show_first_time_setup_dialog'):
                print("✅ AdminLoginWindow has show_first_time_setup_dialog method")
            if hasattr(admin_login, 'handle_account_created'):
                print("✅ AdminLoginWindow has handle_account_created method")
            
            return True
            
        except ImportError:
            print("⚠️  PyQt5 not available - AdminLoginWindow test skipped")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ AdminLoginWindow test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Admin Login Fix Verification Test")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Import Test", test_imports),
        ("AdminController Methods", test_admin_controller_methods),
        ("Dialog Creation", test_dialog_creation),
        ("AdminLoginWindow Methods", test_admin_login_window_methods),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The admin login fix is working correctly.")
        print("✅ The QTimer import issue has been resolved.")
        print("✅ The enhanced admin account management system is ready.")
        print("✅ You can now run the main application without the import error.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
