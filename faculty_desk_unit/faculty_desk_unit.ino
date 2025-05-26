#include <WiFi.h>
#include <PubSubClient.h>  // MQTT client
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <SPI.h>
#include <Adafruit_GFX.h>    // Core graphics library
#include <Adafruit_ST7789.h> // Hardware-specific library for ST7789
#include <time.h>
#include "config.h"          // Include configuration file

// Current Date/Time and User
const char* current_date_time = "2025-05-02 09:46:02";
const char* current_user = FACULTY_NAME;

// WiFi credentials
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;

// MQTT Broker settings
const char* mqtt_server = MQTT_SERVER;
const int mqtt_port = MQTT_PORT;
char mqtt_topic_messages[50];
char mqtt_topic_status[50];
char mqtt_topic_legacy_messages[50];
char mqtt_topic_legacy_status[50];
char mqtt_client_id[50];

// BLE UUIDs - Standardized across all components
#define SERVICE_UUID        "91BAD35B-F3CB-4FC1-8603-88D5137892A6"
#define CHARACTERISTIC_UUID "D9473AA3-E6F4-424B-B6E7-A5F94FDDA285"

// Faculty MAC Addresses Definition
const char* FACULTY_MAC_ADDRESSES[MAX_FACULTY_MAC_ADDRESSES] = {
  "11:22:33:44:55:66",  // Dr. John Smith's device
  "AA:BB:CC:DD:EE:FF",  // Dr. Jane Doe's device
  "4F:AF:C2:01:1F:B5",  // Prof. Robert Chen's device
  "12:34:56:78:9A:BC",  // Jeysibn's device (matches FACULTY_ID 3)
  ""                    // Empty slot for additional faculty
};

// BLE Connection Management (Legacy - for backward compatibility)
unsigned long lastBleSignalTime = 0;
unsigned long lastStatusUpdate = 0;
int bleReconnectAttempts = 0;

// MAC Address Detection Variables
BLEScan* pBLEScan = nullptr;
bool facultyPresent = false;
bool oldFacultyPresent = false;
unsigned long lastMacDetectionTime = 0;
unsigned long lastBleScanTime = 0;
int macDetectionCount = 0;
int macAbsenceCount = 0;
String detectedFacultyMac = "";
String lastDetectedMac = "";

// TFT Display pins for ST7789
#define TFT_CS    5
#define TFT_DC    21
#define TFT_RST   22
#define TFT_MOSI  23
#define TFT_SCLK  18

// Initialize the ST7789 display with hardware SPI
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCLK, TFT_RST);

// Time settings
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 0;  // Adjust for your timezone
const int   daylightOffset_sec = 3600;

// Variables
WiFiClient espClient;
PubSubClient mqttClient(espClient);
BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;
char timeStringBuff[50];
char dateStringBuff[50];
String lastMessage = "";
unsigned long lastDisplayUpdate = 0;
unsigned long lastTimeUpdate = 0;

// National University Philippines Color Scheme
#define NU_BLUE      0x0015      // Dark blue (navy) - Primary color
#define NU_GOLD      0xFE60      // Gold/Yellow - Secondary color
#define NU_DARKBLUE  0x000B      // Darker blue for contrasts
#define NU_LIGHTGOLD 0xF710      // Lighter gold for highlights
#define ST77XX_WHITE 0xFFFF      // White for text
#define ST77XX_BLACK 0x0000      // Black for backgrounds

// Colors for the UI
#define COLOR_BACKGROUND     NU_BLUE         // Changed to blue as primary color
#define COLOR_TEXT           ST77XX_WHITE
#define COLOR_HEADER         NU_DARKBLUE
#define COLOR_MESSAGE_BG     NU_BLUE
#define COLOR_STATUS_GOOD    NU_GOLD
#define COLOR_STATUS_WARNING ST77XX_YELLOW
#define COLOR_STATUS_ERROR   ST77XX_RED
#define COLOR_ACCENT         NU_GOLD
#define COLOR_HIGHLIGHT      NU_LIGHTGOLD

// UI Layout constants - No gaps
#define HEADER_HEIGHT 40
#define STATUS_HEIGHT 20
#define MESSAGE_AREA_TOP HEADER_HEIGHT        // No gap after header
#define MESSAGE_TITLE_HEIGHT 30
#define MESSAGE_TEXT_TOP (MESSAGE_AREA_TOP + MESSAGE_TITLE_HEIGHT)

// Gold accent width
#define ACCENT_WIDTH 5

// BLE Server Callbacks with improved connection handling
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      lastBleSignalTime = millis();  // Record the time of connection
      bleReconnectAttempts = 0;      // Reset reconnection attempts

      // Publish to both standardized and legacy topics for backward compatibility
      mqttClient.publish(mqtt_topic_status, "keychain_connected");
      mqttClient.publish(mqtt_topic_legacy_status, "keychain_connected");

      Serial.println("BLE client connected");

      // Log connection details
      Serial.print("Connection time: ");
      Serial.println(lastBleSignalTime);
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;

      // Publish to both standardized and legacy topics for backward compatibility
      mqttClient.publish(mqtt_topic_status, "keychain_disconnected");
      mqttClient.publish(mqtt_topic_legacy_status, "keychain_disconnected");

      Serial.println("BLE client disconnected");
      Serial.print("Disconnection time: ");
      Serial.println(millis());

      // Restart advertising so new clients can connect
      BLEDevice::startAdvertising();

      // Don't reset reconnection attempts here - we'll manage that in the main loop
      // This allows proper tracking of reconnection attempts
    }
};

