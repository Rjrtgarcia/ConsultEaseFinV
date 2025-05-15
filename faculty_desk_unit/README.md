# ConsultEase - Faculty Desk Unit

This is the firmware for the Faculty Desk Unit component of the ConsultEase system. This unit is installed at each faculty member's desk and shows consultation requests from students while automatically detecting the faculty's presence via BLE.

## Hardware Requirements

- ESP32 Development Board (ESP32-WROOM-32 or similar)
- 2.4" TFT Display (ST7789 SPI interface)
- BLE Beacon (can be another ESP32 or dedicated BLE beacon)
- Power supply (USB or wall adapter)

## Pin Connections

### Display Connections (SPI)
| TFT Display Pin | ESP32 Pin |
|-----------------|-----------|
| MOSI/SDA        | GPIO 23   |
| MISO            | GPIO 19   |
| SCK/CLK         | GPIO 18   |
| CS              | GPIO 5    |
| DC              | GPIO 21   |
| RST             | GPIO 22   |
| VCC             | 3.3V      |
| GND             | GND       |

## Software Dependencies

The following libraries need to be installed via the Arduino Library Manager:

- WiFi
- PubSubClient (by Nick O'Leary)
- BLEDevice
- BLEServer
- BLEUtils
- BLE2902
- SPI
- Adafruit_GFX
- Adafruit_ST7789
- time
- NimBLE-Arduino (for BLE beacon)

## Setup and Configuration

1. Install the required libraries in Arduino IDE
2. Open `faculty_desk_unit.ino` in Arduino IDE
3. Update the configuration in `config.h`:
   - WiFi credentials (`WIFI_SSID` and `WIFI_PASSWORD`)
   - MQTT broker IP address (`MQTT_SERVER`)
   - Faculty ID and name (`FACULTY_ID` and `FACULTY_NAME`)
   - BLE settings (including always-on option)
4. Compile and upload to your ESP32

## Testing

To test the faculty desk unit, you can use the new BLE test script:

1. Make sure the central system is running
2. Make sure the MQTT broker is running
3. Run the BLE test script:
   ```bash
   python scripts/test_ble_connection.py test
   ```

This script will:
1. Simulate a BLE beacon
2. Simulate a faculty desk unit
3. Test MQTT communication between components
4. Verify proper status updates

You can also use the older test scripts in the `test_scripts` directory:
- On Windows: `test_scripts\test_faculty_desk_unit.bat`
- On Linux/macOS: `bash test_scripts/test_faculty_desk_unit.sh`

## Usage

1. The unit will automatically connect to WiFi and the MQTT broker
2. It will act as a BLE server, but simulates an always-connected BLE client
3. The faculty status is always set to "Available" (BLE always on)
4. The unit will periodically send "keychain_connected" messages to maintain the available status
5. Consultation requests from students will appear on the display

### BLE Always-On Feature

This version of the faculty desk unit simulates an always-connected BLE client, which means:
- The faculty status is always shown as "Available" in the central system
- The unit will still accept real BLE client connections, but won't change status when they disconnect
- Every 5 minutes, the unit sends a "keychain_connected" message to ensure the faculty remains available
- This feature is useful for faculty members who want to be always available for consultations

### Database Integration

The central system has been updated to support the always-on BLE client feature:
- A new "always_available" field has been added to the Faculty model
- Faculty members with this flag set will always be shown as available
- The admin dashboard has been updated to allow setting this flag
- The Jeysibn faculty member is set to always available by default

To update an existing database with the new schema, run:
```
python scripts/update_faculty_schema.py
python scripts/update_jeysibn_faculty.py
```

## Manual Testing

You can also test the faculty desk unit manually:

1. Create a faculty member:
   ```
   python test_scripts/create_jeysibn_faculty.py
   ```

2. Simulate BLE beacon connected event:
   ```
   python test_scripts/simulate_ble_connection.py --broker <mqtt_broker_ip> --connect
   ```

3. Send a consultation request:
   ```
   python test_scripts/send_consultation_request.py
   ```

4. Simulate BLE beacon disconnected event:
   ```
   python test_scripts/simulate_ble_connection.py --broker <mqtt_broker_ip> --disconnect
   ```

Replace `<mqtt_broker_ip>` with the IP address of your MQTT broker.

## Troubleshooting

### MQTT Connection Issues

If the faculty desk unit is not connecting to the MQTT broker:
- Make sure the MQTT broker IP address is correct
- Make sure the MQTT broker is running
- Make sure the ESP32 is connected to the WiFi network

### BLE Issues

The faculty desk unit is configured to always report as connected, but if you want to connect a real BLE client:
- Make sure the BLE client (keychain) is powered on
- Make sure the BLE client is within range of the ESP32
- Check the serial output for BLE-related messages
- Note that disconnecting a real BLE client will not change the faculty status (it will remain "Available")

### Display Issues

If the display is not working:
- Check the wiring connections
- Make sure the display is powered on
- Try running the test screen function to verify the display is working

## Integration with Central System

The Faculty Desk Unit communicates with the central system via MQTT. The central system publishes consultation requests to the following topics:

- `consultease/faculty/{faculty_id}/requests` - Main topic for consultation requests
- `professor/messages` - Alternative topic for backward compatibility

The Faculty Desk Unit publishes faculty status updates to:

- `consultease/faculty/{faculty_id}/status` - Faculty status updates
- `professor/status` - Alternative topic for backward compatibility

When the BLE client connects or disconnects, the Faculty Desk Unit publishes a status update with `keychain_connected` or `keychain_disconnected` message, which the central system uses to update the faculty status in the database.

## MQTT Message Format

### Consultation Request (from Central System to Faculty Desk Unit)
```
Student: Alice Johnson
Course: CS101
Request: Need help with assignment
```

### Status Update (from Faculty Desk Unit to Central System)
```
keychain_connected
```

or

```
keychain_disconnected
```

## UI Features

The faculty desk unit features a modern UI with the following elements:

- Gold accent bar on the left side
- Header with date and time
- Message area with title and content
- Status bar at the bottom
- National University Philippines color scheme (blue and gold)
- Smooth transitions between screens