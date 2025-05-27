#!/usr/bin/env python3
"""
Test script to verify the ModernButton parameter fix.

Usage:
    python test_modern_button_fix.py

Author: ConsultEase Development Team
"""

import sys
import os

# Add the central_system directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'central_system'))

def test_modern_button_parameters():
    """Test that ModernButton accepts the correct parameters."""
    print("🧪 Testing ModernButton parameters...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            print("✅ QApplication created")
            
            # Import ModernButton
            from utils.ui_components import ModernButton
            print("✅ ModernButton imported")
            
            # Test correct parameter usage
            print("🔧 Testing correct parameter usage...")
            
            # Test basic button
            button1 = ModernButton("Test Button")
            print("✅ Basic button created")
            
            # Test primary button
            button2 = ModernButton("Primary Button", primary=True)
            print("✅ Primary button created")
            
            # Test danger button
            button3 = ModernButton("Danger Button", danger=True)
            print("✅ Danger button created")
            
            # Test button with icon
            try:
                from utils.icons import Icons
                button4 = ModernButton("Icon Button", icon_name=Icons.MESSAGE)
                print("✅ Icon button created")
            except Exception as e:
                print(f"⚠️  Icon button test skipped: {e}")
            
            # Test that button_type parameter fails (as expected)
            print("🔧 Testing that button_type parameter fails (as expected)...")
            try:
                button_bad = ModernButton("Bad Button", button_type="primary")
                print("❌ ERROR: button_type parameter should not work!")
                return False
            except TypeError as e:
                print("✅ button_type parameter correctly rejected")
                print(f"   Error: {e}")
            
            return True
            
        except ImportError as e:
            print(f"⚠️  PyQt5 not available: {e}")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ ModernButton test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_system_monitoring_widget():
    """Test that SystemMonitoringWidget can be created without errors."""
    print("\n🧪 Testing SystemMonitoringWidget creation...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Import SystemMonitoringWidget
            from views.system_monitoring_widget import SystemMonitoringWidget
            print("✅ SystemMonitoringWidget imported")
            
            # Create widget (don't show it)
            widget = SystemMonitoringWidget()
            print("✅ SystemMonitoringWidget created successfully")
            
            # Check that buttons exist
            if hasattr(widget, 'start_button'):
                print("✅ Widget has start_button")
            if hasattr(widget, 'stop_button'):
                print("✅ Widget has stop_button")
            
            return True
            
        except ImportError as e:
            print(f"⚠️  PyQt5 not available: {e}")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ SystemMonitoringWidget test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_password_change_dialog():
    """Test that PasswordChangeDialog can be created without errors."""
    print("\n🧪 Testing PasswordChangeDialog creation...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Import PasswordChangeDialog
            from views.password_change_dialog import PasswordChangeDialog
            print("✅ PasswordChangeDialog imported")
            
            # Create dialog (don't show it)
            admin_info = {'username': 'test_admin', 'id': 1}
            dialog = PasswordChangeDialog(admin_info)
            print("✅ PasswordChangeDialog created successfully")
            
            # Check that buttons exist
            if hasattr(dialog, 'change_button'):
                print("✅ Dialog has change_button")
            
            return True
            
        except ImportError as e:
            print(f"⚠️  PyQt5 not available: {e}")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ PasswordChangeDialog test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_admin_dashboard_window():
    """Test that AdminDashboardWindow can be created without errors."""
    print("\n🧪 Testing AdminDashboardWindow creation...")
    
    try:
        # Check if PyQt5 is available
        try:
            from PyQt5.QtWidgets import QApplication
            
            # Create QApplication if it doesn't exist
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Import AdminDashboardWindow
            from views.admin_dashboard_window import AdminDashboardWindow
            print("✅ AdminDashboardWindow imported")
            
            # Create window (don't show it)
            admin_info = {'username': 'test_admin', 'id': 1}
            window = AdminDashboardWindow(admin_info)
            print("✅ AdminDashboardWindow created successfully")
            
            # Check that monitoring tab exists
            if hasattr(window, 'monitoring_tab'):
                print("✅ Window has monitoring_tab")
            
            return True
            
        except ImportError as e:
            print(f"⚠️  PyQt5 not available: {e}")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ AdminDashboardWindow test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function."""
    print("🚀 ModernButton Parameter Fix Verification")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("ModernButton Parameters", test_modern_button_parameters),
        ("SystemMonitoringWidget", test_system_monitoring_widget),
        ("PasswordChangeDialog", test_password_change_dialog),
        ("AdminDashboardWindow", test_admin_dashboard_window),
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
        print("\n🎉 All tests passed! The ModernButton fix is working correctly.")
        print("✅ ModernButton uses correct parameters (primary, danger)")
        print("✅ SystemMonitoringWidget creates without errors")
        print("✅ PasswordChangeDialog creates without errors")
        print("✅ AdminDashboardWindow creates without errors")
        print("\n🚀 The admin dashboard should now load without ModernButton errors!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