// Function to process incoming messages and extract content from JSON if needed
String processMessage(String message) {
  // Check if the message is in JSON format (starts with '{')
  if (message.startsWith("{")) {
    Serial.println("Detected JSON message, attempting to extract content");

    // First try to extract the message field
    int messageStart = message.indexOf("\"message\":\"");
    if (messageStart > 0) {
      messageStart += 11; // Length of "message":"
      int messageEnd = message.indexOf("\"", messageStart);
      if (messageEnd > messageStart) {
        String extractedMessage = message.substring(messageStart, messageEnd);
        // Replace escaped quotes and newlines
        extractedMessage.replace("\\\"", "\"");
        extractedMessage.replace("\\n", "\n");
        Serial.print("Extracted message field: ");
        Serial.println(extractedMessage);
        return extractedMessage;
      }
    }

    // If message field not found, try to extract request_message field
    messageStart = message.indexOf("\"request_message\":\"");
    if (messageStart > 0) {
      messageStart += 18; // Length of "request_message":"
      int messageEnd = message.indexOf("\"", messageStart);
      if (messageEnd > messageStart) {
        String extractedMessage = message.substring(messageStart, messageEnd);
        // Replace escaped quotes and newlines
        extractedMessage.replace("\\\"", "\"");
        extractedMessage.replace("\\n", "\n");

        // Try to get student name and course code to format a complete message
        String studentName = "";
        int studentStart = message.indexOf("\"student_name\":\"");
        if (studentStart > 0) {
          studentStart += 16; // Length of "student_name":"
          int studentEnd = message.indexOf("\"", studentStart);
          if (studentEnd > studentStart) {
            studentName = message.substring(studentStart, studentEnd);
          }
        }

        String courseCode = "";
        int courseStart = message.indexOf("\"course_code\":\"");
        if (courseStart > 0) {
          courseStart += 14; // Length of "course_code":"
          int courseEnd = message.indexOf("\"", courseStart);
          if (courseEnd > courseStart) {
            courseCode = message.substring(courseStart, courseEnd);
          }
        }

        // Format a complete message
        String formattedMessage = "";
        if (studentName != "") {
          formattedMessage += "Student: " + studentName + "\n";
        }
        if (courseCode != "") {
          formattedMessage += "Course: " + courseCode + "\n";
        }
        formattedMessage += "Request: " + extractedMessage;

        Serial.print("Formatted message: ");
        Serial.println(formattedMessage);
        return formattedMessage;
      }
    }

    // If no specific message field found, return the whole JSON for debugging
    Serial.println("No message field found in JSON, displaying raw JSON");
    return message;
  }

  // If not JSON, return the original message
  return message;
}

// MAC Address Detection Functions
String normalizeMacAddress(String mac) {
  // Convert MAC address to uppercase and ensure consistent format
  mac.toUpperCase();
  mac.replace("-", ":");
  return mac;
}

bool isFacultyMacAddress(String mac) {
  // Normalize the detected MAC address
  String normalizedMac = normalizeMacAddress(mac);

  // Check against known faculty MAC addresses
  for (int i = 0; i < MAX_FACULTY_MAC_ADDRESSES; i++) {
    if (strlen(FACULTY_MAC_ADDRESSES[i]) > 0) {
      String knownMac = normalizeMacAddress(String(FACULTY_MAC_ADDRESSES[i]));
      if (normalizedMac.equals(knownMac)) {
        Serial.print("Matched faculty MAC: ");
        Serial.print(normalizedMac);
        Serial.print(" (Known as: ");
        Serial.print(knownMac);
        Serial.println(")");
        return true;
      }
    }
  }
  return false;
}

// BLE Scan Callback Class
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      String deviceMac = advertisedDevice.getAddress().toString().c_str();
      int rssi = advertisedDevice.getRSSI();

      // Check if this is a faculty member's device
      if (isFacultyMacAddress(deviceMac) && rssi > BLE_RSSI_THRESHOLD) {
        Serial.print("Faculty device detected: ");
        Serial.print(deviceMac);
        Serial.print(" RSSI: ");
        Serial.println(rssi);

        // Update detection variables
        detectedFacultyMac = deviceMac;
        lastMacDetectionTime = millis();
        macDetectionCount++;
        macAbsenceCount = 0; // Reset absence counter
      }
    }
};

void initializeBLEScanner() {
  Serial.println("Initializing BLE Scanner for MAC address detection...");

  // Initialize BLE
  BLEDevice::init("ConsultEase-Faculty-Scanner");

  // Create BLE Scanner
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(MAC_SCAN_ACTIVE);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);

  Serial.println("BLE Scanner initialized");
  displaySystemStatus("BLE Scanner ready");
}

