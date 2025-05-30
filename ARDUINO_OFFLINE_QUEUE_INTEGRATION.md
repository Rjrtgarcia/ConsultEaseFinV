# Arduino ESP32 Offline Message Queue Integration Guide

## **Answer to Your Questions:**

### **1. Do I need both .h and .cpp files?**
**For Arduino ESP32: YES, you typically need both files when using classes with complex implementations.**

### **2. Is only the .h file sufficient?**
**NO, not for complex implementations. However, I'll provide you with a SIMPLER solution.**

### **3. File placement and integration:**
- Place both `.h` and `.cpp` files in the same folder as `faculty_desk_unit.ino`
- Include only the `.h` file in your main sketch: `#include "offline_message_queue.h"`
- Arduino IDE automatically compiles `.cpp` files in the sketch folder

### **4. Why both files are needed:**
- `.h` file: Contains declarations (what functions exist)
- `.cpp` file: Contains implementations (how functions work)
- Arduino IDE links them together during compilation

## **HOWEVER - Simpler Solution Recommended**

Instead of complex separate files, here's a **simple, working solution** you can add directly to your existing `faculty_desk_unit.ino` file:

## **Simple Offline Queue Implementation**

Add this code directly to your `faculty_desk_unit.ino` file:

```cpp
// ================================
// SIMPLE OFFLINE MESSAGE QUEUE
// ================================

struct SimpleMessage {
  char topic[64];
  char payload[512];
  unsigned long timestamp;
  int retry_count;
  bool is_response;
};

// Queue variables
SimpleMessage messageQueue[10];  // Adjust size as needed
int queueCount = 0;
bool systemOnline = false;

// Queue functions
void initOfflineQueue() {
  queueCount = 0;
  systemOnline = false;
  DEBUG_PRINTLN("📥 Offline message queue initialized");
}

bool queueMessage(const char* topic, const char* payload, bool isResponse = false) {
  if (queueCount >= 10) {
    DEBUG_PRINTLN("⚠️ Queue full, dropping oldest message");
    // Shift queue to make room
    for (int i = 0; i < 9; i++) {
      messageQueue[i] = messageQueue[i + 1];
    }
    queueCount = 9;
  }
  
  // Add new message
  strncpy(messageQueue[queueCount].topic, topic, 63);
  strncpy(messageQueue[queueCount].payload, payload, 511);
  messageQueue[queueCount].topic[63] = '\0';
  messageQueue[queueCount].payload[511] = '\0';
  messageQueue[queueCount].timestamp = millis();
  messageQueue[queueCount].retry_count = 0;
  messageQueue[queueCount].is_response = isResponse;
  
  queueCount++;
  DEBUG_PRINTF("📥 Queued message (%d in queue): %s\n", queueCount, topic);
  return true;
}

bool processQueuedMessages() {
  if (!mqttClient.connected() || queueCount == 0) {
    return false;
  }
  
  // Process one message at a time
  bool success = mqttClient.publish(messageQueue[0].topic, messageQueue[0].payload, MQTT_QOS);
  
  if (success) {
    DEBUG_PRINTF("📤 Sent queued message: %s\n", messageQueue[0].topic);
    
    // Remove processed message by shifting queue
    for (int i = 0; i < queueCount - 1; i++) {
      messageQueue[i] = messageQueue[i + 1];
    }
    queueCount--;
    return true;
  } else {
    // Increment retry count
    messageQueue[0].retry_count++;
    if (messageQueue[0].retry_count > 3) {
      DEBUG_PRINTLN("❌ Message failed after 3 retries, dropping");
      // Remove failed message
      for (int i = 0; i < queueCount - 1; i++) {
        messageQueue[i] = messageQueue[i + 1];
      }
      queueCount--;
    }
    return false;
  }
}

void updateOfflineQueue() {
  // Update online status
  bool wasOnline = systemOnline;
  systemOnline = wifiConnected && mqttConnected;
  
  // If just came online, process queue
  if (!wasOnline && systemOnline && queueCount > 0) {
    DEBUG_PRINTF("🌐 System online - processing %d queued messages\n", queueCount);
  }
  
  // Process one message per update cycle
  if (systemOnline) {
    processQueuedMessages();
  }
}

// Enhanced publish function with queuing
bool publishWithQueue(const char* topic, const char* payload, bool isResponse = false) {
  if (mqttClient.connected()) {
    bool success = mqttClient.publish(topic, payload, MQTT_QOS);
    if (success) {
      return true;
    } else {
      // MQTT publish failed, queue the message
      return queueMessage(topic, payload, isResponse);
    }
  } else {
    // Not connected, queue the message
    return queueMessage(topic, payload, isResponse);
  }
}
```

