#!/usr/bin/env python3
"""
ConsultEase - Faculty Desk Unit Test Script

This script simulates sending messages to the faculty desk unit via MQTT.
It can be used to test the faculty desk unit without needing to set up the entire central system.

Usage:
    python test_faculty_desk.py [faculty_id] [message]

Example:
    python test_faculty_desk.py 1 "Hello, this is a test message"
"""

import sys
import time
import paho.mqtt.client as mqtt

# Default values
DEFAULT_FACULTY_ID = 1
DEFAULT_MESSAGE = "Test consultation request from a student. Please check your schedule for availability."

# MQTT Configuration
MQTT_BROKER = "192.168.1.100"  # Replace with your Raspberry Pi IP address
MQTT_PORT = 1883
MQTT_TOPIC_REQUESTS = "consultease/faculty/%d/requests"
MQTT_TOPIC_STATUS = "consultease/faculty/%d/status"
MQTT_CLIENT_ID = "ConsultEase_Test_Script"

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print(f"Connected to MQTT broker at {MQTT_BROKER}")
    else:
        print(f"Failed to connect to MQTT broker, return code: {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the MQTT broker."""
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

def on_publish(client, userdata, mid):
    """Callback for when a message is published to the MQTT broker."""
    print(f"Message published with ID: {mid}")

def main():
    """Main function to send a test message to the faculty desk unit."""
    # Parse command line arguments
    faculty_id = DEFAULT_FACULTY_ID
    message = DEFAULT_MESSAGE
    
    if len(sys.argv) > 1:
        try:
            faculty_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid faculty ID: {sys.argv[1]}. Using default: {DEFAULT_FACULTY_ID}")
    
    if len(sys.argv) > 2:
        message = sys.argv[2]
    
    # Set up MQTT client
    client = mqtt.Client(MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    
    # Connect to MQTT broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        return
    
    # Start the MQTT client loop in a separate thread
    client.loop_start()
    
    # Wait for connection to establish
    time.sleep(1)
    
    # Subscribe to status topic to see if the faculty desk unit is connected
    status_topic = MQTT_TOPIC_STATUS % faculty_id
    client.subscribe(status_topic)
    print(f"Subscribed to topic: {status_topic}")
    
    # Publish a test message to the faculty desk unit
    requests_topic = MQTT_TOPIC_REQUESTS % faculty_id
    print(f"Sending message to faculty ID {faculty_id} on topic: {requests_topic}")
    print(f"Message: {message}")
    
    result = client.publish(requests_topic, message)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("Message sent successfully")
    else:
        print(f"Failed to send message, return code: {result.rc}")
    
    # Wait for a moment to see if we get any status updates
    print("Waiting for status updates (5 seconds)...")
    time.sleep(5)
    
    # Disconnect from MQTT broker
    client.loop_stop()
    client.disconnect()
    print("Disconnected from MQTT broker")

if __name__ == "__main__":
    main()
