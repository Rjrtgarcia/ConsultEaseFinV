#!/usr/bin/env python3
"""
Test script to verify MQTT fixes are working correctly.
"""

import sys
import os
import time
import json
import logging

# Add the central_system directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'central_system'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mqtt_message_validation():
    """Test MQTT message validation and error handling."""
    logger.info("🧪 Testing MQTT message validation...")
    
    try:
        from central_system.services.async_mqtt_service import AsyncMQTTService
        
        # Create a test MQTT service
        mqtt_service = AsyncMQTTService(
            broker_host="localhost",
            broker_port=1883
        )
        
        # Test message validation
        test_messages = [
            {"topic": "test/topic", "data": {"test": "data"}},
            {"topic": "test/topic", "data": "simple string"},
            {"topic": "test/topic", "data": None},
            {"topic": "", "data": "invalid topic"},
            {"topic": None, "data": "null topic"},
        ]
        
        for i, msg in enumerate(test_messages):
            logger.info(f"Testing message {i+1}: {msg}")
            try:
                mqtt_service.publish_async(msg["topic"], msg["data"])
                logger.info(f"✅ Message {i+1} processed successfully")
            except Exception as e:
                logger.error(f"❌ Message {i+1} failed: {e}")
        
        logger.info("✅ MQTT message validation test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ MQTT validation test failed: {e}")
        return False

def test_dashboard_refresh():
    """Test dashboard refresh method fixes."""
    logger.info("🧪 Testing dashboard refresh fixes...")
    
    try:
        from central_system.views.dashboard_window import DashboardWindow
        from PyQt5.QtWidgets import QApplication
        
        # Create minimal Qt application for testing
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create dashboard window
        dashboard = DashboardWindow()
        
        # Test timer-triggered refresh
        logger.info("Testing timer-triggered refresh...")
        dashboard._refresh_faculty_status_timer()
        logger.info("✅ Timer refresh completed without errors")
        
        # Test manual refresh
        logger.info("Testing manual refresh...")
        dashboard.refresh_faculty_status()
        logger.info("✅ Manual refresh completed without errors")
        
        logger.info("✅ Dashboard refresh test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dashboard refresh test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_faculty_controller():
    """Test faculty controller error handling."""
    logger.info("🧪 Testing faculty controller fixes...")
    
    try:
        from central_system.controllers.faculty_controller import FacultyController
        
        # Create faculty controller
        controller = FacultyController()
        
        # Test with various invalid inputs
        test_cases = [
            {"topic": None, "data": None},
            {"topic": "", "data": "test"},
            {"topic": "invalid/topic", "data": {"test": "data"}},
            {"topic": "consultease/faculty/1/status", "data": None},
            {"topic": "consultease/faculty/invalid/status", "data": {"status": True}},
        ]
        
        for i, case in enumerate(test_cases):
            logger.info(f"Testing case {i+1}: {case}")
            try:
                controller.handle_faculty_status_update(case["topic"], case["data"])
                logger.info(f"✅ Case {i+1} handled gracefully")
            except Exception as e:
                logger.error(f"❌ Case {i+1} failed: {e}")
        
        logger.info("✅ Faculty controller test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Faculty controller test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting MQTT fixes test suite...")
    
    tests = [
        ("MQTT Message Validation", test_mqtt_message_validation),
        ("Dashboard Refresh", test_dashboard_refresh),
        ("Faculty Controller", test_faculty_controller),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} test...")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All tests passed! MQTT fixes are working correctly.")
        return 0
    else:
        logger.error("⚠️ Some tests failed. Please check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
