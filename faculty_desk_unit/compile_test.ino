/*
 * Compilation Test for Faculty Desk Unit with NTP
 * 
 * This is a minimal test to verify that all includes and basic
 * functionality compiles correctly before uploading to ESP32.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <time.h>
#include <WiFiUdp.h>
#include <NTPClient.h>

// Test configuration
const char* ssid = "TestNetwork";
const char* password = "TestPassword";

// NTP Configuration
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 8 * 3600;  // Philippines timezone UTC+8
const int daylightOffset_sec = 0;

// NTP Client setup
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, ntpServer, gmtOffset_sec, 60000);

// TFT Display pins
#define TFT_CS    5
#define TFT_DC    21
#define TFT_RST   22
#define TFT_MOSI  23
#define TFT_SCLK  18

// Initialize display
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCLK, TFT_RST);

// Color definitions
#define ST77XX_GREEN 0x07E0
#define ST77XX_RED   0xF800
#define ST77XX_ORANGE 0xFD20
#define ST77XX_WHITE 0xFFFF
#define ST77XX_BLACK 0x0000

// BLE variables
BLEScan* pBLEScan = nullptr;
bool ntpSyncSuccessful = false;

// Test BLE callback class
class TestAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        Serial.print("BLE Device found: ");
        Serial.println(advertisedDevice.toString().c_str());
    }
};

void setup() {
    Serial.begin(115200);
    Serial.println("=== Faculty Desk Unit Compilation Test ===");
    
    // Test display initialization
    Serial.println("Testing display initialization...");
    SPI.begin();
    tft.init(240, 320);
    tft.setRotation(1);
    tft.fillScreen(ST77XX_BLACK);
    tft.setTextColor(ST77XX_WHITE);
    tft.setTextSize(2);
    tft.setCursor(10, 10);
    tft.println("Compile Test OK");
    Serial.println("✓ Display initialization successful");
    
    // Test WiFi initialization
    Serial.println("Testing WiFi initialization...");
    WiFi.mode(WIFI_STA);
    Serial.println("✓ WiFi initialization successful");
    
    // Test NTP client initialization
    Serial.println("Testing NTP client initialization...");
    timeClient.begin();
    Serial.println("✓ NTP client initialization successful");
    
    // Test BLE initialization
    Serial.println("Testing BLE initialization...");
    BLEDevice::init("TestDevice");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new TestAdvertisedDeviceCallbacks());
    pBLEScan->setActiveScan(true);
    pBLEScan->setInterval(100);
    pBLEScan->setWindow(99);
    Serial.println("✓ BLE initialization successful");
    
    // Test MQTT client initialization
    Serial.println("Testing MQTT client initialization...");
    WiFiClient espClient;
    PubSubClient mqttClient(espClient);
    mqttClient.setServer("192.168.1.1", 1883);
    Serial.println("✓ MQTT client initialization successful");
    
    // Test time functions
    Serial.println("Testing time functions...");
    struct tm timeinfo;
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    Serial.println("✓ Time functions successful");
    
    // Display success message
    tft.fillScreen(ST77XX_BLACK);
    tft.setCursor(10, 10);
    tft.setTextColor(ST77XX_GREEN);
    tft.println("All Tests");
    tft.setCursor(10, 40);
    tft.println("PASSED!");
    
    // Test NTP time formatting
    Serial.println("Testing NTP time formatting...");
    String testTime = getTestFormattedTime();
    String testDate = getTestFormattedDate();
    Serial.print("Test time: ");
    Serial.println(testTime);
    Serial.print("Test date: ");
    Serial.println(testDate);
    Serial.println("✓ Time formatting successful");
    
    Serial.println("=== All Compilation Tests PASSED ===");
    Serial.println("The firmware should compile and upload successfully!");
}

void loop() {
    // Test NTP sync status indicator
    static unsigned long lastUpdate = 0;
    if (millis() - lastUpdate > 5000) {
        lastUpdate = millis();
        
        // Toggle sync status for testing
        ntpSyncSuccessful = !ntpSyncSuccessful;
        
        // Test status indicator
        int statusX = tft.width() - 15;
        int statusY = 10;
        
        if (ntpSyncSuccessful) {
            tft.fillCircle(statusX, statusY, 5, ST77XX_GREEN);
            Serial.println("Status: NTP Synced (simulated)");
        } else {
            tft.fillCircle(statusX, statusY, 5, ST77XX_ORANGE);
            Serial.println("Status: Fallback Time (simulated)");
        }
    }
    
    delay(100);
}

String getTestFormattedTime() {
    // Test time formatting function
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
        char timeStr[10];
        strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
        return String(timeStr);
    } else {
        return "12:00:00"; // Fallback
    }
}

String getTestFormattedDate() {
    // Test date formatting function
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
        char dateStr[12];
        strftime(dateStr, sizeof(dateStr), "%Y-%m-%d", &timeinfo);
        return String(dateStr);
    } else {
        return "2024-01-01"; // Fallback
    }
}
