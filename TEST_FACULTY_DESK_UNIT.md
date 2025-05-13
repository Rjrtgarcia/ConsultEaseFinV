# Testing the Faculty Desk Unit

This document provides instructions for testing the Faculty Desk Unit component of the ConsultEase system.

## Prerequisites

### Hardware Requirements
- ESP32 Development Board
- 2.4" TFT Display (ST7789 SPI interface)
- USB cable for power and programming
- Raspberry Pi or computer running MQTT broker (optional for full testing)

### Software Requirements
- Arduino IDE with ESP32 board support
- Required libraries:
  - WiFi.h
  - PubSubClient.h
  - BLEDevice.h
  - SPI.h
  - Adafruit_GFX.h
  - Adafruit_ST7789.h
- Python 3.6+ with paho-mqtt library (for test scripts)
- Mosquitto MQTT broker (optional for full testing)

## Setup Instructions

### 1. Update Configuration

Before uploading the code to the ESP32, update the configuration in `faculty_desk_unit/config.h`:

- Set `MQTT_SERVER` to the IP address of your MQTT broker
- Update `FACULTY_NAME` and `FACULTY_ID` if needed
- Verify WiFi credentials (`WIFI_SSID` and `WIFI_PASSWORD`)

### 2. Upload the Firmware

1. Connect the ESP32 to your computer via USB
2. Open `faculty_desk_unit/faculty_desk_unit.ino` in Arduino IDE
3. Select the correct board and port
4. Click the Upload button
5. Open the Serial Monitor (115200 baud) to view debug output

### 3. Test with MQTT Messages

You can use the provided Python script to send test messages to the faculty desk unit:

```bash
# Install required Python library
pip install paho-mqtt

# Run the test script
python test_faculty_desk.py [faculty_id] [message]
```

Example:
```bash
python test_faculty_desk.py 1 "Hello, this is a test consultation request"
```

### 4. Test BLE Beacon (Optional)

If you want to test the BLE functionality, you have two options:

#### Option 1: Use a Second ESP32 as a BLE Beacon
1. Open `faculty_desk_unit/ble_beacon/ble_beacon.ino` in Arduino IDE
2. Upload to a second ESP32
3. The faculty desk unit should detect the beacon and update its status

#### Option 2: Use the Python BLE Beacon Simulator
```bash
# Install required Python library
pip install bluepy

# Run the BLE beacon simulator
python test_ble_beacon.py [faculty_id] [device_name]
```

Example:
```bash
python test_ble_beacon.py 1 "ConsultEase-Faculty"
```

## Expected Behavior

When the faculty desk unit is working correctly, you should observe:

1. **Startup Sequence**:
   - Display shows National University colors and logo
   - System connects to WiFi
   - BLE server starts
   - Status shows "System Ready"

2. **Message Reception**:
   - When a message is sent via MQTT, it should appear on the display
   - The message should be properly formatted with a title and content

3. **BLE Functionality**:
   - The unit should detect when a BLE beacon is nearby
   - Status should update to "Keychain connected!"
   - MQTT status messages should be sent periodically

## Troubleshooting

### Display Issues
- Verify the pin connections between ESP32 and the TFT display
- Check that the display is properly powered
- Try adjusting the display rotation in the code

### WiFi Connection Issues
- Verify WiFi credentials in the config.h file
- Ensure the WiFi network is available and within range
- Check the serial output for connection errors

### MQTT Issues
- Verify the MQTT broker IP address is correct
- Ensure the MQTT broker is running and accessible
- Check the serial output for MQTT connection errors
- Try using an MQTT client (like MQTT Explorer) to monitor topics

### BLE Issues
- Make sure Bluetooth is enabled on your device
- Check that the BLE UUIDs match between the beacon and desk unit
- Verify the BLE beacon is powered and advertising
- Check the serial output for BLE connection messages

## Additional Notes

- The faculty desk unit is designed to always show as "Available" even when no BLE beacon is detected
- The display updates the time every minute
- MQTT status messages are sent every 5 minutes to maintain the "Available" status
