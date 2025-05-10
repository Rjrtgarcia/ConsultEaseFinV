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
3. Open `faculty_desk_unit.ino` in Arduino IDE
4. Modify the configuration section at the top of the sketch:
   - Update WiFi credentials
   - Set the MQTT broker address to your Raspberry Pi IP
   - Update the BLE beacon MAC address for the faculty member
   - Set the faculty ID to match the database record
   - Adjust faculty name as needed
5. Compile and upload to your ESP32

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

You can modify these parameters in the sketch:

- `BLE_SCAN_INTERVAL`: Time between BLE scans (seconds)
- `BLE_SCAN_DURATION`: Duration of each BLE scan (seconds)
- `BLE_RSSI_THRESHOLD`: Signal strength threshold for presence detection
- `BLE_TIMEOUT`: Time before marking faculty as away (seconds)
- `MAX_REQUESTS`: Maximum number of consultation requests to display 