void performBLEScan() {
  if (pBLEScan == nullptr) {
    Serial.println("BLE Scanner not initialized");
    return;
  }

  unsigned long currentTime = millis();

  // Only scan at specified intervals
  if (currentTime - lastBleScanTime < BLE_SCAN_INTERVAL) {
    return;
  }

  lastBleScanTime = currentTime;

  Serial.println("Starting BLE scan for faculty devices...");
  displaySystemStatus("Scanning for faculty...");

  // Clear previous detection for this scan
  String previousDetectedMac = detectedFacultyMac;
  detectedFacultyMac = "";

  // Perform scan
  BLEScanResults foundDevices = pBLEScan->start(BLE_SCAN_DURATION, false);

  // Check if we detected any faculty member
  bool currentScanDetected = (detectedFacultyMac.length() > 0);

  if (currentScanDetected) {
    Serial.print("Faculty detected in scan: ");
    Serial.println(detectedFacultyMac);
  } else {
    Serial.println("No faculty devices detected in scan");
    macAbsenceCount++;
  }

  // Clear scan results to free memory
  pBLEScan->clearResults();

  // Update faculty presence based on debouncing logic
  updateFacultyPresenceStatus();

  Serial.print("Scan complete. Found ");
  Serial.print(foundDevices.getCount());
  Serial.println(" devices total");
}

void updateFacultyPresenceStatus() {
  bool newFacultyPresent = false;

  // Determine presence based on recent detections and debouncing
  if (macDetectionCount >= MAC_DETECTION_DEBOUNCE) {
    // Faculty has been consistently detected
    newFacultyPresent = true;
  } else if (macAbsenceCount >= MAC_DETECTION_DEBOUNCE) {
    // Faculty has been consistently absent
    newFacultyPresent = false;
  } else {
    // Not enough consistent readings, maintain current state
    newFacultyPresent = facultyPresent;
  }

  // Check for timeout (faculty left without proper detection)
  unsigned long currentTime = millis();
  if (facultyPresent && (currentTime - lastMacDetectionTime > MAC_DETECTION_TIMEOUT)) {
    Serial.println("Faculty presence timeout - marking as absent");
    newFacultyPresent = false;
    macAbsenceCount = MAC_DETECTION_DEBOUNCE; // Force absence state
  }

  // Update status if changed
  if (newFacultyPresent != facultyPresent) {
    oldFacultyPresent = facultyPresent;
    facultyPresent = newFacultyPresent;

    // Reset counters when state changes
    macDetectionCount = 0;
    macAbsenceCount = 0;

    // Update last detected MAC for status reporting
    if (facultyPresent) {
      lastDetectedMac = detectedFacultyMac;
    }

    Serial.print("Faculty presence changed: ");
    Serial.println(facultyPresent ? "PRESENT" : "ABSENT");

    // Publish status change via MQTT
    publishFacultyStatus();
  }
}

void publishFacultyStatus() {
  if (!mqttClient.connected()) {
    Serial.println("MQTT not connected, cannot publish status");
    return;
  }

  const char* status_message;
  String detailed_status;

  if (facultyPresent) {
    status_message = "faculty_present";
    detailed_status = "Faculty detected via MAC: " + lastDetectedMac;

    // Also send legacy format for backward compatibility
    mqttClient.publish(mqtt_topic_status, "keychain_connected");
    mqttClient.publish(mqtt_topic_legacy_status, "keychain_connected");

    Serial.println("Published faculty present status");
    displaySystemStatus("Faculty Present");
  } else {
    status_message = "faculty_absent";
    detailed_status = "No faculty MAC detected";

    // Also send legacy format for backward compatibility
    mqttClient.publish(mqtt_topic_status, "keychain_disconnected");
    mqttClient.publish(mqtt_topic_legacy_status, "keychain_disconnected");

    Serial.println("Published faculty absent status");
    displaySystemStatus("Faculty Absent");
  }

  // Publish detailed status with MAC address information
  String statusTopic = "consultease/faculty/" + String(FACULTY_ID) + "/mac_status";
  String statusPayload = "{\"status\":\"" + String(status_message) + "\",\"mac\":\"" + lastDetectedMac + "\",\"timestamp\":" + String(millis()) + "}";

  mqttClient.publish(statusTopic.c_str(), statusPayload.c_str());

  Serial.print("Published detailed status: ");
  Serial.println(statusPayload);
}

// Function to draw the continuous gold accent bar
void drawGoldAccent() {
  // Draw gold accent that spans the entire height except status bar
  tft.fillRect(0, 0, ACCENT_WIDTH, tft.height() - STATUS_HEIGHT, COLOR_ACCENT);
}

// Centralized UI update function that preserves the gold accent
void updateUIArea(int area, const String &message = "") {
  // Area types:
  // 0 = Full message area
  // 1 = Message title area only
  // 2 = Message content area only
  // 3 = Status bar only

  switch (area) {
    case 0: // Full message area
      // Clear the message area but preserve gold accent
      tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP,
                  tft.width() - ACCENT_WIDTH,
                  tft.height() - MESSAGE_AREA_TOP - STATUS_HEIGHT,
                  COLOR_MESSAGE_BG);

      // Ensure gold accent is intact
      drawGoldAccent();

      // If message provided, display it
      if (message.length() > 0) {
        tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
        tft.setTextSize(2);
        tft.setTextColor(NU_GOLD);
        tft.println(message);
      }
      break;

    case 1: // Message title area only
      // Clear just the title area
      tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP,
                  tft.width() - ACCENT_WIDTH,
                  MESSAGE_TITLE_HEIGHT,
                  COLOR_MESSAGE_BG);

      // Ensure gold accent is intact
      drawGoldAccent();

      // If message provided, display it as title
      if (message.length() > 0) {
        tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
        tft.setTextSize(2);
        tft.setTextColor(NU_GOLD);
        tft.println(message);
      }
      break;

    case 2: // Message content area only
      // Clear just the content area below title
      tft.fillRect(ACCENT_WIDTH, MESSAGE_TEXT_TOP,
                  tft.width() - ACCENT_WIDTH,
                  tft.height() - MESSAGE_TEXT_TOP - STATUS_HEIGHT,
                  COLOR_MESSAGE_BG);

      // Ensure gold accent is intact
      drawGoldAccent();
      break;

    case 3: // Status bar only
      // Update status bar
      displaySystemStatus(message);
      break;
  }
}

