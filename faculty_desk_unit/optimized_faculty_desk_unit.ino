/**
 * Optimized ConsultEase Faculty Desk Unit
 * ESP32-based with TFT display, BLE, and MQTT
 * Includes memory optimization, power management, and security enhancements
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLEAdvertising.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <ArduinoJson.h>

// Include optimization modules
#include "optimizations/memory_optimization.h"
#include "optimizations/power_management.h"
#include "optimizations/security_enhancements.h"

// Configuration
#include "config.h"

// Display configuration
#define TFT_CS     5
#define TFT_RST    4
#define TFT_DC     2
#define TFT_MOSI   23
#define TFT_SCLK   18

// Colors (optimized for readability)
#define COLOR_BACKGROUND    0x0000  // Black
#define COLOR_PRIMARY       0x001F  // Blue
#define COLOR_SECONDARY     0xF800  // Red
#define COLOR_TEXT          0xFFFF  // White
#define COLOR_ACCENT        0xFFE0  // Yellow
#define COLOR_SUCCESS       0x07E0  // Green
#define COLOR_WARNING       0xFD20  // Orange

// Global objects
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCLK, TFT_RST);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// BLE objects
BLEServer* pServer = nullptr;
BLEAdvertising* pAdvertising = nullptr;
bool deviceConnected = false;
bool oldDeviceConnected = false;

// System state
bool systemInitialized = false;
unsigned long lastMQTTReconnect = 0;
unsigned long lastBLECheck = 0;
unsigned long lastDisplayUpdate = 0;
unsigned long lastHeartbeat = 0;

// Message handling
char currentMessage[512];
bool hasNewMessage = false;
unsigned long messageDisplayTime = 0;

// Performance monitoring
unsigned long frameStartTime = 0;
int frameCount = 0;
float averageFrameTime = 0;

// Function prototypes
void initializeSystem();
void initializeDisplay();
void initializeWiFi();
void initializeMQTT();
void initializeBLE();
void updateSystem();
void handleMQTTMessage(char* topic, byte* payload, unsigned int length);
void displayMessage(const char* message);
void displaySystemStatus();
void displayLogo();
void checkConnections();
void publishHeartbeat();
void handlePowerManagement();
void performSecurityChecks();

// BLE Callbacks
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        PowerManager::recordActivity();
        Serial.println("BLE device connected");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("BLE device disconnected");
    }
};

void setup() {
    Serial.begin(115200);
    Serial.println("Starting Optimized ConsultEase Faculty Desk Unit...");
    
    // Initialize optimization systems
    MemoryMonitor::init();
    PowerManager::init();
    EncryptionManager::init();
    MessageAuthenticator::init();
    DeviceAuthenticator::init();
    SecurityMonitor::init();
    
    // Initialize main system
    initializeSystem();
    
    Serial.println("System initialization complete");
    systemInitialized = true;
    
    // Record initial activity
    PowerManager::recordActivity();
    PowerManager::recordDisplayActivity();
}

void loop() {
    frameStartTime = micros();
    
    // Update optimization systems
    PowerManager::update();
    SecurityMonitor::checkSecurityStatus();
    MemoryMonitor::checkMemory();
    
    // Main system updates
    if (systemInitialized) {
        updateSystem();
    }
    
    // Performance monitoring
    unsigned long frameTime = micros() - frameStartTime;
    frameCount++;
    averageFrameTime = (averageFrameTime * (frameCount - 1) + frameTime) / frameCount;
    
    // Reset frame count periodically
    if (frameCount >= 1000) {
        Serial.printf("Average frame time: %.2f us\n", averageFrameTime);
        frameCount = 0;
        averageFrameTime = 0;
    }
    
    // Power-aware delay
    powerAwareDelay(10);
}

void initializeSystem() {
    Serial.println("Initializing system components...");
    
    // Initialize display first
    initializeDisplay();
    displayLogo();
    
    // Initialize network components
    initializeWiFi();
    initializeMQTT();
    initializeBLE();
    
    // Display initial status
    displaySystemStatus();
    
    Serial.println("System components initialized");
}

void initializeDisplay() {
    Serial.println("Initializing display...");
    
    tft.init(240, 320);
    tft.setRotation(1);
    tft.fillScreen(COLOR_BACKGROUND);
    
    // Initialize display buffer
    DisplayBuffer::init();
    
    Serial.println("Display initialized");
}

void initializeWiFi() {
    Serial.println("Connecting to WiFi...");
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
        
        // Update display with connection status
        tft.fillRect(0, 200, 320, 40, COLOR_BACKGROUND);
        tft.setCursor(10, 210);
        tft.setTextColor(COLOR_TEXT);
        tft.setTextSize(1);
        tft.printf("WiFi connecting... %d/20", attempts);
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.printf("IP address: %s\n", WiFi.localIP().toString().c_str());
        
        // Enable WiFi power management for battery life
        PowerManager::enableWiFiPowerSave();
    } else {
        Serial.println("\nWiFi connection failed!");
    }
}

void initializeMQTT() {
    Serial.println("Initializing MQTT...");
    
    mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
    mqttClient.setCallback(handleMQTTMessage);
    
    // Set authentication if available
    const char* authToken = DeviceAuthenticator::getAuthToken();
    if (authToken) {
        mqttClient.setCredentials(DeviceAuthenticator::getDeviceId(), authToken);
    }
    
    Serial.println("MQTT initialized");
}

void initializeBLE() {
    Serial.println("Initializing BLE...");
    
    BLEDevice::init("ConsultEase-Faculty-Desk");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());
    
    // Create BLE service
    BLEService *pService = pServer->createService("12345678-1234-1234-1234-123456789abc");
    
    // Start advertising
    pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID("12345678-1234-1234-1234-123456789abc");
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("BLE initialized and advertising");
}

void updateSystem() {
    unsigned long currentTime = millis();
    
    // Handle MQTT
    if (WiFi.status() == WL_CONNECTED) {
        if (!mqttClient.connected()) {
            if (currentTime - lastMQTTReconnect > 5000) {
                Serial.println("Attempting MQTT reconnection...");
                
                String clientId = "FacultyDesk-";
                clientId += DeviceAuthenticator::getDeviceId();
                
                if (mqttClient.connect(clientId.c_str())) {
                    Serial.println("MQTT connected");
                    
                    // Subscribe to consultation topics
                    globalStringHandler.reset();
                    globalStringHandler.append("consultease/faculty/");
                    globalStringHandler.append(String(FACULTY_ID).c_str());
                    globalStringHandler.append("/consultation");
                    
                    mqttClient.subscribe(globalStringHandler.getString());
                    
                    // Subscribe to system topics
                    mqttClient.subscribe("consultease/system/broadcast");
                    
                    PowerManager::recordActivity();
                } else {
                    Serial.printf("MQTT connection failed, rc=%d\n", mqttClient.state());
                }
                lastMQTTReconnect = currentTime;
            }
        } else {
            mqttClient.loop();
        }
    }
    
    // Handle BLE status changes
    if (currentTime - lastBLECheck > 1000) {
        if (deviceConnected != oldDeviceConnected) {
            if (deviceConnected) {
                // Publish faculty available status
                if (mqttClient.connected()) {
                    globalStringHandler.reset();
                    globalStringHandler.append("consultease/faculty/");
                    globalStringHandler.append(String(FACULTY_ID).c_str());
                    globalStringHandler.append("/status");
                    
                    mqttClient.publish(globalStringHandler.getString(), "available");
                }
            } else {
                // Publish faculty unavailable status
                if (mqttClient.connected()) {
                    globalStringHandler.reset();
                    globalStringHandler.append("consultease/faculty/");
                    globalStringHandler.append(String(FACULTY_ID).c_str());
                    globalStringHandler.append("/status");
                    
                    mqttClient.publish(globalStringHandler.getString(), "unavailable");
                }
                
                // Restart advertising
                pServer->startAdvertising();
            }
            oldDeviceConnected = deviceConnected;
        }
        lastBLECheck = currentTime;
    }
    
    // Update display if needed
    if (hasNewMessage || currentTime - lastDisplayUpdate > 30000) {
        if (hasNewMessage) {
            displayMessage(currentMessage);
            hasNewMessage = false;
            messageDisplayTime = currentTime;
            PowerManager::recordDisplayActivity();
        } else {
            displaySystemStatus();
        }
        lastDisplayUpdate = currentTime;
    }
    
    // Publish heartbeat
    if (currentTime - lastHeartbeat > 60000) {
        publishHeartbeat();
        lastHeartbeat = currentTime;
    }
    
    // Perform security checks
    performSecurityChecks();
}

void handleMQTTMessage(char* topic, byte* payload, unsigned int length) {
    PowerManager::recordActivity();
    
    // Validate topic
    if (!SecurityUtils::validateMQTTTopic(topic)) {
        SecurityMonitor::recordSuspiciousActivity("Invalid MQTT topic");
        return;
    }
    
    // Convert payload to string
    char message[512];
    if (length >= sizeof(message)) {
        SecurityMonitor::recordSuspiciousActivity("MQTT payload too large");
        return;
    }
    
    memcpy(message, payload, length);
    message[length] = '\0';
    
    // Validate payload
    if (!SecurityUtils::validateMQTTPayload(message, sizeof(message))) {
        SecurityMonitor::recordSuspiciousActivity("Invalid MQTT payload");
        return;
    }
    
    Serial.printf("Received message on topic: %s\n", topic);
    Serial.printf("Message: %s\n", message);
    
    // Process the message
    optimizedProcessMessage(message, currentMessage, sizeof(currentMessage));
    hasNewMessage = true;
    
    // Flash notification
    for (int i = 0; i < 3; i++) {
        tft.fillRect(0, 0, 320, 10, COLOR_ACCENT);
        delay(100);
        tft.fillRect(0, 0, 320, 10, COLOR_BACKGROUND);
        delay(100);
    }
}

void displayMessage(const char* message) {
    if (!PowerManager::isDisplayEnabled()) return;
    
    tft.fillScreen(COLOR_BACKGROUND);
    
    // Display header
    tft.fillRect(0, 0, 320, 40, COLOR_PRIMARY);
    tft.setCursor(10, 15);
    tft.setTextColor(COLOR_TEXT);
    tft.setTextSize(2);
    tft.print("Consultation Request");
    
    // Display message content
    tft.setCursor(10, 60);
    tft.setTextColor(COLOR_TEXT);
    tft.setTextSize(1);
    
    // Use optimized display function
    optimizedDisplayMessage(message);
    
    // Display footer with timestamp
    tft.fillRect(0, 200, 320, 40, COLOR_SECONDARY);
    tft.setCursor(10, 215);
    tft.setTextColor(COLOR_TEXT);
    tft.setTextSize(1);
    
    // Format timestamp
    snprintf(timeBuffer, sizeof(timeBuffer), "Received: %02d:%02d:%02d", 
             (millis() / 3600000) % 24, (millis() / 60000) % 60, (millis() / 1000) % 60);
    tft.print(timeBuffer);
}

void displaySystemStatus() {
    if (!PowerManager::isDisplayEnabled()) return;
    
    tft.fillScreen(COLOR_BACKGROUND);
    
    // Display logo and title
    displayLogo();
    
    // Display status information
    tft.setCursor(10, 100);
    tft.setTextColor(COLOR_TEXT);
    tft.setTextSize(1);
    
    // WiFi status
    tft.printf("WiFi: %s\n", WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
    
    // MQTT status
    tft.printf("MQTT: %s\n", mqttClient.connected() ? "Connected" : "Disconnected");
    
    // BLE status
    tft.printf("BLE: %s\n", deviceConnected ? "Connected" : "Advertising");
    
    // Faculty status
    tft.printf("Faculty: %s\n", deviceConnected ? "Available" : "Away");
    
    // System information
    tft.printf("Memory: %d KB free\n", ESP.getFreeHeap() / 1024);
    tft.printf("Uptime: %lu min\n", millis() / 60000);
    
    // Battery status (if available)
    tft.printf("Battery: %d%%\n", PowerManager::getBatteryPercentage());
    
    // Security status
    tft.setTextColor(DeviceAuthenticator::isAuthenticated() ? COLOR_SUCCESS : COLOR_WARNING);
    tft.printf("Security: %s\n", DeviceAuthenticator::isAuthenticated() ? "Authenticated" : "Not Auth");
}

void displayLogo() {
    // Display National University logo area
    tft.fillRect(50, 20, 220, 60, COLOR_PRIMARY);
    tft.setCursor(70, 40);
    tft.setTextColor(COLOR_TEXT);
    tft.setTextSize(2);
    tft.print("ConsultEase");
    
    tft.setCursor(80, 60);
    tft.setTextSize(1);
    tft.print("Faculty Desk Unit");
}

void publishHeartbeat() {
    if (!mqttClient.connected()) return;
    
    // Create heartbeat message
    DynamicJsonDocument doc(256);
    doc["device_id"] = DeviceAuthenticator::getDeviceId();
    doc["faculty_id"] = FACULTY_ID;
    doc["timestamp"] = millis();
    doc["status"] = deviceConnected ? "available" : "away";
    doc["battery"] = PowerManager::getBatteryPercentage();
    doc["memory_free"] = ESP.getFreeHeap();
    doc["uptime"] = millis();
    
    globalStringHandler.reset();
    serializeJson(doc, globalStringHandler.getString(), MAX_MESSAGE_LENGTH);
    
    // Publish heartbeat
    globalStringHandler.reset();
    globalStringHandler.append("consultease/faculty/");
    globalStringHandler.append(String(FACULTY_ID).c_str());
    globalStringHandler.append("/heartbeat");
    
    mqttClient.publish(globalStringHandler.getString(), globalStringHandler.getString());
}

void performSecurityChecks() {
    // Check authentication status
    if (!DeviceAuthenticator::isAuthenticated()) {
        // Attempt re-authentication with stored credentials
        // This would be implemented based on your authentication system
    }
    
    // Check for security breaches
    if (SecurityMonitor::isSecurityBreached()) {
        // Implement security response
        Serial.println("SECURITY BREACH DETECTED - Implementing countermeasures");
        
        // Could disable certain features, alert admin, etc.
    }
    
    // Rotate encryption keys periodically
    static unsigned long lastKeyRotation = 0;
    if (millis() - lastKeyRotation > 3600000) { // Every hour
        EncryptionManager::rotateSessionKey();
        lastKeyRotation = millis();
    }
}
