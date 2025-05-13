# ConsultEase Deployment Guide (Updated)

This guide provides comprehensive instructions for deploying the ConsultEase system, including the Central System (Raspberry Pi) and Faculty Desk Units (ESP32). This updated guide incorporates recent improvements to the system.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Central System Setup](#central-system-setup)
3. [On-Screen Keyboard Setup](#on-screen-keyboard-setup)
4. [Faculty Desk Unit Setup](#faculty-desk-unit-setup)
5. [BLE Beacon Setup](#ble-beacon-setup)
6. [Network Configuration](#network-configuration)
7. [Database Setup](#database-setup)
8. [System Testing](#system-testing)
9. [Troubleshooting](#troubleshooting)
10. [Performance Optimization](#performance-optimization)

## Hardware Requirements

### Central System (Raspberry Pi)
- Raspberry Pi 4 (4GB RAM recommended)
- 10.1-inch touchscreen (1024x600 resolution)
- USB RFID IC Reader
- 32GB+ microSD card
- Power supply (5V, 3A recommended)
- Case or mounting solution

### Faculty Desk Unit (per faculty member)
- ESP32 development board
- 2.4-inch TFT SPI Display (ST7789)
- Power supply (USB or wall adapter)
- Case or enclosure

### BLE Beacon (per faculty member)
- ESP32 development board (smaller form factor recommended)
- Small LiPo battery (optional for portable use)
- Case or enclosure

### Additional Requirements
- Local network with Wi-Fi access
- Ethernet cable (optional for Raspberry Pi)
- RFID cards for students

## Central System Setup

### 1. Operating System Installation
1. Download Raspberry Pi OS (64-bit, Bookworm) from the [official website](https://www.raspberrypi.org/software/operating-systems/)
2. Flash the OS to the microSD card using [Raspberry Pi Imager](https://www.raspberrypi.org/software/)
3. Insert the microSD card into the Raspberry Pi and connect the display, keyboard, and mouse
4. Power on the Raspberry Pi and complete the initial setup

### 2. Touchscreen Configuration
1. Connect the touchscreen to the Raspberry Pi
2. Update the system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. Configure the display resolution if needed:
   ```bash
   sudo nano /boot/config.txt
   ```
   Add these lines at the end:
   ```
   hdmi_group=2
   hdmi_mode=87
   hdmi_cvt=1024 600 60 6 0 0 0
   ```
4. Save and reboot the Raspberry Pi:
   ```bash
   sudo reboot
   ```
5. Calibrate the touchscreen (if needed):
   ```bash
   cd /path/to/consultease
   sudo chmod +x scripts/calibrate_touch.sh
   sudo ./scripts/calibrate_touch.sh
   ```

### 3. Required Software Installation
1. Install required packages:
   ```bash
   sudo apt install -y git python3-pip python3-pyqt5 python3-dev libpq-dev mosquitto mosquitto-clients
   ```
2. Install PostgreSQL:
   ```bash
   sudo apt install -y postgresql postgresql-contrib
   ```
3. Start the PostgreSQL and Mosquitto services:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto
   ```

### 4. ConsultEase Installation
1. Clone the ConsultEase repository:
   ```bash
   git clone https://github.com/yourusername/ConsultEase.git
   cd ConsultEase
   ```
2. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

### 5. Database Setup
1. Create the database and user:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE consultease;"
   sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"
   ```
2. Configure environment variables (create a `.env` file in the project root):
   ```
   DB_USER=piuser
   DB_PASSWORD=password
   DB_HOST=localhost
   DB_NAME=consultease
   MQTT_BROKER_HOST=localhost
   MQTT_BROKER_PORT=1883
   CONSULTEASE_KEYBOARD=onboard
   ```

## On-Screen Keyboard Setup

ConsultEase now prioritizes the onboard keyboard over squeekboard for better touch input support.

### 1. Install Onboard Keyboard (Recommended)
```bash
cd /path/to/consultease
chmod +x scripts/install_onboard.sh
./scripts/install_onboard.sh
```

This script will:
- Install the onboard keyboard
- Configure it for touch-friendly operation
- Set up environment variables
- Create keyboard management scripts
- Disable squeekboard to avoid conflicts
- Create autostart entries

### 2. Keyboard Management Scripts
After running the installation script, you'll have these keyboard management scripts:
- `~/keyboard-toggle.sh` - Toggle keyboard visibility
- `~/keyboard-show.sh` - Force show keyboard
- `~/keyboard-hide.sh` - Force hide keyboard

### 3. Keyboard Troubleshooting
If you encounter issues with the keyboard:
```bash
cd /path/to/consultease
chmod +x scripts/fix_keyboard.sh
./scripts/fix_keyboard.sh
```

## Faculty Desk Unit Setup

### 1. Arduino IDE Installation
1. Download and install the Arduino IDE from the [official website](https://www.arduino.cc/en/software)
2. Install the ESP32 board package:
   - In Arduino IDE, go to File > Preferences
   - Add this URL to the "Additional Boards Manager URLs" field:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools > Board > Boards Manager
   - Search for ESP32 and install the latest version

### 2. Required Libraries Installation
Install the following libraries via the Arduino Library Manager (Tools > Manage Libraries):
- TFT_eSPI by Bodmer
- PubSubClient by Nick O'Leary
- ArduinoJson by Benoit Blanchon
- NimBLE-Arduino by h2zero

### 3. TFT_eSPI Configuration
1. Navigate to your Arduino libraries folder (usually in Documents/Arduino/libraries)
2. Find the TFT_eSPI folder
3. Replace the User_Setup.h file with the one from the ConsultEase repository
4. Alternatively, edit the file to match your display configuration

### 4. Faculty Desk Unit Firmware
1. Open the `faculty_desk_unit.ino` sketch in Arduino IDE
2. Update the following settings:
   - WiFi credentials (`ssid` and `password`)
   - MQTT broker IP address (`mqtt_server`)
   - Faculty name (`current_user`)
3. Upload the sketch to your ESP32

## BLE Beacon Setup

### 1. Testing BLE Functionality
Before deploying the BLE beacons, you can test the BLE functionality using the provided test script:
```bash
cd /path/to/consultease
python scripts/test_ble_connection.py test
```

This script will:
- Simulate a BLE beacon
- Simulate a faculty desk unit
- Test MQTT communication between components
- Verify proper status updates

### 2. BLE Beacon Configuration
1. Open the `ble_beacon.ino` sketch in Arduino IDE
2. Update the following settings:
   - Faculty ID (`faculty_id`)
   - Beacon name (`device_name`)
3. Upload the sketch to your ESP32

## Network Configuration

### 1. MQTT Broker Configuration
1. Configure Mosquitto for better security:
   ```bash
   sudo nano /etc/mosquitto/mosquitto.conf
   ```
2. Add the following lines:
   ```
   listener 1883
   allow_anonymous true
   ```
3. Restart Mosquitto:
   ```bash
   sudo systemctl restart mosquitto
   ```

### 2. MQTT Communication Testing
Test the MQTT communication between components:
```bash
# Subscribe to faculty status topic
mosquitto_sub -t "consultease/faculty/+/status"

# Subscribe to consultation requests topic
mosquitto_sub -t "consultease/faculty/+/requests"

# Publish a test message
mosquitto_pub -t "consultease/faculty/1/status" -m "keychain_connected"
```

## Database Setup

### 1. Initial Data Setup
1. Create a script to add initial admin user:
   ```bash
   sudo nano add_admin.py
   ```
2. Add the following content:
   ```python
   from central_system.models import Admin, init_db
   from central_system.controllers import AdminController

   # Initialize database
   init_db()

   # Create admin controller
   admin_controller = AdminController()

   # Ensure default admin exists
   admin_controller.ensure_default_admin()

   print("Default admin created with username 'admin' and password 'admin123'")
   print("Please change this password immediately!")
   ```
3. Run the script:
   ```bash
   python3 add_admin.py
   ```

### 2. Sample Data (Optional)
1. Create a script to add sample data for testing:
   ```bash
   sudo nano add_sample_data.py
   ```
2. Add faculty and student records as needed
3. Run the script:
   ```bash
   python3 add_sample_data.py
   ```

## System Testing

### 1. UI Improvements Testing
Test the improved UI components:
```bash
cd /path/to/consultease
python scripts/test_ui_improvements.py
```

This script will:
- Test the improved UI transitions
- Test the enhanced consultation panel
- Verify smooth animations and proper user feedback

### 2. RFID Testing
Test the RFID functionality:
```bash
cd /path/to/consultease
python scripts/debug_rfid.py list
python scripts/debug_rfid.py test
```

If you encounter issues with the RFID reader:
```bash
cd /path/to/consultease
sudo chmod +x scripts/fix_rfid.sh
sudo ./scripts/fix_rfid.sh
```

### 3. Full System Testing
1. Start the ConsultEase application:
   ```bash
   cd /path/to/consultease
   python central_system/main.py
   ```
2. Test the following functionality:
   - RFID card scanning
   - Faculty status display
   - Consultation requests
   - On-screen keyboard
   - Touch interface
   - BLE presence detection

## Troubleshooting

### 1. On-Screen Keyboard Issues
If the on-screen keyboard doesn't appear:
- Run `~/keyboard-show.sh` to manually show it
- Press F5 in the application to toggle the keyboard
- Check if onboard is installed: `which onboard`
- Run the fix script: `./scripts/fix_keyboard.sh`

### 2. MQTT Connection Issues
If MQTT communication is not working:
- Check if Mosquitto is running: `systemctl status mosquitto`
- Verify MQTT broker IP address in the `.env` file
- Test MQTT manually: `mosquitto_sub -t "consultease/#"`
- Check firewall settings: `sudo ufw status`

### 3. Database Connection Issues
If database connection fails:
- Check PostgreSQL status: `systemctl status postgresql`
- Verify database credentials in the `.env` file
- Test database connection: `psql -U piuser -d consultease`
- Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`

## Performance Optimization

### 1. Raspberry Pi Optimization
1. Disable unnecessary services:
   ```bash
   sudo systemctl disable bluetooth.service
   sudo systemctl disable avahi-daemon.service
   ```
2. Add swap space if needed:
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=1024
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

### 2. Database Optimization
1. Configure PostgreSQL for better performance:
   ```bash
   sudo nano /etc/postgresql/*/main/postgresql.conf
   ```
2. Adjust the following settings:
   ```
   shared_buffers = 128MB
   work_mem = 4MB
   maintenance_work_mem = 32MB
   ```
3. Restart PostgreSQL:
   ```bash
   sudo systemctl restart postgresql
   ```

### 3. Application Optimization
1. Enable fullscreen mode:
   ```bash
   cd /path/to/consultease
   python scripts/enable_fullscreen.py
   ```
2. Configure auto-start:
   ```bash
   sudo nano /etc/systemd/system/consultease.service
   ```
   Add the following content:
   ```
   [Unit]
   Description=ConsultEase Central System
   After=network.target postgresql.service mosquitto.service

   [Service]
   ExecStart=/usr/bin/python3 /path/to/consultease/central_system/main.py
   WorkingDirectory=/path/to/consultease
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl enable consultease.service
   sudo systemctl start consultease.service
   ```

## Conclusion

This deployment guide covers the setup and configuration of the ConsultEase system with the latest improvements. If you encounter any issues not covered in this guide, please refer to the troubleshooting section or contact the development team for assistance.