// Function to test the full display
void testScreen() {
  // Test pattern to verify the display is working properly
  tft.fillScreen(NU_BLUE);
  delay(500);

  // Draw National University Philippines colors for test
  int sectionHeight = tft.height() / 3;

  // Draw sections with no gaps
  tft.fillRect(0, 0, tft.width(), sectionHeight, NU_DARKBLUE);
  tft.fillRect(0, sectionHeight, tft.width(), sectionHeight, NU_BLUE);
  tft.fillRect(0, 2*sectionHeight, tft.width(), sectionHeight, NU_GOLD);

  // Add continuous gold accent line at left
  drawGoldAccent();

  // Display text
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);

  tft.setCursor(ACCENT_WIDTH + 5, 10);
  tft.println("National University");

  tft.setCursor(ACCENT_WIDTH + 5, sectionHeight + 10);
  tft.println("Philippines");

  tft.setTextColor(NU_DARKBLUE);
  tft.setCursor(ACCENT_WIDTH + 5, 2*sectionHeight + 10);
  tft.println("Professor's Desk Unit");

  delay(3000);
  tft.fillScreen(NU_BLUE);
}

// Function to draw the header with time and date
void updateTimeDisplay() {
  struct tm timeinfo;

  // Clear only the header area, preserving the gold accent
  tft.fillRect(ACCENT_WIDTH, 0, tft.width() - ACCENT_WIDTH, HEADER_HEIGHT, COLOR_HEADER);

  // Get the current time
  if(!getLocalTime(&timeinfo)){
    Serial.println("Failed to obtain time");

    // Use provided time if NTP fails
    // Parse the date and time from current_date_time string
    String dateTime = String(current_date_time);
    String date = dateTime.substring(0, 10);  // "2025-05-02"
    String time = dateTime.substring(11);     // "09:46:02"

    // Draw time on left
    tft.setTextColor(COLOR_TEXT);
    tft.setTextSize(2);
    tft.setCursor(ACCENT_WIDTH + 5, 10);
    tft.print(time);

    // Draw date on right
    int16_t x1, y1;
    uint16_t w, h;
    tft.getTextBounds(date, 0, 0, &x1, &y1, &w, &h);
    tft.setCursor(tft.width() - w - 10, 10);
    tft.print(date);

    // Ensure gold accent is intact
    drawGoldAccent();
    return;
  }

  // Format time (HH:MM:SS)
  strftime(timeStringBuff, sizeof(timeStringBuff), "%H:%M:%S", &timeinfo);

  // Format date (YYYY-MM-DD)
  strftime(dateStringBuff, sizeof(dateStringBuff), "%Y-%m-%d", &timeinfo);

  // Draw time on left
  tft.setTextColor(COLOR_TEXT);
  tft.setTextSize(2);
  tft.setCursor(ACCENT_WIDTH + 5, 10);
  tft.print(timeStringBuff);

  // Draw date on right
  int16_t x1, y1;
  uint16_t w, h;
  tft.getTextBounds(dateStringBuff, 0, 0, &x1, &y1, &w, &h);
  tft.setCursor(tft.width() - w - 10, 10);
  tft.print(dateStringBuff);

  // Ensure gold accent is intact
  drawGoldAccent();
}

// Function to display a new message
void displayMessage(String message) {
  // Use centralized UI update function to clear the full message area
  updateUIArea(0);

  // Display "New Message:" title with gold accent
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 5);
  tft.setTextColor(COLOR_ACCENT);  // Gold color for title
  tft.setTextSize(2);
  tft.println("New Message:");

  // Draw a gold divider line right after the title
  tft.drawFastHLine(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + MESSAGE_TITLE_HEIGHT - 5, tft.width() - ACCENT_WIDTH - 10, COLOR_ACCENT);

  // Display message text with word wrapping
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_TEXT_TOP);
  tft.setTextColor(COLOR_TEXT);  // White text for message
  tft.setTextSize(2);

  // Handle long messages with line wrapping
  int16_t x1, y1;
  uint16_t w, h;
  int maxWidth = tft.width() - ACCENT_WIDTH - 10;
  String line = "";
  int yPos = MESSAGE_TEXT_TOP;

  for (int i = 0; i < message.length(); i++) {
    char c = message.charAt(i);
    line += c;

    tft.getTextBounds(line, 0, 0, &x1, &y1, &w, &h);

    if (w > maxWidth || c == '\n') {
      // Remove the last character if it was due to width
      if (w > maxWidth && c != '\n')
        line = line.substring(0, line.length() - 1);

      tft.setCursor(ACCENT_WIDTH + 5, yPos);
      tft.println(line);

      yPos += h + 2;  // Reduced spacing for more compact layout
      line = (w > maxWidth && c != '\n') ? String(c) : "";
    }
  }

  // Print any remaining text
  if (line.length() > 0) {
    tft.setCursor(ACCENT_WIDTH + 5, yPos);
    tft.println(line);
  }

  lastMessage = message;
}

