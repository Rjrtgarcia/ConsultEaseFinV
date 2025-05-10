# ConsultEase - Technical Context

## Technologies Used

### Central System (Raspberry Pi)

#### Hardware
- **Raspberry Pi 4** (Bookworm 64-bit)
- **10.1-inch touchscreen** (1024x600 resolution)
- **USB RFID IC Reader**

#### Software
- **Python 3.9+** (Primary programming language)
- **PyQt5** (GUI framework)
- **PostgreSQL** (Database)
- **Paho MQTT** (MQTT client library)
- **SQLAlchemy** (ORM for database operations)
- **evdev** (Linux input device library for RFID reader)

### Faculty Desk Unit (ESP32)

#### Hardware
- **ESP32 microcontroller**
- **2.4-inch TFT SPI Screen** (ST7789)

#### Software
- **Arduino IDE** (Development environment)
- **ESP32 Arduino Core** (ESP32 support for Arduino)
- **TFT_eSPI** (Display library)
- **NimBLE-Arduino** (BLE library)
- **PubSubClient** (MQTT client library)
- **ArduinoJson** (JSON parsing)

## Development Setup

### Central System
1. **OS Configuration**
   - Raspberry Pi OS (Bookworm 64-bit)
   - Desktop environment configured for touchscreen
   - Auto-start application on boot

2. **Dependencies**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and pip
   sudo apt install python3 python3-pip -y
   
   # Install PyQt5
   sudo apt install python3-pyqt5 -y
   
   # Install PostgreSQL
   sudo apt install postgresql postgresql-contrib -y
   
   # Install Python libraries
   pip3 install paho-mqtt sqlalchemy psycopg2-binary evdev
   ```

3. **Database Setup**
   ```bash
   # Create database and user
   sudo -u postgres psql -c "CREATE DATABASE consultease;"
   sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"
   ```

### Faculty Desk Unit
1. **Arduino IDE Setup**
   - Arduino IDE 2.0+
   - ESP32 board manager URL: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

2. **Libraries**
   - TFT_eSPI
   - NimBLE-Arduino
   - PubSubClient
   - ArduinoJson

3. **ESP32 Configuration**
   - Flash with 4MB of program storage
   - PSRAM enabled

## Communication Protocols

### MQTT
- **Broker**: Mosquitto MQTT broker running on Raspberry Pi
- **Topics**:
  - `consultease/faculty/{faculty_id}/status` - Faculty status updates
  - `consultease/faculty/{faculty_id}/requests` - Consultation requests
  - `consultease/system/notifications` - System notifications

### Database Schema
```
faculty
  id (PK)
  name
  department
  email
  ble_id
  status

students
  id (PK)
  name
  department
  rfid_uid

consultations
  id (PK)
  student_id (FK)
  faculty_id (FK)
  request_message
  timestamp
  status
```

### BLE Protocol
- **Scanning interval**: 5 seconds
- **Service UUID**: Custom UUID for faculty identification
- **Detection threshold**: RSSI > -80dBm for presence detection

## Technical Constraints

1. **Power Considerations**
   - ESP32 should operate on USB power or battery
   - Raspberry Pi requires stable power supply
   - BLE beacons require regular battery maintenance (2-3 week battery life)

2. **Network Requirements**
   - Wi-Fi network available for both devices
   - MQTT broker accessible on local network
   - Network ports open for MQTT communication (default: 1883)
   - All devices must be on the same local network
   - Optional: Internet connectivity for remote monitoring

3. **Security Considerations**
   - Admin authentication required for faculty management
   - Secured database connection
   - Encrypted MQTT communication (TLS)
   - Secure storage of credentials

4. **Performance Requirements**
   - UI response time < 500ms
   - MQTT message delivery < 1 second
   - BLE detection latency < 10 seconds
   - System should support up to 50 simultaneous users
   - Database backups should be performed weekly
   - System should maintain >99% uptime

5. **Maintenance Requirements**
   - Weekly database maintenance recommended
   - System restart once per week for optimal performance
   - BLE beacon batteries should be checked monthly
   - Regular backups of database data using Admin interface

## UI Theme and Styling

1. **Color Scheme**
   - Background: White (#ffffff)
   - Primary accent: Navy blue (#0d3b66) for buttons, selection highlighting, and headings
   - Secondary accent: Gold (#ffc233) for primary buttons, tab headers, and subheadings
   - Text: Dark gray (#333333) for optimal readability
   - Status indicators: Green (#28a745) for available, Red (#e63946) for unavailable

2. **Styling Approach**
   - Modern, clean design with consistent spacing
   - Touch-optimized element sizing (minimum 48x48px touch targets)
   - Cohesive styling through centralized stylesheet.py
   - Light theme with high contrast for readability
   - Custom styling for faculty cards and interactive elements

3. **Theme Configuration**
   - Default theme set in main.py with environment variable support
   - Can be configured through CONSULTEASE_THEME environment variable:
     ```bash
     export CONSULTEASE_THEME=light  # For light theme (default after update)
     ```

## Development Workflow
1. Feature branch development
2. Local testing on development hardware
3. Integration testing with both components
4. Deployment to production hardware 