/**
 * ConsultEase - Faculty Desk Unit Configuration
 *
 * This file contains configuration settings for the Faculty Desk Unit.
 * Update these values to match your specific setup.
 */

#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
// ⚠️ SECURITY WARNING: Update these credentials before production deployment!
// These are default values that MUST be changed for security
#define WIFI_SSID "YOUR_WIFI_NETWORK"  // ⚠️ CHANGE THIS: Replace with your actual WiFi network name
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"  // ⚠️ CHANGE THIS: Replace with your actual WiFi password

// MQTT Configuration
#define MQTT_SERVER "192.168.1.100"  // ⚠️ CHANGE THIS: Replace with your MQTT broker IP address
#define MQTT_PORT 1883
#define MQTT_USERNAME "consultease_esp32"  // ⚠️ CHANGE THIS: Use unique MQTT username for security
#define MQTT_PASSWORD "CHANGE_THIS_PASSWORD"  // ⚠️ CHANGE THIS: Use strong password for MQTT authentication

// Faculty Configuration
#define FACULTY_ID 3  // This should match the faculty ID in the database
#define FACULTY_NAME "Jeysibn"  // This should match the faculty name in the database
#define FACULTY_DEPARTMENT "Computer Science"  // This should match the faculty department in the database

// BLE Configuration - Optimized for nRF51822 Beacon Detection
#define BLE_SCAN_INTERVAL 5000  // Scan interval in milliseconds (5 seconds for reliable detection)
#define BLE_SCAN_DURATION 3     // Scan duration in seconds (3 seconds for thorough scanning)
#define BLE_RSSI_THRESHOLD -75  // RSSI threshold for presence detection (-75 dBm for ~5-10 meter range)

// Faculty BLE Beacon Configuration - nRF51822 Beacon
// Each ESP32 unit is configured with only its assigned faculty member's beacon MAC address
// Format: "XX:XX:XX:XX:XX:XX" (case insensitive, colons optional)
//
// SETUP INSTRUCTIONS:
// 1. Power on your nRF51822 beacon
// 2. Upload this firmware with default MAC (00:00:00:00:00:00)
// 3. Check serial output - it will show all detected BLE devices
// 4. Find your beacon's MAC address in the device list
// 5. Update FACULTY_BEACON_MAC below with the actual MAC address
// 6. Re-upload the firmware
//
// IMPORTANT: Replace with actual nRF51822 beacon MAC address
#define FACULTY_BEACON_MAC "00:00:00:00:00:00"  // ⚠️ MUST BE UPDATED WITH REAL BEACON MAC

// Beacon Discovery Mode - Set to true to see all BLE devices (for finding beacon MAC)
#define BEACON_DISCOVERY_MODE false  // Set to true to discover beacon MAC addresses

// MAC Address Detection Settings - Optimized for nRF51822 Beacons
#define MAC_DETECTION_TIMEOUT 30000   // Time in ms to consider faculty absent (30 seconds)
#define MAC_SCAN_ACTIVE true          // Use active scanning (recommended for beacons)
#define MAC_DETECTION_DEBOUNCE 2      // Number of consecutive scans needed for state change

// Display Configuration
#define TFT_ROTATION 1  // 0=Portrait, 1=Landscape, 2=Inverted Portrait, 3=Inverted Landscape

// Color Scheme - National University Philippines
#define NU_BLUE      0x0015      // Dark blue (navy) - Primary color
#define NU_GOLD      0xFE60      // Gold/Yellow - Secondary color
#define NU_DARKBLUE  0x000B      // Darker blue for contrasts
#define NU_LIGHTGOLD 0xF710      // Lighter gold for highlights
#define TFT_WHITE    0xFFFF      // White for text
#define TFT_BLACK    0x0000      // Black for backgrounds

// UI Colors
#define TFT_BG       NU_BLUE         // Background color
#define TFT_TEXT     TFT_WHITE       // Text color
#define TFT_HEADER   NU_DARKBLUE     // Header color
#define TFT_ACCENT   NU_GOLD         // Accent color
#define TFT_HIGHLIGHT NU_LIGHTGOLD   // Highlight color

// MQTT Topics - Standardized format
#define MQTT_TOPIC_STATUS "consultease/faculty/%d/status"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_MAC_STATUS "consultease/faculty/%d/mac_status"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_REQUESTS "consultease/faculty/%d/requests"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_MESSAGES "consultease/faculty/%d/messages"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_NOTIFICATIONS "consultease/system/notifications"

// Legacy MQTT Topics - For backward compatibility
#define MQTT_LEGACY_STATUS "professor/status"
#define MQTT_LEGACY_MESSAGES "professor/messages"

// NTP Time Synchronization Configuration
#define NTP_SERVER_1 "pool.ntp.org"
#define NTP_SERVER_2 "time.nist.gov"
#define NTP_SERVER_3 "time.google.com"
#define TIMEZONE_OFFSET_HOURS 8  // Philippines timezone UTC+8
#define NTP_SYNC_INTERVAL_HOURS 1  // Sync every 1 hour
#define NTP_RETRY_INTERVAL_MINUTES 5  // Retry every 5 minutes if failed
#define NTP_MAX_RETRY_ATTEMPTS 3  // Maximum retry attempts before giving up

// Debug Configuration
#define DEBUG_ENABLED true  // Set to false to disable debug output

#endif // CONFIG_H