// Show system status on display
void displaySystemStatus(String status) {
  // Clear the status area at the bottom of the screen
  tft.fillRect(0, tft.height() - STATUS_HEIGHT, tft.width(), STATUS_HEIGHT, NU_DARKBLUE);

  // Display the status text
  tft.setCursor(ACCENT_WIDTH + 5, tft.height() - STATUS_HEIGHT + 5);
  tft.setTextColor(COLOR_STATUS_GOOD);
  tft.setTextSize(1);
  tft.println(status);

  // Draw a gold line above status bar
  tft.drawFastHLine(0, tft.height() - STATUS_HEIGHT, tft.width(), COLOR_ACCENT);
}

// MQTT callback with improved topic handling
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");

  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println(message);

  // Enhanced debug output
  Serial.println("Message details:");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Length: ");
  Serial.println(length);
  Serial.print("Content: ");
  Serial.println(message);

  // Check if this is a system ping message (for keeping connection alive)
  if (strcmp(topic, MQTT_TOPIC_NOTIFICATIONS) == 0 && message.indexOf("ping") >= 0) {
    Serial.println("Received system ping, no need to display");
    return;
  }

  // Process the message based on format
  message = processMessage(message);

  // Display the message on TFT with visual notification
  displayMessage(message);
  displaySystemStatus("New message received");

  // Flash the screen briefly to draw attention to the new message
  for (int i = 0; i < 3; i++) {
    // Flash the header area
    tft.fillRect(ACCENT_WIDTH, 0, tft.width() - ACCENT_WIDTH, HEADER_HEIGHT, COLOR_ACCENT);
    delay(100);
    tft.fillRect(ACCENT_WIDTH, 0, tft.width() - ACCENT_WIDTH, HEADER_HEIGHT, COLOR_HEADER);
    delay(100);
  }

  // Restore the time display
  updateTimeDisplay();

  // Also forward to connected BLE device if any
  if (deviceConnected) {
    pCharacteristic->setValue(message.c_str());
    pCharacteristic->notify();

    // Update the last BLE signal time
    lastBleSignalTime = millis();
  }
}

// Draw the main UI framework - truly seamless design
void drawUIFramework() {
  // Fill entire screen with the NU blue color
  tft.fillScreen(COLOR_BACKGROUND);

  // Draw the header bar with darker blue - no gaps
  tft.fillRect(ACCENT_WIDTH, 0, tft.width() - ACCENT_WIDTH, HEADER_HEIGHT, COLOR_HEADER);

  // Draw status bar area - seamless with main area
  tft.fillRect(0, tft.height() - STATUS_HEIGHT, tft.width(), STATUS_HEIGHT, NU_DARKBLUE);

  // Add thin gold accent line above status bar
  tft.drawFastHLine(0, tft.height() - STATUS_HEIGHT, tft.width(), COLOR_ACCENT);

  // Draw continuous gold accent at left
  drawGoldAccent();
}

void setup_wifi() {
  // Clear the main content area but preserve the gold accent bar
  tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP, tft.width() - ACCENT_WIDTH, tft.height() - MESSAGE_AREA_TOP - STATUS_HEIGHT, COLOR_BACKGROUND);

  // Ensure gold accent is intact
  drawGoldAccent();

  // Display connecting message
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
  tft.setTextColor(COLOR_TEXT);
  tft.setTextSize(2);
  tft.println("Connecting to WiFi");

  // Add the SSID right beneath
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 40);
  tft.setTextSize(1);
  tft.println(ssid);

  // Connect to WiFi
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  // Animated connecting indicator with National University colors
  int dots = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");

    // Clear dot area but preserve gold accent
    tft.fillRect(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 60, tft.width() - ACCENT_WIDTH - 10, 20, COLOR_BACKGROUND);

    // Update dots animation with alternating colors
    tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 60);
    tft.setTextColor(COLOR_TEXT);
    tft.print("Connecting");

    for (int i = 0; i < 6; i++) {
      if (i < dots) {
        // Alternate between blue and gold dots
        tft.setTextColor((i % 2 == 0) ? NU_GOLD : NU_LIGHTGOLD);
        tft.print(".");
      } else {
        tft.print(" ");
      }
    }

    dots = (dots + 1) % 7;
  }

  // Connected - display connection details
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // Clear the connecting message and show success - but preserve gold accent bar
  tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP, tft.width() - ACCENT_WIDTH, tft.height() - MESSAGE_AREA_TOP - STATUS_HEIGHT, COLOR_BACKGROUND);

  // Ensure gold accent is intact
  drawGoldAccent();

  // Show connected message
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
  tft.setTextSize(2);
  tft.setTextColor(NU_GOLD);
  tft.println("WiFi Connected");

  // Show network details
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 50);
  tft.setTextSize(1);
  tft.setTextColor(COLOR_TEXT);
  tft.print("SSID: ");
  tft.println(ssid);

  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 70);
  tft.print("IP: ");
  tft.println(WiFi.localIP().toString());

  // Update status bar
  displaySystemStatus("WiFi connected successfully");

  // Give time to read the info
  delay(2000);
}

