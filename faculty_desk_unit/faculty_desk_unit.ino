/**
 * ConsultEase - Faculty Desk Unit
 * 
 * This firmware runs on an ESP32 and provides:
 * 1. BLE beacon detection for faculty presence
 * 2. TFT display for consultation requests
 * 3. MQTT communication with the central system
 * 
 * Hardware:
 * - ESP32 Dev Board
 * - 2.4" TFT Display (ST7789)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>
#include <NimBLEDevice.h>
#include <Preferences.h>

// ===== Configuration =====
// WiFi Settings
const char* WIFI_SSID = "YourWiFiSSID";      // WiFi network name
const char* WIFI_PASSWORD = "YourWiFiPass";  // WiFi password

// MQTT Settings
const char* MQTT_SERVER = "192.168.1.100";   // MQTT broker address (Raspberry Pi)
const int MQTT_PORT = 1883;                  // MQTT broker port
const char* MQTT_CLIENT_ID = "faculty_desk"; // MQTT client ID
const char* MQTT_USERNAME = "";              // MQTT username (if required)
const char* MQTT_PASSWORD = "";              // MQTT password (if required)

// BLE Settings
const char* TARGET_BLE_ADDRESS = "11:22:33:44:55:66"; // Faculty BLE beacon MAC address
const int BLE_SCAN_INTERVAL = 5;             // Seconds between scans
const int BLE_SCAN_DURATION = 3;             // Scan duration in seconds
const int BLE_RSSI_THRESHOLD = -80;          // RSSI threshold for presence detection (-80 dBm)
const int BLE_TIMEOUT = 15;                  // Seconds before marking faculty as away

// Faculty Settings
const int FACULTY_ID = 1;                    // Faculty ID in the database
const char* FACULTY_NAME = "Dr. Smith";      // Faculty name

// Display Settings
#define TFT_BG TFT_BLACK                     // Background color
#define TFT_TEXT TFT_WHITE                   // Text color
#define TFT_HEADER_BG 0x03E0                 // Header background color (dark green)
#define STATUS_AVAILABLE TFT_GREEN           // Available status color
#define STATUS_UNAVAILABLE TFT_RED           // Unavailable status color

// ===== Global Variables =====
// Display
TFT_eSPI tft = TFT_eSPI();                  // TFT instance

// WiFi & MQTT
WiFiClient espClient;
PubSubClient mqtt(espClient);
bool mqttConnected = false;
unsigned long lastWiFiReconnectAttempt = 0;
unsigned long lastMQTTReconnectAttempt = 0;
const unsigned long WIFI_RECONNECT_INTERVAL = 10000; // 10 seconds
const unsigned long MQTT_RECONNECT_INTERVAL = 5000;  // 5 seconds

// BLE Scanning
NimBLEScan* pBLEScan = nullptr;
bool facultyPresent = false;
unsigned long lastBLEDetectionTime = 0;
unsigned long lastBLEScanTime = 0;
NimBLEAddress targetBLEAddress(TARGET_BLE_ADDRESS); // Pre-create NimBLEAddress for comparison

// Consultation Requests
#define MAX_REQUESTS 5                       // Maximum number of displayed requests
struct ConsultationRequest {
  int id;
  String studentName;
  String message;
  String courseCode;
  String requestTime;
  String status;
  bool isNew;
};
ConsultationRequest requests[MAX_REQUESTS];
int requestCount = 0;

// Other
unsigned long lastStatusUpdateTime = 0;
Preferences preferences;

// ===== Function Declarations =====
void setupWiFi();
void setupMQTT();
void setupBLE();
void setupDisplay();
void reconnectMQTT();
void handleMQTTMessage(char* topic, byte* payload, unsigned int length);
void updateBLEStatus();
void updateDisplay();
void drawHeader();
void drawStatus();
void drawRequests();
void publishStatus(bool available);
void scanBLEDevices();
void processConsultationRequest(JsonDocument& doc);

// ===== Setup Function =====
void setup() {
  // Initialize serial
  Serial.begin(115200);
  Serial.println("\nConsultEase Faculty Desk Unit Starting...");
  
  // Initialize preferences
  preferences.begin("consultease", false);
  
  // Setup components
  setupDisplay();
  setupWiFi();
  setupMQTT();
  setupBLE();
  
  // Initial display update
  updateDisplay();
  
  Serial.println("Setup complete!");
}

// ===== Main Loop =====
void loop() {
  // Handle WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastWiFiReconnectAttempt > WIFI_RECONNECT_INTERVAL) {
      lastWiFiReconnectAttempt = millis();
      Serial.println("WiFi disconnected. Attempting reconnection...");
      setupWiFi(); // This will now be non-blocking
    }
  }
  
  // Handle MQTT connection
  if (WiFi.status() == WL_CONNECTED && !mqtt.connected()) {
    if (millis() - lastMQTTReconnectAttempt > MQTT_RECONNECT_INTERVAL) {
      lastMQTTReconnectAttempt = millis();
      Serial.println("MQTT disconnected. Attempting reconnection...");
      reconnectMQTT(); // This will now be non-blocking
    }
  }
  
  if (mqtt.connected()) {
    mqtt.loop();
  }
  
  // Update BLE status
  updateBLEStatus();
  
  // Perform BLE scan at intervals
  unsigned long currentMillis = millis();
  if (currentMillis - lastBLEScanTime > (BLE_SCAN_INTERVAL * 1000)) {
    lastBLEScanTime = currentMillis;
    scanBLEDevices();
  }
  
  // Update display only when needed (after BLE scan or MQTT message)
  
  // Allow other tasks to run
  delay(100);
}

// ===== Component Setup Functions =====
void setupWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  // Show connecting message on display (briefly, as this is non-blocking now)
  tft.fillScreen(TFT_BG);
  tft.setTextColor(TFT_TEXT);
  tft.setTextSize(2);
  tft.setCursor(20, 100);
  tft.println("WiFi: Attempting...");
  
  // Note: Connection check will happen in the loop
  lastWiFiReconnectAttempt = millis(); // Reset timer for next check in loop
}

void setupMQTT() {
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setCallback(handleMQTTMessage);
  reconnectMQTT();
}

void setupBLE() {
  // Initialize BLE device
  NimBLEDevice::init("ConsultEase");
  
  // Create scan instance
  pBLEScan = NimBLEDevice::getScan();
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);
  
  Serial.println("BLE scanning initialized");
}

void setupDisplay() {
  // Initialize TFT display
  tft.init();
  tft.setRotation(1); // Landscape mode
  tft.fillScreen(TFT_BG);
  
  // Show startup screen
  tft.setTextColor(TFT_TEXT);
  tft.setTextSize(3);
  tft.setCursor(30, 50);
  tft.println("ConsultEase");
  tft.setTextSize(2);
  tft.setCursor(60, 90);
  tft.println("Faculty Desk Unit");
  tft.setCursor(40, 150);
  tft.println("Initializing...");
  
  Serial.println("Display initialized");
}

// ===== MQTT Functions =====
void reconnectMQTT() {
  // Attempt to connect to MQTT broker
  if (!mqtt.connected() && WiFi.status() == WL_CONNECTED) { // Only attempt if WiFi is up
    Serial.print("Attempting MQTT connection...");
    
    // Show connecting message on display (briefly)
    // Consider a more persistent status icon/message if connection is intermittent
    // For now, keeping it simple for non-blocking behavior
    // updateDisplay(); // Refresh display to show status

    bool connected = false;
    if (strlen(MQTT_USERNAME) > 0) {
      connected = mqtt.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD);
    } else {
      connected = mqtt.connect(MQTT_CLIENT_ID);
    }
    
    if (connected) {
      Serial.println("connected");
      mqttConnected = true;
      
      // Subscribe to topics
      char requestTopic[50];
      sprintf(requestTopic, "consultease/faculty/%d/requests", FACULTY_ID);
      mqtt.subscribe(requestTopic);
      
      // Publish initial status
      publishStatus(facultyPresent);
      
      // Update display
      updateDisplay();
    } else {
      Serial.println(mqtt.state());
      mqttConnected = false;
      
      // Show error on display - this might be too quick if non-blocking
      // Consider a status area on the main display for MQTT/WiFi status
      // For now, error is logged to Serial.
      // tft.fillScreen(TFT_BG);
      // tft.setCursor(20, 100);
      // tft.println("MQTT connection failed!");
      // tft.setCursor(20, 130);
      // tft.println("Please check settings");
      lastMQTTReconnectAttempt = millis(); // Reset timer for next check in loop
    }
  }
}

void handleMQTTMessage(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  // Create a buffer for the payload
  char message[length + 1];
  for (unsigned int i = 0; i < length; i++) {
    message[i] = (char)payload[i];
  }
  message[length] = '\0';
  
  Serial.println(message);
  
  // Check if this is a consultation request
  char requestTopic[50];
  sprintf(requestTopic, "consultease/faculty/%d/requests", FACULTY_ID);
  
  if (strcmp(topic, requestTopic) == 0) {
    // Parse JSON message
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, message);
    
    if (error) {
      Serial.print("deserializeJson() failed: ");
      Serial.println(error.c_str());
      return;
    }
    
    // Process the consultation request
    processConsultationRequest(doc);
    
    // Update display
    updateDisplay();
  }
}

void publishStatus(bool available) {
  if (!mqtt.connected()) {
    return;
  }
  
  // Create status message
  StaticJsonDocument<128> doc;
  doc["status"] = available;
  doc["faculty_id"] = FACULTY_ID;
  
  char buffer[128];
  size_t n = serializeJson(doc, buffer);
  
  // Publish to faculty status topic
  char statusTopic[50];
  sprintf(statusTopic, "consultease/faculty/%d/status", FACULTY_ID);
  
  mqtt.publish(statusTopic, buffer, n);
  Serial.println("Published status update: " + String(available ? "Available" : "Unavailable"));
  
  lastStatusUpdateTime = millis();
}

// ===== BLE Functions =====
void scanBLEDevices() {
  Serial.println("Scanning for BLE devices...");
  
  // Perform BLE scan
  NimBLEScanResults results = pBLEScan->start(BLE_SCAN_DURATION, false);
  
  // Check if target device is found
  bool deviceFound = false;
  for (int i = 0; i < results.getCount(); i++) {
    NimBLEAdvertisedDevice device = results.getDevice(i);
    String deviceAddressStr = device.getAddress().toString().c_str(); // Keep for logging if needed
    
    if (device.getAddress() == targetBLEAddress) { // Direct comparison of NimBLEAddress objects
      Serial.print("Found target device: ");
      Serial.print(deviceAddressStr.c_str()); // Use the string version for printing
      Serial.print(" with RSSI: ");
      Serial.println(device.getRSSI());
      
      // Check if RSSI is above threshold
      if (device.getRSSI() >= BLE_RSSI_THRESHOLD) {
        deviceFound = true;
        lastBLEDetectionTime = millis();
      }
    }
  }
  
  // Update faculty presence status based on scan results
  bool previousStatus = facultyPresent;
  
  if (deviceFound) {
    facultyPresent = true;
  } else if (millis() - lastBLEDetectionTime > (BLE_TIMEOUT * 1000)) {
    // If not detected for longer than timeout, mark as away
    facultyPresent = false;
  }
  
  // If status changed, update MQTT and display
  if (facultyPresent != previousStatus) {
    publishStatus(facultyPresent);
    updateDisplay();
  }
  
  // Clear scan results to free memory
  pBLEScan->clearResults();
}

void updateBLEStatus() {
  // Check if faculty should be marked as away due to timeout
  if (facultyPresent && millis() - lastBLEDetectionTime > (BLE_TIMEOUT * 1000)) {
    facultyPresent = false;
    publishStatus(facultyPresent);
    updateDisplay();
  }
}

// ===== Display Functions =====
void updateDisplay() {
  // Clear display
  tft.fillScreen(TFT_BG);
  
  // Draw UI components
  drawHeader();
  drawStatus();
  drawRequests();
}

void drawHeader() {
  // Draw header bar
  tft.fillRect(0, 0, tft.width(), 30, TFT_HEADER_BG);
  
  // Draw header text
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 5);
  tft.print(FACULTY_NAME);
}

void drawStatus() {
  // Set status color
  uint16_t statusColor = facultyPresent ? STATUS_AVAILABLE : STATUS_UNAVAILABLE;
  
  // Draw status indicator
  tft.fillRoundRect(10, 40, tft.width() - 20, 40, 5, statusColor);
  
  // Draw status text
  tft.setTextColor(TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(20, 50);
  tft.print(facultyPresent ? "AVAILABLE" : "UNAVAILABLE");
  
  // Draw WiFi/MQTT status indicator
  tft.setTextColor(TFT_TEXT);
  tft.setTextSize(1);
  tft.setCursor(tft.width() - 100, tft.height() - 15); // Position at bottom right
  String wifiStatus = (WiFi.status() == WL_CONNECTED) ? "WiFi:ON" : "WiFi:OFF";
  String mqttStatusText = mqttConnected ? "MQTT:ON" : "MQTT:OFF";
  tft.print(wifiStatus + " " + mqttStatusText);
}

void drawRequests() {
  // Draw requests header
  tft.setTextColor(TFT_TEXT);
  tft.setTextSize(2);
  tft.setCursor(10, 90);
  tft.print("Consultation Requests");
  
  // Draw horizontal line
  tft.drawFastHLine(10, 110, tft.width() - 20, TFT_TEXT);
  
  // Draw request list or "No requests" message
  if (requestCount == 0) {
    tft.setTextSize(1);
    tft.setCursor(10, 130);
    tft.print("No pending consultation requests");
  } else {
    // Draw requests
    int yPos = 120;
    for (int i = 0; i < requestCount && i < MAX_REQUESTS; i++) {
      // Highlight new requests
      if (requests[i].isNew) {
        tft.fillRect(10, yPos - 5, tft.width() - 20, 40, TFT_NAVY);
        requests[i].isNew = false; // Reset new flag after displaying
      }
      
      // Student name
      tft.setTextColor(TFT_YELLOW);
      tft.setTextSize(1);
      tft.setCursor(10, yPos);
      tft.print(requests[i].studentName);
      
      // Course code (if any)
      if (requests[i].courseCode.length() > 0) {
        tft.setTextColor(TFT_GREEN);
        tft.setCursor(tft.width() - 70, yPos);
        tft.print(requests[i].courseCode);
      }
      
      // Request message
      tft.setTextColor(TFT_TEXT);
      tft.setCursor(10, yPos + 15);
      
      // Truncate message if too long
      String message = requests[i].message;
      if (message.length() > 40) {
        message = message.substring(0, 37) + "...";
      }
      tft.print(message);
      
      // Time
      tft.setTextColor(TFT_SILVER);
      tft.setCursor(10, yPos + 30);
      tft.print(requests[i].requestTime);
      
      yPos += 45;
      
      // Draw divider line except for last item
      if (i < requestCount - 1 && i < MAX_REQUESTS - 1) {
        tft.drawFastHLine(20, yPos - 5, tft.width() - 40, TFT_DARKGREY);
      }
    }
  }
}

// ===== Consultation Request Functions =====
void processConsultationRequest(JsonDocument& doc) {
  // Create a new consultation request
  ConsultationRequest newRequest;
  
  // Fill in request data
  newRequest.id = doc["id"];
  newRequest.studentName = doc["student_name"].as<String>();
  newRequest.message = doc["request_message"].as<String>();
  newRequest.courseCode = doc["course_code"].as<String>();
  newRequest.status = doc["status"].as<String>();
  newRequest.requestTime = doc["requested_at"].as<String>().substring(11, 16); // Extract time (HH:MM)
  newRequest.isNew = true;
  
  // Check if this request already exists (update) or is new
  bool isUpdate = false;
  for (int i = 0; i < requestCount; i++) {
    if (requests[i].id == newRequest.id) {
      // Update existing request
      requests[i] = newRequest;
      isUpdate = true;
      break;
    }
  }
  
  // If not an update and we have space, add as new request
  if (!isUpdate && requestCount < MAX_REQUESTS) {
    // Shift existing requests to make room at the top
    for (int i = requestCount; i > 0; i--) {
      requests[i] = requests[i - 1];
    }
    
    // Add new request at the top
    requests[0] = newRequest;
    
    // Increment request count
    if (requestCount < MAX_REQUESTS) {
      requestCount++;
    }
  }
  
  // Flash display background to notify of new request
  for (int i = 0; i < 3; i++) {
    tft.fillScreen(TFT_NAVY);
    delay(200);
    tft.fillScreen(TFT_BG);
    delay(200);
  }
} 