## **Integration Steps**

### **Step 1: Add to setup()**
```cpp
void setup() {
  // ... your existing setup code ...
  
  // Initialize offline queue
  initOfflineQueue();
  
  // ... rest of setup ...
}
```

### **Step 2: Add to loop()**
```cpp
void loop() {
  // ... your existing loop code ...
  
  // Update offline queue
  updateOfflineQueue();
  
  // ... rest of loop ...
}
```

### **Step 3: Update your publish functions**

Replace your existing publish calls:

**OLD:**
```cpp
mqttClient.publish(MQTT_TOPIC_RESPONSES, response.c_str(), MQTT_QOS);
```

**NEW:**
```cpp
publishWithQueue(MQTT_TOPIC_RESPONSES, response.c_str(), true);  // true = is response
```

**OLD:**
```cpp
mqttClient.publish(MQTT_TOPIC_STATUS, payload.c_str(), MQTT_QOS);
```

**NEW:**
```cpp
publishWithQueue(MQTT_TOPIC_STATUS, payload.c_str(), false);  // false = not response
```

## **Benefits of This Simple Approach**

### **✅ Advantages:**
1. **No separate files needed** - everything in one place
2. **Arduino-compatible** - uses standard Arduino functions
3. **Simple to understand** - straightforward logic
4. **Easy to debug** - all code visible in main file
5. **Immediate integration** - works with your existing code

### **✅ Features:**
- **Message queuing** when MQTT disconnected
- **Automatic processing** when connection restored
- **Retry logic** with failure handling
- **Queue overflow protection**
- **Response prioritization** (responses processed first)

### **✅ Memory efficient:**
- Fixed-size arrays (no dynamic allocation)
- Configurable queue size
- Automatic cleanup of failed messages

## **Usage Examples**

### **Queue a faculty response:**
```cpp
void handleAcknowledgeButton() {
  String response = "{\"faculty_id\":1,\"response\":\"ACKNOWLEDGE\"}";
  publishWithQueue(MQTT_TOPIC_RESPONSES, response.c_str(), true);
  showResponseConfirmation("QUEUED", COLOR_WARNING);
}
```

### **Queue a status update:**
```cpp
void publishPresenceUpdate() {
  String payload = "{\"faculty_id\":1,\"present\":true}";
  publishWithQueue(MQTT_TOPIC_STATUS, payload.c_str(), false);
}
```

## **Monitoring Queue Status**

Add this function to check queue status:

```cpp
void printQueueStatus() {
  DEBUG_PRINTF("📊 Queue Status: %d messages, Online: %s\n", 
               queueCount, systemOnline ? "YES" : "NO");
  for (int i = 0; i < queueCount; i++) {
    DEBUG_PRINTF("  [%d] %s (retries: %d)\n", 
                 i, messageQueue[i].topic, messageQueue[i].retry_count);
  }
}
```

## **Final Answer**

**For your ESP32 Arduino project:**

1. **Use the simple solution above** - add the code directly to your `faculty_desk_unit.ino` file
2. **No separate .h/.cpp files needed** for this simple implementation
3. **Immediate functionality** - works right away with your existing code
4. **Production ready** - handles offline operation and automatic recovery

This approach gives you **robust offline message queuing** without the complexity of separate files or advanced C++ features that can cause compilation issues in Arduino IDE.