void reconnect() {
  // Loop until we're reconnected to MQTT broker
  int attempts = 0;

  while (!mqttClient.connected() && attempts < 5) {
    Serial.print("Attempting MQTT connection...");
    displaySystemStatus("Connecting to MQTT...");

    // Create a client ID using the user's login
    String clientId = mqtt_client_id;
    clientId += String(random(0xffff), HEX);

    // Attempt to connect
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
      displaySystemStatus("MQTT connected");
      // Subscribe to message topics (both standardized and legacy topics)
      mqttClient.subscribe(mqtt_topic_messages);
      mqttClient.subscribe(mqtt_topic_legacy_messages);

      // Also subscribe to system notifications for ping messages
      mqttClient.subscribe(MQTT_TOPIC_NOTIFICATIONS);

      Serial.println("Subscribed to topics:");
      Serial.println(mqtt_topic_messages);
      Serial.println(mqtt_topic_legacy_messages);
      Serial.println(MQTT_TOPIC_NOTIFICATIONS);

      // Display a brief confirmation in message area - preserve gold accent
      tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP, tft.width() - ACCENT_WIDTH, 40, COLOR_MESSAGE_BG);

      // Ensure gold accent is intact
      drawGoldAccent();

      tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
      tft.setTextSize(2);
      tft.setTextColor(COLOR_ACCENT);
      tft.println("MQTT Connected");
      delay(1000);

      // Clear message but preserve gold accent
      tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP, tft.width() - ACCENT_WIDTH, 40, COLOR_MESSAGE_BG);
      drawGoldAccent();
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      displaySystemStatus("MQTT connection failed. Retrying...");
      delay(5000);
      attempts++;
    }
  }

  if (!mqttClient.connected()) {
    displaySystemStatus("Failed to connect to MQTT after multiple attempts");
  }
}

void drawNULogo(int centerX, int centerY, int size) {
  // Draw a simplified NU logo
  int circleSize = size;
  int innerSize1 = size * 0.8;
  int innerSize2 = size * 0.6;
  int innerSize3 = size * 0.4;

  // Outer gold circle
  tft.fillCircle(centerX, centerY, circleSize, NU_GOLD);

  // Inner blue circle
  tft.fillCircle(centerX, centerY, innerSize1, NU_DARKBLUE);

  // White middle ring
  tft.fillCircle(centerX, centerY, innerSize2, ST77XX_WHITE);

  // Blue inner circle
  tft.fillCircle(centerX, centerY, innerSize3, NU_BLUE);

  // Add "NU" text in the center
  tft.setTextColor(NU_GOLD);
  tft.setTextSize(1);

  // Center the text in the logo
  tft.setCursor(centerX - 5, centerY - 3);
  tft.print("NU");
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting National University Philippines Desk Unit");
  Serial.print("Current user: ");
  Serial.println(current_user);
  Serial.print("Current time: ");
  Serial.println(current_date_time);

  // Initialize MQTT topics with faculty ID - both standardized and legacy
  sprintf(mqtt_topic_messages, MQTT_TOPIC_REQUESTS, FACULTY_ID);
  sprintf(mqtt_topic_status, MQTT_TOPIC_STATUS, FACULTY_ID);
  strcpy(mqtt_topic_legacy_messages, MQTT_LEGACY_MESSAGES);
  strcpy(mqtt_topic_legacy_status, MQTT_LEGACY_STATUS);
  sprintf(mqtt_client_id, "DeskUnit_%s", FACULTY_NAME);

  Serial.println("MQTT topics initialized:");
  Serial.print("Standard messages topic: ");
  Serial.println(mqtt_topic_messages);
  Serial.print("Standard status topic: ");
  Serial.println(mqtt_topic_status);
  Serial.print("Legacy messages topic: ");
  Serial.println(mqtt_topic_legacy_messages);
  Serial.print("Legacy status topic: ");
  Serial.println(mqtt_topic_legacy_status);
  Serial.print("Client ID: ");
  Serial.println(mqtt_client_id);

  // Initialize SPI communication
  SPI.begin();

  // Initialize ST7789 display (240x320)
  tft.init(240, 320); // Initialize the display with its dimensions

  Serial.println("Display initialized");

  // Set rotation for landscape orientation
  tft.setRotation(1);

  // Run screen test to check if display is working correctly
  testScreen();

  // Setup the basic UI framework - truly seamless design
  drawUIFramework();

  // Show current time/date in header
  updateTimeDisplay();

  // Show initial status
  displaySystemStatus("Initializing system...");

  // Display welcome message with NU branding - seamlessly
  int centerX = tft.width() / 2;
  int logoY = MESSAGE_AREA_TOP + 60;

  // Ensure gold accent is intact
  drawGoldAccent();

  // Draw NU logo
  drawNULogo(centerX, logoY, 35);

  // Draw welcome text
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
  tft.setTextColor(NU_GOLD);
  tft.setTextSize(2);
  tft.println("Welcome, " + String(current_user));

  tft.setCursor(ACCENT_WIDTH + 5, logoY + 50);
  tft.setTextSize(1.5);
  tft.setTextColor(ST77XX_WHITE);
  tft.println("National University");

  tft.setCursor(ACCENT_WIDTH + 5, logoY + 70);
  tft.println("Professor's Desk Unit");

  tft.setCursor(ACCENT_WIDTH + 5, logoY + 100);
  tft.setTextColor(NU_GOLD);
  tft.println("System Initializing...");

  delay(2000);

  // Set up WiFi - this will clear the welcome message but preserve gold accent
  setup_wifi();

  // Configure time
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);

  // Initialize MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback);

  // Initialize BLE Scanner for MAC address detection
  if (BLE_DETECTION_MODE_MAC_ADDRESS) {
    Serial.println("Initializing MAC address-based faculty detection...");
    initializeBLEScanner();

    // Initialize MAC detection variables
    facultyPresent = false;
    oldFacultyPresent = false;
    lastMacDetectionTime = 0;
    lastBleScanTime = 0;
    macDetectionCount = 0;
    macAbsenceCount = 0;
    detectedFacultyMac = "";
    lastDetectedMac = "";

    // Publish initial status to MQTT (both standardized and legacy topics)
    mqttClient.publish(mqtt_topic_status, "keychain_disconnected");
    mqttClient.publish(mqtt_topic_legacy_status, "keychain_disconnected");
    Serial.println("MAC address detection ready, scanning for faculty devices");
    displaySystemStatus("Scanning for faculty...");
  } else {
    // Legacy BLE server mode (for backward compatibility)
    Serial.println("Using legacy BLE server mode...");

    // Create the BLE Device with faculty name
    char ble_device_name[50];
    sprintf(ble_device_name, "ProfDeskUnit_%s", FACULTY_NAME);
    BLEDevice::init(ble_device_name);
    Serial.print("BLE Device initialized: ");
    Serial.println(ble_device_name);

    // Create the BLE Server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create the BLE Service
    BLEService *pService = pServer->createService(SERVICE_UUID);

    // Create a BLE Characteristic
    pCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID,
                        BLECharacteristic::PROPERTY_READ   |
                        BLECharacteristic::PROPERTY_WRITE  |
                        BLECharacteristic::PROPERTY_NOTIFY |
                        BLECharacteristic::PROPERTY_INDICATE
                      );

    // Create a BLE Descriptor
    pCharacteristic->addDescriptor(new BLE2902());

    // Start the service
    pService->start();

    // Start advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(false);
    pAdvertising->setMinPreferred(0x0);
    BLEDevice::startAdvertising();

    Serial.println("BLE Server ready!");
    displaySystemStatus("BLE Server ready");

    // Initialize connection status
    deviceConnected = false;
    oldDeviceConnected = false;
    lastBleSignalTime = millis();  // Initialize the last BLE signal time

    // Publish initial status to MQTT (both standardized and legacy topics)
    mqttClient.publish(mqtt_topic_status, "keychain_disconnected");
    mqttClient.publish(mqtt_topic_legacy_status, "keychain_disconnected");
    Serial.println("BLE server ready, waiting for keychain connection");
    displaySystemStatus("Waiting for keychain...");
  }

  // Update time display
  updateTimeDisplay();

  // Display ready message - seamless design (preserve gold accent)
  tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP, tft.width() - ACCENT_WIDTH, tft.height() - MESSAGE_AREA_TOP - STATUS_HEIGHT, COLOR_MESSAGE_BG);

  // Ensure gold accent is maintained
  drawGoldAccent();

  // Redraw NU logo
  drawNULogo(centerX, logoY, 35);

  // Text
  tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
  tft.setTextColor(NU_GOLD);
  tft.setTextSize(2);
  tft.println("System Ready");

  tft.setCursor(ACCENT_WIDTH + 5, logoY + 50);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(1.5);
  tft.println("National University");

  tft.setCursor(ACCENT_WIDTH + 5, logoY + 70);
  tft.println("Professor's Desk Unit");

  tft.setCursor(ACCENT_WIDTH + 5, logoY + 100);
  tft.setTextColor(NU_LIGHTGOLD);
  tft.println("Waiting for messages...");
}

