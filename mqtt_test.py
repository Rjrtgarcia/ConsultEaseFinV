#!/usr/bin/env python3
"""
MQTT Test Script for ConsultEase Faculty Desk Unit

This script tests MQTT communication with the faculty desk unit by:
1. Subscribing to all relevant topics to monitor messages
2. Publishing test messages to both JSON and plain text topics
3. Providing detailed logging of all MQTT activity
"""

import paho.mqtt.client as mqtt
import json
import time
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default values
DEFAULT_BROKER = "192.168.1.100"
DEFAULT_PORT = 1883
DEFAULT_FACULTY_ID = 1
DEFAULT_FACULTY_NAME = "Jeysibn"

# MQTT Topics
TOPIC_REQUESTS_JSON = "consultease/faculty/{}/requests"
TOPIC_REQUESTS_TEXT = "professor/messages"
TOPIC_FACULTY_MESSAGES = "consultease/faculty/{}/messages"
TOPIC_STATUS = "consultease/faculty/{}/status"
TOPIC_SYSTEM_PING = "consultease/system/ping"

# Message received counter
messages_received = 0

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {args.broker}:{args.port}")
        
        # Subscribe to all relevant topics
        topics = [
            TOPIC_REQUESTS_JSON.format(args.faculty_id),
            TOPIC_REQUESTS_TEXT,
            TOPIC_FACULTY_MESSAGES.format(args.faculty_id),
            TOPIC_STATUS.format(args.faculty_id),
            TOPIC_SYSTEM_PING,
            # Add wildcard subscription to catch all messages
            "consultease/#",
            "professor/#"
        ]
        
        for topic in topics:
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the MQTT broker."""
    global messages_received
    messages_received += 1
    
    topic = msg.topic
    try:
        payload = msg.payload.decode('utf-8')
        logger.info(f"Received message #{messages_received} on topic {topic}")
        logger.info(f"Payload: {payload}")
        
        # Try to parse as JSON for better display
        try:
            json_payload = json.loads(payload)
            logger.info(f"JSON content: {json.dumps(json_payload, indent=2)}")
        except json.JSONDecodeError:
            # Not JSON, which is fine for text messages
            pass
    except Exception as e:
        logger.error(f"Error processing message on {topic}: {e}")

def on_publish(client, userdata, mid):
    """Callback for when a message is published to the MQTT broker."""
    logger.info(f"Message published with ID: {mid}")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the MQTT broker."""
    if rc != 0:
        logger.warning(f"Unexpected disconnection from MQTT broker, code: {rc}")
    else:
        logger.info("Disconnected from MQTT broker")

def send_test_messages(client, faculty_id, faculty_name):
    """Send test messages to all relevant topics."""
    logger.info("Sending test messages to all topics...")
    
    # Create test messages
    text_message = f"Test message from MQTT test script.\nTimestamp: {time.time()}"
    json_message = {
        'id': 999,
        'student_id': 123,
        'student_name': "Test Student",
        'student_department': "Test Department",
        'faculty_id': faculty_id,
        'faculty_name': faculty_name,
        'request_message': text_message,
        'course_code': "TEST101",
        'status': "PENDING",
        'requested_at': time.time(),
        'message': text_message
    }
    
    # Simplified message format for faculty desk unit
    simplified_json = {
        'message': f"Student: Test Student\nCourse: TEST101\nRequest: {text_message}",
        'student_name': "Test Student",
        'course_code': "TEST101",
        'consultation_id': 999,
        'timestamp': time.time()
    }
    
    # Send to all topics
    topics_and_payloads = [
        (TOPIC_REQUESTS_JSON.format(faculty_id), json.dumps(json_message)),
        (TOPIC_REQUESTS_TEXT, text_message),
        (TOPIC_FACULTY_MESSAGES.format(faculty_id), text_message),
        (TOPIC_REQUESTS_JSON.format(faculty_id), json.dumps(simplified_json)),
    ]
    
    for topic, payload in topics_and_payloads:
        logger.info(f"Publishing to {topic}:")
        logger.info(f"Payload: {payload}")
        result = client.publish(topic, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Successfully published to {topic}")
        else:
            logger.error(f"Failed to publish to {topic}, error code: {result.rc}")
        
        # Wait a bit between messages
        time.sleep(1)

def main():
    global args
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MQTT Test Script for ConsultEase Faculty Desk Unit')
    parser.add_argument('--broker', default=DEFAULT_BROKER, help=f'MQTT broker address (default: {DEFAULT_BROKER})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'MQTT broker port (default: {DEFAULT_PORT})')
    parser.add_argument('--faculty-id', type=int, default=DEFAULT_FACULTY_ID, help=f'Faculty ID (default: {DEFAULT_FACULTY_ID})')
    parser.add_argument('--faculty-name', default=DEFAULT_FACULTY_NAME, help=f'Faculty name (default: {DEFAULT_FACULTY_NAME})')
    parser.add_argument('--monitor-only', action='store_true', help='Only monitor topics without sending test messages')
    args = parser.parse_args()
    
    # Create MQTT client
    client_id = f"ConsultEase_MQTT_Test_{int(time.time())}"
    client = mqtt.Client(client_id)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker at {args.broker}:{args.port}")
        client.connect(args.broker, args.port, 60)
        
        # Start the MQTT client loop in a separate thread
        client.loop_start()
        
        # Wait for connection to establish
        time.sleep(2)
        
        if not args.monitor_only:
            # Send test messages
            send_test_messages(client, args.faculty_id, args.faculty_name)
            
            # Wait for messages to be processed
            logger.info("Waiting for messages to be processed...")
            time.sleep(5)
            
            # Send another round of test messages
            logger.info("Sending another round of test messages...")
            send_test_messages(client, args.faculty_id, args.faculty_name)
        
        # Keep the script running to monitor messages
        logger.info("Monitoring MQTT messages. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Exiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Disconnect from MQTT broker
        client.loop_stop()
        client.disconnect()
        logger.info("Disconnected from MQTT broker")

if __name__ == "__main__":
    main()
