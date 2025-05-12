/**
 * ConsultEase - Faculty BLE Beacon Configuration
 * 
 * This file contains configuration settings for the Faculty BLE Beacon.
 * Update these values to match your specific setup.
 */

#ifndef CONFIG_H
#define CONFIG_H

// Faculty Configuration
#define FACULTY_ID 1  // This should match the faculty ID in the database
#define FACULTY_NAME "Dr. John Smith"  // This should match the faculty name in the database

// BLE Configuration
#define DEVICE_NAME "ConsultEase-Faculty"  // BLE device name
#define ADVERTISE_INTERVAL 200  // Advertising interval in ms (lower values = more frequent advertising, but more power consumption)

// Battery Configuration
#define BATTERY_PIN 34  // Analog pin for battery monitoring (set to -1 to disable)
#define BATTERY_MIN_VOLTAGE 3.2  // Minimum battery voltage
#define BATTERY_MAX_VOLTAGE 4.2  // Maximum battery voltage
#define BATTERY_DIVIDER_RATIO 2.0  // Voltage divider ratio (if used)
#define ADC_RESOLUTION 4095  // ADC resolution (12-bit for ESP32)
#define ADC_REFERENCE 3.3  // ADC reference voltage

// LED Configuration
#define LED_PIN 2  // Built-in LED pin (for status indication)

// UUID Configuration
#define SERVICE_UUID "91BAD35B-F3CB-4FC1-8603-88D5137892A6"  // UUID for ConsultEase faculty identification
#define CHARACTERISTIC_UUID "D9473AA3-E6F4-424B-B6E7-A5F94FDDA285"  // UUID for ConsultEase faculty characteristic

// Debug Configuration
#define DEBUG_ENABLED true  // Set to false to disable debug output

#endif // CONFIG_H
