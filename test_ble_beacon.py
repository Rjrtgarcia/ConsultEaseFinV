#!/usr/bin/env python3
"""
ConsultEase - BLE Beacon Simulator

This script simulates a BLE beacon for testing the faculty desk unit.
It requires a Bluetooth adapter and the bluepy library.

Usage:
    python test_ble_beacon.py [faculty_id] [device_name]

Example:
    python test_ble_beacon.py 1 "ConsultEase-Faculty"
"""

import sys
import time
import random
from bluepy.btle import UUID, Peripheral, DefaultDelegate, ADDR_TYPE_RANDOM

# Default values
DEFAULT_FACULTY_ID = 1
DEFAULT_DEVICE_NAME = "ConsultEase-Faculty"

# BLE Configuration
SERVICE_UUID = "91BAD35B-F3CB-4FC1-8603-88D5137892A6"
CHARACTERISTIC_UUID = "D9473AA3-E6F4-424B-B6E7-A5F94FDDA285"

class BLEBeaconSimulator:
    """Class to simulate a BLE beacon for the faculty desk unit."""
    
    def __init__(self, faculty_id, device_name):
        """Initialize the BLE beacon simulator."""
        self.faculty_id = faculty_id
        self.device_name = device_name
        self.peripheral = None
        
    def start_advertising(self):
        """Start advertising as a BLE beacon."""
        try:
            # Create a peripheral device
            self.peripheral = Peripheral()
            
            # Set up the service
            service = self.peripheral.addService(UUID(SERVICE_UUID))
            
            # Add a characteristic
            char = service.addCharacteristic(
                UUID(CHARACTERISTIC_UUID),
                ["read", "notify"]
            )
            
            # Set the initial value
            faculty_id_bytes = self.faculty_id.to_bytes(4, byteorder='big')
            char.setValue(faculty_id_bytes)
            
            # Start advertising
            self.peripheral.advertise(self.device_name, [SERVICE_UUID])
            
            print(f"Started advertising as '{self.device_name}' with faculty ID {self.faculty_id}")
            print(f"Service UUID: {SERVICE_UUID}")
            print(f"Characteristic UUID: {CHARACTERISTIC_UUID}")
            
            # Keep advertising until interrupted
            try:
                while True:
                    # Update the characteristic value occasionally
                    if random.random() < 0.1:  # 10% chance each second
                        # Add some random data to simulate updates
                        random_data = random.randint(0, 255).to_bytes(1, byteorder='big')
                        new_value = faculty_id_bytes + random_data
                        char.setValue(new_value)
                        print(f"Updated characteristic value: {new_value.hex()}")
                    
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Stopping advertising...")
                self.peripheral.stopAdvertising()
                
        except Exception as e:
            print(f"Error starting BLE advertising: {e}")
            if self.peripheral:
                self.peripheral.stopAdvertising()

def main():
    """Main function to simulate a BLE beacon."""
    # Parse command line arguments
    faculty_id = DEFAULT_FACULTY_ID
    device_name = DEFAULT_DEVICE_NAME
    
    if len(sys.argv) > 1:
        try:
            faculty_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid faculty ID: {sys.argv[1]}. Using default: {DEFAULT_FACULTY_ID}")
    
    if len(sys.argv) > 2:
        device_name = sys.argv[2]
    
    # Create and start the BLE beacon simulator
    simulator = BLEBeaconSimulator(faculty_id, device_name)
    simulator.start_advertising()

if __name__ == "__main__":
    main()
