/**
 * Memory optimization implementation for ConsultEase Faculty Desk Unit
 */

#include "memory_optimization.h"
#include <string.h>
#include <stdlib.h>

// Global instances
OptimizedStringHandler globalStringHandler;
char mqttTopicBuffer[64];
char timeBuffer[32];
char dateBuffer[32];

// Static member definitions
unsigned long MemoryMonitor::lastCheck = 0;
size_t MemoryMonitor::minFreeHeap = 0;
char DisplayBuffer::displayBuffer[DISPLAY_BUFFER_SIZE];
bool DisplayBuffer::bufferDirty = false;

// Optimized message processing function
void optimizedDisplayMessage(const char* message) {
    if (!message) return;
    
    // Use global string handler to avoid memory allocation
    globalStringHandler.reset();
    
    // Process message with word wrapping
    const char* ptr = message;
    int lineWidth = 35; // Approximate characters per line
    int currentLineLength = 0;
    
    while (*ptr) {
        char c = *ptr;
        
        if (c == '\n' || currentLineLength >= lineWidth) {
            globalStringHandler.append('\n');
            currentLineLength = 0;
            
            // Skip the newline if it was a forced wrap
            if (c != '\n') {
                globalStringHandler.append(c);
                currentLineLength = 1;
            }
        } else {
            globalStringHandler.append(c);
            currentLineLength++;
        }
        
        ptr++;
    }
    
    // Display the processed message
    Serial.println("Optimized Message Display:");
    Serial.println(globalStringHandler.getString());
}

// Optimized message processing function
void optimizedProcessMessage(const char* input, char* output, size_t outputSize) {
    if (!input || !output || outputSize == 0) return;
    
    globalStringHandler.reset();
    
    // Check if JSON format
    if (input[0] == '{') {
        // Extract message field from JSON
        const char* messageStart = strstr(input, "\"message\":\"");
        if (messageStart) {
            messageStart += 11; // Skip "message":"
            const char* messageEnd = strchr(messageStart, '"');
            if (messageEnd) {
                size_t messageLen = messageEnd - messageStart;
                if (messageLen < MAX_MESSAGE_LENGTH - 1) {
                    strncpy(output, messageStart, messageLen);
                    output[messageLen] = '\0';
                    return;
                }
            }
        }
        
        // Try to extract other fields
        const char* fields[] = {"student_name", "course_code", "request_message"};
        for (int i = 0; i < 3; i++) {
            char searchStr[32];
            snprintf(searchStr, sizeof(searchStr), "\"%s\":\"", fields[i]);
            
            const char* fieldStart = strstr(input, searchStr);
            if (fieldStart) {
                fieldStart += strlen(searchStr);
                const char* fieldEnd = strchr(fieldStart, '"');
                if (fieldEnd) {
                    size_t fieldLen = fieldEnd - fieldStart;
                    if (fieldLen > 0 && globalStringHandler.length() + fieldLen + 20 < MAX_MESSAGE_LENGTH) {
                        if (i == 0) globalStringHandler.append("Student: ");
                        else if (i == 1) globalStringHandler.append("Course: ");
                        else globalStringHandler.append("Request: ");
                        
                        // Append field value
                        for (size_t j = 0; j < fieldLen; j++) {
                            globalStringHandler.append(fieldStart[j]);
                        }
                        globalStringHandler.append('\n');
                    }
                }
            }
        }
        
        SAFE_STRING_COPY(output, globalStringHandler.getString(), outputSize);
    } else {
        // Plain text message
        SAFE_STRING_COPY(output, input, outputSize);
    }
}

// Optimized JSON field extraction
bool optimizedJSONExtract(const char* json, const char* key, char* value, size_t valueSize) {
    if (!json || !key || !value || valueSize == 0) return false;
    
    // Create search pattern
    char searchPattern[64];
    snprintf(searchPattern, sizeof(searchPattern), "\"%s\":\"", key);
    
    const char* start = strstr(json, searchPattern);
    if (!start) return false;
    
    start += strlen(searchPattern);
    const char* end = strchr(start, '"');
    if (!end) return false;
    
    size_t length = end - start;
    if (length >= valueSize) length = valueSize - 1;
    
    strncpy(value, start, length);
    value[length] = '\0';
    
    return true;
}

// Memory monitoring functions
void MemoryMonitor::init() {
    lastCheck = millis();
    minFreeHeap = ESP.getFreeHeap();
    Serial.printf("Memory Monitor initialized - Free: %d bytes\n", minFreeHeap);
}

