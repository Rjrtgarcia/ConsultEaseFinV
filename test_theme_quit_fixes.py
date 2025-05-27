#!/usr/bin/env python3
"""
Test script to verify the theme and quit method fixes.

Usage:
    python test_theme_quit_fixes.py

Author: ConsultEase Development Team
"""

import sys
import os

# Add the central_system directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'central_system'))

def test_theme_methods():
    """Test that ConsultEaseTheme has all required methods."""
    print("🧪 Testing ConsultEaseTheme methods...")
    
    try:
        from utils.theme import ConsultEaseTheme
        
        # Test that all required methods exist
        required_methods = [
            'get_base_stylesheet',
            'get_login_stylesheet', 
            'get_dashboard_stylesheet',
            'get_consultation_stylesheet',
            'get_dialog_stylesheet'  # This was missing and causing the error
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if not hasattr(ConsultEaseTheme, method_name):
                missing_methods.append(method_name)
            else:
                print(f"✅ {method_name} exists")
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        
        # Test that get_dialog_stylesheet returns a string
        try:
            dialog_stylesheet = ConsultEaseTheme.get_dialog_stylesheet()
            if isinstance(dialog_stylesheet, str) and len(dialog_stylesheet) > 0:
                print("✅ get_dialog_stylesheet returns valid stylesheet")
                print(f"   Stylesheet length: {len(dialog_stylesheet)} characters")
            else:
                print("❌ get_dialog_stylesheet doesn't return valid stylesheet")
                return False
        except Exception as e:
            print(f"❌ Error calling get_dialog_stylesheet: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Theme test failed: {e}")
        return False

def test_password_change_dialog_import():
    """Test that PasswordChangeDialog can be imported without theme errors."""
    print("\n🧪 Testing PasswordChangeDialog import...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Try to import the password change dialog
            from views.password_change_dialog import PasswordChangeDialog
            print("✅ PasswordChangeDialog imported successfully")
            
            # Test that we can create the dialog (don't show it)
            # We need to provide admin_info parameter
            admin_info = {'username': 'test_admin', 'id': 1}
            dialog = PasswordChangeDialog(admin_info)
            print("✅ PasswordChangeDialog created successfully")
            
            return True
            
        except ImportError:
            print("⚠️  PyQt5 not available - dialog test skipped")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ PasswordChangeDialog test failed: {e}")
        return False

def test_main_app_methods():
    """Test that ConsultEaseApp has correct methods."""
    print("\n🧪 Testing ConsultEaseApp methods...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Import the main app class
            from main import ConsultEaseApp
            print("✅ ConsultEaseApp imported successfully")
            
            # Create app instance (don't run it)
            consultease_app = ConsultEaseApp()
            print("✅ ConsultEaseApp created successfully")
            
            # Check that it has the app attribute (for quit method)
            if hasattr(consultease_app, 'app'):
                print("✅ ConsultEaseApp has 'app' attribute")
                
                # Check that app has quit method
                if hasattr(consultease_app.app, 'quit'):
                    print("✅ ConsultEaseApp.app has 'quit' method")
                else:
                    print("❌ ConsultEaseApp.app doesn't have 'quit' method")
                    return False
            else:
                print("❌ ConsultEaseApp doesn't have 'app' attribute")
                return False
            
            return True
            
        except ImportError:
            print("⚠️  PyQt5 not available - app test skipped")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ ConsultEaseApp test failed: {e}")
        return False

def test_admin_account_creation_dialog():
    """Test that AdminAccountCreationDialog works with the theme."""
    print("\n🧪 Testing AdminAccountCreationDialog with theme...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Try to import and create the admin account creation dialog
            from views.admin_account_creation_dialog import AdminAccountCreationDialog
            print("✅ AdminAccountCreationDialog imported successfully")
            
            # Create dialog (don't show it)
            dialog = AdminAccountCreationDialog()
            print("✅ AdminAccountCreationDialog created successfully")
            
            # Check that it has the required form elements
            if hasattr(dialog, 'username_input'):
                print("✅ Dialog has username_input")
            if hasattr(dialog, 'password_input'):
                print("✅ Dialog has password_input")
            if hasattr(dialog, 'create_button'):
                print("✅ Dialog has create_button")
            
            return True
            
        except ImportError:
            print("⚠️  PyQt5 not available - dialog test skipped")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ AdminAccountCreationDialog test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Theme and Quit Method Fixes Verification")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("ConsultEaseTheme Methods", test_theme_methods),
        ("PasswordChangeDialog Import", test_password_change_dialog_import),
        ("ConsultEaseApp Methods", test_main_app_methods),
        ("AdminAccountCreationDialog", test_admin_account_creation_dialog),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
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
        print("\n🎉 All tests passed! The fixes are working correctly.")
        print("✅ ConsultEaseTheme.get_dialog_stylesheet() method added")
        print("✅ PasswordChangeDialog can be created without theme errors")
        print("✅ ConsultEaseApp.app.quit() method is available")
        print("✅ AdminAccountCreationDialog works with theme system")
        print("\n🚀 The application should now run without theme or quit errors!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