void loop() {
  // MQTT connection management with improved reliability
  static unsigned long lastMqttCheckTime = 0;
  unsigned long currentMillis = millis();

  // Check MQTT connection every 5 seconds
  if (!mqttClient.connected() || (currentMillis - lastMqttCheckTime > 5000)) {
    lastMqttCheckTime = currentMillis;

    if (!mqttClient.connected()) {
      Serial.println("MQTT disconnected, attempting to reconnect...");
      reconnect();
    } else {
      // Periodically check if we're still receiving messages by pinging the broker
      mqttClient.publish(MQTT_TOPIC_NOTIFICATIONS, "ping");
    }
  }

  // Process MQTT messages
  mqttClient.loop();

  // MAC Address Detection (if enabled)
  if (BLE_DETECTION_MODE_MAC_ADDRESS) {
    // Perform BLE scanning for faculty MAC addresses
    performBLEScan();
  } else {
    // Legacy BLE connection management with improved reliability
    // Handle BLE connection state changes
    if (deviceConnected && !oldDeviceConnected) {
    // Just connected
    oldDeviceConnected = deviceConnected;
    Serial.println("BLE client connected - updating status");
    mqttClient.publish(mqtt_topic_status, "keychain_connected");
    mqttClient.publish(mqtt_topic_legacy_status, "keychain_connected");
    lastStatusUpdate = currentMillis;

    // Show a notification about keychain connection using centralized UI function
    updateUIArea(3, "Keychain connected!");
    updateUIArea(1, "Keychain Connected");
    delay(2000);

    // If we have a last message, redisplay it, otherwise clear
    if (lastMessage.length() > 0) {
      displayMessage(lastMessage);
    } else {
      tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP, tft.width() - ACCENT_WIDTH, tft.height() - MESSAGE_AREA_TOP - STATUS_HEIGHT, COLOR_MESSAGE_BG);
      drawGoldAccent();
    }
  }

  if (!deviceConnected && oldDeviceConnected) {
    // Just disconnected
    oldDeviceConnected = deviceConnected;
    Serial.println("BLE client disconnected - updating status");

    // Always update status when BLE disconnects
    mqttClient.publish(mqtt_topic_status, "keychain_disconnected");
    mqttClient.publish(mqtt_topic_legacy_status, "keychain_disconnected");

    // Show a notification about keychain disconnection using centralized UI function
    updateUIArea(3, "Keychain disconnected!");
    updateUIArea(1, "Keychain Disconnected");

    // Use error color for the disconnection message
    tft.setCursor(ACCENT_WIDTH + 5, MESSAGE_AREA_TOP + 10);
    tft.setTextSize(2);
    tft.setTextColor(COLOR_STATUS_ERROR);
    tft.println("Keychain Disconnected");
    delay(2000);

    // If we have a last message, redisplay it, otherwise clear
    if (lastMessage.length() > 0) {
      displayMessage(lastMessage);
    } else {
      tft.fillRect(ACCENT_WIDTH, MESSAGE_AREA_TOP, tft.width() - ACCENT_WIDTH, tft.height() - MESSAGE_AREA_TOP - STATUS_HEIGHT, COLOR_MESSAGE_BG);
      drawGoldAccent();
    }

    // Restart advertising so new clients can connect
    BLEDevice::startAdvertising();
  }

  // BLE reconnection logic - improved with better handling
  if (!deviceConnected) {
    // Check if we've lost connection for longer than the timeout
    if (currentMillis - lastBleSignalTime > BLE_CONNECTION_TIMEOUT) {
      // Only attempt reconnection if we haven't exceeded the maximum attempts
      if (bleReconnectAttempts < BLE_RECONNECT_ATTEMPTS) {
        Serial.print("BLE connection timed out. Attempting reconnection (");
        Serial.print(bleReconnectAttempts + 1);
        Serial.print(" of ");
        Serial.print(BLE_RECONNECT_ATTEMPTS);
        Serial.println(")");

        // Restart advertising
        BLEDevice::startAdvertising();

        // Increment reconnection attempts
        bleReconnectAttempts++;

        // Update last signal time to prevent rapid reconnection attempts
        lastBleSignalTime = currentMillis;

        // Display reconnection attempt
        displaySystemStatus("Attempting BLE reconnection...");
      } else if (bleReconnectAttempts == BLE_RECONNECT_ATTEMPTS) {
        // We've reached the maximum number of attempts
        Serial.println("Maximum BLE reconnection attempts reached");

        // Display status message
        displaySystemStatus("BLE reconnection failed");

        // Increment to prevent repeated messages
        bleReconnectAttempts++;

        // Reset the BLE device if we've reached max attempts
        // This can help recover from some BLE stack issues
        if (bleReconnectAttempts > BLE_RECONNECT_ATTEMPTS + 5) {
          Serial.println("Resetting BLE device after multiple failed reconnection attempts");
          BLEDevice::deinit(true);  // Full deinit
          delay(1000);

          // Reinitialize BLE
          char ble_device_name[50];
          sprintf(ble_device_name, "ProfDeskUnit_%s", FACULTY_NAME);
          BLEDevice::init(ble_device_name);

          // Recreate server and service
          pServer = BLEDevice::createServer();
          pServer->setCallbacks(new MyServerCallbacks());
          BLEService *pService = pServer->createService(SERVICE_UUID);
          pCharacteristic = pService->createCharacteristic(
                            CHARACTERISTIC_UUID,
                            BLECharacteristic::PROPERTY_READ   |
                            BLECharacteristic::PROPERTY_WRITE  |
                            BLECharacteristic::PROPERTY_NOTIFY |
                            BLECharacteristic::PROPERTY_INDICATE
                          );
          pCharacteristic->addDescriptor(new BLE2902());
          pService->start();
          BLEDevice::startAdvertising();

          // Reset counters
          bleReconnectAttempts = 0;
          lastBleSignalTime = currentMillis;
          displaySystemStatus("BLE device reset completed");
        }
      }
    }
  } else {
    // Reset reconnection attempts when connected
    bleReconnectAttempts = 0;
  }

  // Periodic status updates with improved efficiency
  if (currentMillis - lastStatusUpdate > 300000) { // Every 5 minutes
    lastStatusUpdate = currentMillis;

    // Determine status message based on connection state
    const char* status_message;

    if (deviceConnected) {
      status_message = "keychain_connected";
      Serial.println("Periodic BLE connected status update sent");
    } else {
      status_message = "keychain_disconnected";
      Serial.println("Periodic BLE disconnected status update sent");
    }

    // Send to both standardized and legacy topics
    mqttClient.publish(mqtt_topic_status, status_message);
    mqttClient.publish(mqtt_topic_legacy_status, status_message);

    // Also update the display status
    if (deviceConnected) {
      displaySystemStatus("BLE connected");
    } else {
      displaySystemStatus("BLE disconnected");
    }
  } // End of legacy BLE mode else block

  // Update time display every minute
  if (currentMillis - lastTimeUpdate > 60000) {
    lastTimeUpdate = currentMillis;
    updateTimeDisplay();
  }
}