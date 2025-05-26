#!/usr/bin/env python3
"""
Test script for MAC address-based faculty detection.

This script helps test the MAC address detection functionality by:
1. Monitoring MQTT messages for MAC status updates
2. Verifying faculty status changes in the database
3. Providing debug information for troubleshooting

Usage:
    python test_mac_detection.py [--faculty-id FACULTY_ID] [--mqtt-host HOST]
"""

import argparse
import json
import logging
import time
import sys
import os

# Add the parent directory to the path so we can import from central_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import paho.mqtt.client as mqtt
    from central_system.models import get_db, Faculty
    from central_system.utils.mqtt_topics import MQTTTopics
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you have installed the required dependencies:")
    print("pip install paho-mqtt sqlalchemy")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MACDetectionTester:
    def __init__(self, mqtt_host="localhost", mqtt_port=1883, faculty_id=None):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.faculty_id = faculty_id
        self.mqtt_client = None
        self.db = None
        
    def setup_mqtt(self):
        """Set up MQTT client and connect to broker."""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        try:
            logger.info(f"Connecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def setup_database(self):
        """Set up database connection."""
        try:
            self.db = get_db()
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when MQTT client connects."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            
            # Subscribe to relevant topics
            topics = [
                "consultease/faculty/+/mac_status",
                "consultease/faculty/+/status", 
                "professor/status",
                "consultease/system/notifications"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback for when MQTT message is received."""
        topic = msg.topic
        try:
            # Try to decode as JSON first
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                is_json = True
            except json.JSONDecodeError:
                payload = msg.payload.decode('utf-8')
                is_json = False
            
            logger.info(f"Received message on topic '{topic}':")
            
            if is_json:
                logger.info(f"  JSON Payload: {json.dumps(payload, indent=2)}")
                
                # Handle MAC status updates
                if topic.endswith("/mac_status"):
                    self.handle_mac_status_update(topic, payload)
                elif payload.get('type') == 'faculty_mac_status':
                    self.handle_system_notification(payload)
            else:
                logger.info(f"  String Payload: {payload}")
                
                # Handle legacy status updates
                if topic.endswith("/status") or topic == "professor/status":
                    self.handle_legacy_status_update(topic, payload)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def handle_mac_status_update(self, topic, payload):
        """Handle MAC address status updates."""
        try:
            # Extract faculty ID from topic
            faculty_id = int(topic.split("/")[2])
            status = payload.get("status", "")
            mac = payload.get("mac", "")
            timestamp = payload.get("timestamp", 0)
            
            logger.info(f"MAC Status Update for Faculty {faculty_id}:")
            logger.info(f"  Status: {status}")
            logger.info(f"  MAC Address: {mac}")
            logger.info(f"  Timestamp: {timestamp}")
            
            # Check database status
            if self.db:
                faculty = self.db.query(Faculty).filter(Faculty.id == faculty_id).first()
                if faculty:
                    logger.info(f"  Database Status: {'Available' if faculty.status else 'Unavailable'}")
                    logger.info(f"  Database BLE ID: {faculty.ble_id}")
                else:
                    logger.warning(f"  Faculty {faculty_id} not found in database")
                    
        except Exception as e:
            logger.error(f"Error handling MAC status update: {e}")
    
    def handle_legacy_status_update(self, topic, payload):
        """Handle legacy status updates."""
        logger.info(f"Legacy Status Update:")
        logger.info(f"  Topic: {topic}")
        logger.info(f"  Status: {payload}")
        
        # Map legacy status to boolean
        if payload in ["keychain_connected", "faculty_present"]:
            status = "Available"
        elif payload in ["keychain_disconnected", "faculty_absent"]:
            status = "Unavailable"
        else:
            status = f"Unknown ({payload})"
            
        logger.info(f"  Interpreted as: {status}")
    
    def handle_system_notification(self, payload):
        """Handle system notifications."""
        logger.info(f"System Notification:")
        logger.info(f"  Type: {payload.get('type', 'unknown')}")
        logger.info(f"  Faculty ID: {payload.get('faculty_id', 'unknown')}")
        logger.info(f"  Faculty Name: {payload.get('faculty_name', 'unknown')}")
        logger.info(f"  Status: {payload.get('status', 'unknown')}")
        logger.info(f"  Detected MAC: {payload.get('detected_mac', 'none')}")
    
    def get_faculty_status(self, faculty_id=None):
        """Get current faculty status from database."""
        if not self.db:
            logger.error("Database not connected")
            return
            
        try:
            if faculty_id:
                faculty_list = self.db.query(Faculty).filter(Faculty.id == faculty_id).all()
            else:
                faculty_list = self.db.query(Faculty).all()
                
            logger.info("Current Faculty Status:")
            logger.info("-" * 60)
            for faculty in faculty_list:
                status = "Available" if faculty.status else "Unavailable"
                logger.info(f"ID: {faculty.id:2d} | {faculty.name:20s} | {status:11s} | BLE: {faculty.ble_id or 'None'}")
            logger.info("-" * 60)
            
        except Exception as e:
            logger.error(f"Error getting faculty status: {e}")
    
    def run(self):
        """Run the test monitoring."""
        logger.info("Starting MAC Address Detection Test")
        logger.info("=" * 50)
        
        # Setup connections
        if not self.setup_database():
            return False
            
        if not self.setup_mqtt():
            return False
        
        # Show initial faculty status
        self.get_faculty_status(self.faculty_id)
        
        logger.info("\nMonitoring MQTT messages... (Press Ctrl+C to stop)")
        logger.info("Trigger faculty detection by bringing a registered device near the desk unit")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nStopping test...")
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            return True

def main():
    parser = argparse.ArgumentParser(description="Test MAC address-based faculty detection")
    parser.add_argument("--faculty-id", type=int, help="Specific faculty ID to monitor")
    parser.add_argument("--mqtt-host", default="localhost", help="MQTT broker host (default: localhost)")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    
    args = parser.parse_args()
    
    tester = MACDetectionTester(
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
        faculty_id=args.faculty_id
    )
    
    success = tester.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
