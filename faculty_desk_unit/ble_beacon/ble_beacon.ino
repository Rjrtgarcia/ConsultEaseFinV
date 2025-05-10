/**
 * ConsultEase - Faculty BLE Beacon
 * 
 * This firmware creates a BLE beacon that faculty members can carry to automatically
 * update their availability status. It can be used on a separate ESP32 device or 
 * even programmed onto a small ESP32-based wearable.
 * 
 * The device advertises a BLE signal with a specific MAC address that the
 * Faculty Desk Unit detects to determine presence.
 */

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEServer.h>
#include <NimBLEUtils.h>

// ===== Configuration =====
const char* DEVICE_NAME = "ConsultEase-Faculty";  // BLE device name
const int ADVERTISE_INTERVAL = 200;               // Advertising interval in ms
const int LED_PIN = 2;                            // Built-in LED pin (for status indication)

// Battery management
const int BATTERY_PIN = 34;                       // Battery voltage measurement pin (optional)
const float BATTERY_DIVIDER_RATIO = 2.0;          // Voltage divider ratio for battery measurement
const float BATTERY_MAX_VOLTAGE = 4.2;            // Maximum battery voltage
const float BATTERY_MIN_VOLTAGE = 3.3;            // Minimum battery voltage
const float ADC_REFERENCE = 3.3;                  // ADC reference voltage
const int ADC_RESOLUTION = 4095;                  // ADC resolution

// ===== Global Variables =====
NimBLEServer* pServer = nullptr;
bool deviceConnected = false;
unsigned long lastBatteryCheck = 0;
int batteryLevel = 100;

// UUID used for ConsultEase faculty identification
#define SERVICE_UUID        "91BAD35B-F3CB-4FC1-8603-88D5137892A6"
#define CHARACTERISTIC_UUID "D9473AA3-E6F4-424B-B6E7-A5F94FDDA285"

class ServerCallbacks: public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer) {
        deviceConnected = true;
        digitalWrite(LED_PIN, HIGH);  // Turn on LED when connected
        Serial.println("Device connected");
    };

    void onDisconnect(NimBLEServer* pServer) {
        deviceConnected = false;
        digitalWrite(LED_PIN, LOW);   // Turn off LED when disconnected
        Serial.println("Device disconnected");
        // Start advertising again
        NimBLEAdvertising* pAdvertising = pServer->getAdvertising();
        pAdvertising->start();
    }
};

void setup() {
    // Initialize serial
    Serial.begin(115200);
    Serial.println("ConsultEase Faculty BLE Beacon Starting...");
    
    // Initialize LED
    pinMode(LED_PIN, OUTPUT);
    
    // Initialize BLE device
    NimBLEDevice::init(DEVICE_NAME);
    
    // Set transmit power (can be one of: ESP_PWR_LVL_N12, ESP_PWR_LVL_N9, ESP_PWR_LVL_N6,
    // ESP_PWR_LVL_N3, ESP_PWR_LVL_N0, ESP_PWR_LVL_P3, ESP_PWR_LVL_P6, ESP_PWR_LVL_P9)
    NimBLEDevice::setPower(ESP_PWR_LVL_P9); // Maximum power
    
    // Create the BLE Server
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());
    
    // Create the BLE Service
    NimBLEService* pService = pServer->createService(SERVICE_UUID);
    
    // Create a BLE Characteristic
    NimBLECharacteristic* pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
    );
    
    // Initial value
    uint8_t initialValue[4] = {0x46, 0x41, 0x43, 0x31}; // "FAC1" in hex
    pCharacteristic->setValue(initialValue, 4);
    
    // Start the service
    pService->start();
    
    // Start advertising
    NimBLEAdvertising* pAdvertising = pServer->getAdvertising();
    pAdvertising->setName(DEVICE_NAME);
    pAdvertising->setManufacturerData("CE01"); // ConsultEase identifier
    pAdvertising->setScanResponse(true);
    
    // Set advertising interval (lower values = more frequent advertising, but more power consumption)
    pAdvertising->setMinInterval(ADVERTISE_INTERVAL / 0.625);  // min interval in 0.625ms units
    pAdvertising->setMaxInterval(ADVERTISE_INTERVAL / 0.625);  // max interval in 0.625ms units
    
    // Start advertising
    pAdvertising->start();
    
    Serial.println("BLE Advertising started");
    Serial.print("Device MAC Address: ");
    Serial.println(NimBLEDevice::getAddress().toString().c_str());
    Serial.println("Setup complete! Beacon is now broadcasting.");
    
    // Blink LED to indicate ready
    for (int i = 0; i < 5; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(100);
        digitalWrite(LED_PIN, LOW);
        delay(100);
    }
}

void loop() {
    // Check battery level every minute
    if (millis() - lastBatteryCheck > 60000) {
        lastBatteryCheck = millis();
        checkBattery();
    }
    
    // Blink LED occasionally to show it's working
    if (!deviceConnected) {
        // Single short blink every 5 seconds if not connected
        if (millis() % 5000 < 50) {
            digitalWrite(LED_PIN, HIGH);
        } else {
            digitalWrite(LED_PIN, LOW);
        }
    }
    
    // Allow for some power savings
    delay(100);
}

void checkBattery() {
    // Read battery voltage (if connected)
    if (BATTERY_PIN > 0) {
        int adcValue = analogRead(BATTERY_PIN);
        float voltage = (adcValue / (float)ADC_RESOLUTION) * ADC_REFERENCE * BATTERY_DIVIDER_RATIO;
        
        // Calculate percentage
        float percentage = (voltage - BATTERY_MIN_VOLTAGE) / (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE) * 100.0;
        
        // Constrain to 0-100%
        batteryLevel = constrain(percentage, 0, 100);
        
        Serial.print("Battery: ");
        Serial.print(voltage);
        Serial.print("V (");
        Serial.print(batteryLevel);
        Serial.println("%)");
        
        // If battery is too low, blink rapidly to indicate charging needed
        if (batteryLevel < 10) {
            for (int i = 0; i < 10; i++) {
                digitalWrite(LED_PIN, HIGH);
                delay(100);
                digitalWrite(LED_PIN, LOW);
                delay(100);
            }
        }
    }
} 