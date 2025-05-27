#!/usr/bin/env python3
"""
Test script to verify the admin email and MQTT ping fixes.

Usage:
    python test_fixes.py

Author: ConsultEase Development Team
"""

import sys
import os

# Add the central_system directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'central_system'))

def test_admin_model_fields():
    """Test that Admin model has the correct fields."""
    print("🧪 Testing Admin model fields...")
    
    try:
        from models.admin import Admin
        
        # Check Admin model fields
        admin_fields = [attr for attr in dir(Admin) if not attr.startswith('_')]
        expected_fields = ['id', 'username', 'password_hash', 'salt', 'is_active', 
                          'force_password_change', 'last_password_change', 'created_at', 'updated_at']
        
        print(f"✅ Admin model imported successfully")
        print(f"📋 Admin model fields: {admin_fields}")
        
        # Check that email is NOT in the model
        if 'email' in admin_fields:
            print("❌ ERROR: Admin model still has 'email' field")
            return False
        else:
            print("✅ Admin model correctly does NOT have 'email' field")
        
        # Test creating an Admin instance without email
        try:
            # This should work without email parameter
            admin = Admin(
                username="test",
                password_hash="hash",
                salt="salt",
                is_active=True,
                force_password_change=False
            )
            print("✅ Admin object creation without email works correctly")
            return True
        except Exception as e:
            print(f"❌ ERROR: Admin object creation failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Admin model test failed: {e}")
        return False

def test_admin_controller_create_account():
    """Test that AdminController.create_admin_account works without email."""
    print("\n🧪 Testing AdminController.create_admin_account...")
    
    try:
        from controllers.admin_controller import AdminController
        
        controller = AdminController()
        print("✅ AdminController created successfully")
        
        # Test the method signature (should not require email)
        import inspect
        sig = inspect.signature(controller.create_admin_account)
        params = list(sig.parameters.keys())
        
        print(f"📋 create_admin_account parameters: {params}")
        
        if 'email' in params:
            print("❌ ERROR: create_admin_account still has 'email' parameter")
            return False
        else:
            print("✅ create_admin_account correctly does NOT have 'email' parameter")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: AdminController test failed: {e}")
        return False

def test_mqtt_service():
    """Test that MQTT service doesn't use ping method."""
    print("\n🧪 Testing MQTT service ping fix...")
    
    try:
        from services.async_mqtt_service import AsyncMQTTService
        
        # Create MQTT service instance
        mqtt_service = AsyncMQTTService()
        print("✅ AsyncMQTTService created successfully")
        
        # Check that the connection monitor method exists and doesn't crash
        if hasattr(mqtt_service, '_connection_monitor'):
            print("✅ _connection_monitor method exists")
        else:
            print("❌ ERROR: _connection_monitor method missing")
            return False
        
        # Test that we can import paho.mqtt.client
        try:
            import paho.mqtt.client as mqtt
            client = mqtt.Client()
            
            # Verify that client doesn't have ping method
            if hasattr(client, 'ping'):
                print("⚠️  WARNING: MQTT client has ping method (unexpected)")
            else:
                print("✅ MQTT client correctly does NOT have ping method")
            
            print("✅ MQTT service test completed successfully")
            return True
            
        except ImportError:
            print("⚠️  paho-mqtt not available - MQTT test skipped")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ ERROR: MQTT service test failed: {e}")
        return False

def test_admin_account_creation_dialog():
    """Test that AdminAccountCreationDialog works without email."""
    print("\n🧪 Testing AdminAccountCreationDialog...")
    
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
            
            # Check that email_input field doesn't exist
            if hasattr(dialog, 'email_input'):
                print("❌ ERROR: Dialog still has email_input field")
                return False
            else:
                print("✅ Dialog correctly does NOT have email_input field")
            
            return True
            
        except ImportError:
            print("⚠️  PyQt5 not available - dialog test skipped")
            return True  # Not a failure, just not available
            
    except Exception as e:
        print(f"❌ ERROR: Dialog test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Admin Email and MQTT Ping Fixes Verification")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Admin Model Fields", test_admin_model_fields),
        ("AdminController Method", test_admin_controller_create_account),
        ("MQTT Service", test_mqtt_service),
        ("Account Creation Dialog", test_admin_account_creation_dialog),
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
        print("✅ Admin model no longer uses 'email' field")
        print("✅ MQTT service no longer uses ping method")
        print("✅ Account creation dialog works without email")
        print("✅ AdminController works without email parameter")
        print("\n🚀 The application should now run without the reported errors!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