void MemoryMonitor::checkMemory() {
    size_t currentFree = ESP.getFreeHeap();
    if (currentFree < minFreeHeap) {
        minFreeHeap = currentFree;
    }
    
    // Log memory status every 30 seconds
    if (millis() - lastCheck > 30000) {
        Serial.printf("Memory Status - Free: %d bytes, Min: %d bytes\n", 
                     currentFree, minFreeHeap);
        lastCheck = millis();
        
        // Warning if memory is low
        if (currentFree < 10000) {
            Serial.println("WARNING: Low memory detected!");
        }
        
        // Critical memory warning
        if (currentFree < 5000) {
            Serial.println("CRITICAL: Very low memory! Forcing garbage collection...");
            forceGarbageCollection();
        }
    }
}

size_t MemoryMonitor::getFreeHeap() {
    return ESP.getFreeHeap();
}

size_t MemoryMonitor::getMinFreeHeap() {
    return minFreeHeap;
}

void MemoryMonitor::forceGarbageCollection() {
    // Force garbage collection by allocating and freeing memory
    void* ptr = malloc(1024);
    if (ptr) {
        free(ptr);
    }
    
    // Also try to trigger ESP32 garbage collection
    size_t beforeGC = ESP.getFreeHeap();
    delay(10);
    size_t afterGC = ESP.getFreeHeap();
    
    Serial.printf("Garbage collection: %d -> %d bytes (freed %d)\n", 
                 beforeGC, afterGC, afterGC - beforeGC);
}

// Display buffer functions
void DisplayBuffer::init() {
    memset(displayBuffer, 0, DISPLAY_BUFFER_SIZE);
    bufferDirty = false;
    Serial.println("Display buffer initialized");
}

char* DisplayBuffer::getBuffer() {
    return displayBuffer;
}

void DisplayBuffer::markDirty() {
    bufferDirty = true;
}

bool DisplayBuffer::isDirty() {
    return bufferDirty;
}

void DisplayBuffer::markClean() {
    bufferDirty = false;
}

void DisplayBuffer::clear() {
    memset(displayBuffer, 0, DISPLAY_BUFFER_SIZE);
    bufferDirty = true;
}

// Optimized string handler implementation
void OptimizedStringHandler::reset() {
    bufferPos = 0;
    memset(buffer, 0, MAX_MESSAGE_LENGTH);
}

bool OptimizedStringHandler::append(const char* str) {
    size_t len = strlen(str);
    if (bufferPos + len >= MAX_MESSAGE_LENGTH - 1) {
        return false; // Buffer overflow protection
    }
    strcpy(buffer + bufferPos, str);
    bufferPos += len;
    return true;
}

bool OptimizedStringHandler::append(char c) {
    if (bufferPos >= MAX_MESSAGE_LENGTH - 1) {
        return false;
    }
    buffer[bufferPos++] = c;
    buffer[bufferPos] = '\0';
    return true;
}

const char* OptimizedStringHandler::getString() const {
    return buffer;
}

size_t OptimizedStringHandler::length() const {
    return bufferPos;
}

void OptimizedStringHandler::clear() {
    reset();
}

// Memory optimization utility functions
void* optimizedMalloc(size_t size) {
    // Check available memory before allocation
    if (ESP.getFreeHeap() < size + 1000) { // Keep 1KB safety margin
        Serial.printf("WARNING: Low memory for allocation of %d bytes\n", size);
        MemoryMonitor::forceGarbageCollection();
        
        if (ESP.getFreeHeap() < size + 500) {
            Serial.println("ERROR: Insufficient memory for allocation");
            return nullptr;
        }
    }
    
    void* ptr = malloc(size);
    if (ptr) {
        MemoryMonitor::checkMemory();
    }
    return ptr;
}

void optimizedFree(void* ptr) {
    if (ptr) {
        free(ptr);
        MemoryMonitor::checkMemory();
    }
}

// String optimization utilities
void optimizedStringCopy(char* dest, const char* src, size_t maxLen) {
    if (!dest || !src || maxLen == 0) return;
    
    size_t i = 0;
    while (i < maxLen - 1 && src[i] != '\0') {
        dest[i] = src[i];
        i++;
    }
    dest[i] = '\0';
}

int optimizedStringCompare(const char* str1, const char* str2) {
    if (!str1 || !str2) return -1;
    
    while (*str1 && *str2 && *str1 == *str2) {
        str1++;
        str2++;
    }
    
    return *str1 - *str2;
}

// Memory statistics
void printMemoryStatistics() {
    Serial.println("=== Memory Statistics ===");
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("Min Free Heap: %d bytes\n", MemoryMonitor::getMinFreeHeap());
    Serial.printf("Largest Free Block: %d bytes\n", ESP.getMaxAllocHeap());
    Serial.printf("Total Heap: %d bytes\n", ESP.getHeapSize());
    Serial.printf("Free PSRAM: %d bytes\n", ESP.getFreePsram());
    Serial.println("========================");
}
