# ConsultEase

A comprehensive system for enhanced student-faculty interaction, featuring RFID-based authentication, real-time faculty availability, and streamlined consultation requests.

## Components

### Central System (Raspberry Pi)
- PyQt5 user interface for student interaction
- RFID-based authentication
- Real-time faculty availability display
- Consultation request management
- Secure admin interface
- Touch-optimized UI with on-screen keyboard support

### Faculty Desk Unit (ESP32)
- 2.4" TFT Display for consultation requests
- BLE-based presence detection
- MQTT communication with Central System

## Requirements

### Central System
- Raspberry Pi 4 (Bookworm 64-bit)
- 10.1-inch touchscreen (1024x600 resolution)
- USB RFID IC Reader
- Python 3.9+
- PostgreSQL database

### Faculty Desk Unit
- ESP32 microcontroller
- 2.4-inch TFT SPI Screen (ST7789)
- Arduino IDE 2.0+

## Installation

### Central System

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE consultease;"
sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"
```

3. Install touchscreen utilities (for Raspberry Pi):
```bash
sudo chmod +x scripts/install_squeekboard.sh
sudo ./scripts/install_squeekboard.sh
```

4. Calibrate the touchscreen (if needed):
```bash
sudo chmod +x scripts/calibrate_touch.sh
sudo ./scripts/calibrate_touch.sh
```

5. Enable fullscreen mode (for deployment):
```bash
python scripts/enable_fullscreen.py
```

6. Run the application:
```bash
python central_system/main.py
```

### Faculty Desk Unit

1. Install the Arduino IDE and required libraries:
   - TFT_eSPI
   - NimBLE-Arduino
   - PubSubClient
   - ArduinoJson

2. Configure TFT_eSPI for your display

3. Upload the sketch to your ESP32

## Development

### Project Structure
```
consultease/
├── central_system/           # Raspberry Pi application
│   ├── models/               # Database models
│   ├── views/                # PyQt UI components
│   ├── controllers/          # Application logic
│   ├── services/             # External services (MQTT, RFID)
│   └── utils/                # Utility functions
├── faculty_desk_unit/        # ESP32 firmware
├── scripts/                  # Utility scripts
│   ├── install_squeekboard.sh # Install on-screen keyboard
│   ├── calibrate_touch.sh    # Touchscreen calibration utility
│   └── enable_fullscreen.py  # Enable fullscreen for deployment
├── tests/                    # Test suite
└── docs/                     # Documentation
```

## Touchscreen Features

ConsultEase includes several features to enhance usability on touchscreen devices:

- **Auto-popup keyboard**: Virtual keyboard appears automatically when text fields receive focus
- **Fullscreen mode**: Optimized for touchscreen deployment with full screen utilization
- **Touch calibration**: Tools to ensure accurate touch input recognition
- **Touch-friendly UI**: Larger buttons and input elements optimized for touch interaction

See the user manual and deployment guide in the `docs/` directory for detailed instructions on touchscreen setup and optimization.

## RFID Troubleshooting

If you're experiencing issues with the RFID scanner, the following tools can help:

### Automated RFID Fix (Raspberry Pi)

Run the following command to automatically detect and configure your RFID reader:

```bash
sudo ./scripts/fix_rfid.sh
```

This script will:
1. Detect connected USB devices
2. List potential RFID readers
3. Test the selected device
4. Configure proper permissions
5. Create udev rules for persistent configuration

### Manual RFID Debugging

For more granular control, use the debug_rfid.py tool:

```bash
# List all input devices and identify potential RFID readers
python scripts/debug_rfid.py list

# Monitor a specific input device to see raw events
python scripts/debug_rfid.py monitor <device_number>

# Test RFID reading functionality with a specific device
python scripts/debug_rfid.py test <device_number>
```

### Common RFID Issues

1. **Permission denied errors**: Run `sudo chmod -R a+r /dev/input/` to ensure proper permissions
2. **Device not detected**: Ensure it's properly connected and check `lsusb` output
3. **Wrong device selected**: Use the debug tool to identify the correct device
4. **Thread-related crashes**: The latest update includes thread-safe implementations to prevent crashes

For the target RFID reader with VID:ffff PID:0035, the system should auto-detect it during startup.

## License
[MIT](LICENSE) 