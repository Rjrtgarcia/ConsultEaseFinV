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
| DC              | GPIO 2    |
| RST             | GPIO 4    |
| BL              | GPIO 15   |
| VCC             | 3.3V      |
| GND             | GND       |

## Software Dependencies

The following libraries need to be installed via the Arduino Library Manager:

- TFT_eSPI (by Bodmer)
- PubSubClient (by Nick O'Leary)
- ArduinoJson (by Benoit Blanchon)
- NimBLE-Arduino (by h2zero)

## Setup and Configuration

1. Install the required libraries in Arduino IDE
2. Copy the `User_Setup.h` file to the `libraries/TFT_eSPI` folder to configure the display
3. Open `config.h` and update the following settings:
   - WiFi credentials (`WIFI_SSID` and `WIFI_PASSWORD`)
   - MQTT server IP address (`MQTT_SERVER`)
   - Faculty ID (`FACULTY_ID`) - This should match the faculty ID in the database
   - Faculty name (`FACULTY_NAME`) - This should match the faculty name in the database
4. Open `faculty_desk_unit.ino` in Arduino IDE
5. Compile and upload to your ESP32

### BLE Beacon Configuration

1. Open the `ble_beacon/config.h` file and update the following settings:
   - Faculty ID (`FACULTY_ID`) - This should match the faculty ID in the database
   - Faculty name (`FACULTY_NAME`) - This should match the faculty name in the database
2. Open `ble_beacon/ble_beacon.ino` in Arduino IDE
3. Compile and upload to a separate ESP32 device that will serve as the faculty's BLE beacon

## Usage

1. The unit will automatically connect to WiFi and the MQTT broker
2. It will scan for the configured BLE beacon at regular intervals
3. When the faculty's BLE beacon is detected, status updates to "Available"
4. When the beacon is not detected for 15 seconds, status updates to "Unavailable"
5. Consultation requests from students will appear on the display

## Troubleshooting

- If the display doesn't work, check the pin connections and TFT_eSPI configuration
- If BLE detection isn't working, verify the target BLE address and RSSI threshold
- For MQTT connection issues, check the broker address and network connectivity
- Serial monitor (115200 baud) provides debugging information

## Advanced Settings

You can modify these parameters in the `config.h` file:

- `BLE_SCAN_INTERVAL`: Time between BLE scans (milliseconds)
- `BLE_SCAN_DURATION`: Duration of each BLE scan (seconds)
- `BLE_RSSI_THRESHOLD`: Signal strength threshold for presence detection
- `TFT_ROTATION`: Display rotation (0=Portrait, 1=Landscape, 2=Inverted Portrait, 3=Inverted Landscape)
- Various color settings for the UI theme

## Integration with Central System

The Faculty Desk Unit communicates with the central system via MQTT. The central system publishes consultation requests to the following topics:

- `consultease/faculty/{faculty_id}/requests` - Main topic for consultation requests
- `professor/messages` - Alternative topic for backward compatibility

The Faculty Desk Unit publishes faculty status updates to:

- `consultease/faculty/{faculty_id}/status` - Faculty status updates
- `professor/status` - Alternative topic for backward compatibility

When the BLE beacon is detected, the Faculty Desk Unit publishes a status update with `keychain_connected` or `keychain_disconnected` message, which the central system uses to update the faculty status in the database.

## MQTT Message Format

### Consultation Request (from Central System to Faculty Desk Unit)
```json
{
  "message": "Student: Alice Johnson\nCourse: CS101\nRequest: Need help with assignment",
  "student_name": "Alice Johnson",
  "course_code": "CS101",
  "consultation_id": 123,
  "timestamp": "2025-05-02T09:46:02"
}
```

### Status Update (from Faculty Desk Unit to Central System)
```json
{
  "status": true,
  "faculty_id": 1
}
```

or

```json
{
  "keychain_connected": true,
  "faculty_id": 1
}
```