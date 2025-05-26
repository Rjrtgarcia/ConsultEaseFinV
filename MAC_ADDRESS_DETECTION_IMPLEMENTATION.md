# MAC Address-Based Faculty Detection Implementation

## Summary

Successfully implemented MAC address-based faculty detection for the ConsultEase Faculty Desk Unit. The system now scans for known faculty device MAC addresses instead of waiting for BLE connections, providing more reliable and flexible faculty presence detection.

## Files Modified

### 1. Faculty Desk Unit Configuration
**File: `faculty_desk_unit/config.h`**
- Added `BLE_DETECTION_MODE_MAC_ADDRESS` flag to enable MAC detection mode
- Added `FACULTY_MAC_ADDRESSES` array declaration for storing known MAC addresses
- Added MAC detection configuration parameters:
  - `MAC_DETECTION_TIMEOUT`: Timeout for faculty absence detection
  - `MAC_SCAN_ACTIVE`: Enable active BLE scanning
  - `MAC_DETECTION_DEBOUNCE`: Required consecutive detections for status change

### 2. Faculty Desk Unit Main Code
**File: `faculty_desk_unit/faculty_desk_unit.ino`**
- **Added BLE Scanner Functionality**:
  - `initializeBLEScanner()`: Initialize BLE scanner instead of server
  - `performBLEScan()`: Perform periodic BLE scans for faculty devices
  - `MyAdvertisedDeviceCallbacks`: Handle BLE scan results
  - `isFacultyMacAddress()`: Check if detected MAC matches known faculty
  - `normalizeMacAddress()`: Normalize MAC address format
  
- **Added MAC Detection Logic**:
  - `updateFacultyPresenceStatus()`: Update presence based on detections with debouncing
  - `publishFacultyStatus()`: Publish detailed MAC status via MQTT
  - Debouncing logic to prevent false positives/negatives
  - Timeout handling for faculty absence detection

- **Enhanced Setup and Loop**:
  - Conditional initialization based on `BLE_DETECTION_MODE_MAC_ADDRESS`
  - Backward compatibility with legacy BLE server mode
  - Integration of MAC scanning in main loop

- **Updated MAC Address Array**:
  - Defined known faculty MAC addresses including Jeysibn's device

### 3. Central System Validators
**File: `central_system/utils/validators.py`**
- Added `MAC_ADDRESS_PATTERN` for MAC address validation
- Updated `validate_ble_id()` to accept both UUID and MAC address formats
- Enhanced error messages to indicate both supported formats

### 4. Faculty Model
**File: `central_system/models/faculty.py`**
- Updated `validate_ble_id()` to support MAC addresses
- Added `normalize_mac_address()` method for consistent MAC formatting
- Enhanced BLE ID validation to handle both UUID and MAC formats

### 5. MQTT Topics
**File: `central_system/utils/mqtt_topics.py`**
- Added `FACULTY_MAC_STATUS` topic for detailed MAC address status updates
- Added `get_faculty_mac_status_topic()` method for topic generation

### 6. Faculty Controller
**File: `central_system/controllers/faculty_controller.py`**
- **Added MAC Status Handler**:
  - Processes MAC address status updates from desk units
  - Automatically updates faculty BLE ID with detected MAC addresses
  - Publishes system notifications for MAC-based status changes
  - Handles both presence and absence detection

- **Enhanced Legacy Support**:
  - Updated legacy status handling to support new status messages
  - Maintains backward compatibility with existing systems

### 7. Database Sample Data
**File: `central_system/models/base.py`**
- Updated sample faculty data to use MAC address format
- Added Jeysibn faculty member with corresponding MAC address
- Ensured MAC addresses match those configured in desk unit

## New Features

### 1. MAC Address Detection
- Scans for known faculty device MAC addresses
- Supports multiple faculty members per desk unit
- Configurable RSSI threshold for proximity detection
- Debouncing logic to prevent false status changes

### 2. Enhanced MQTT Communication
- New `mac_status` topic with detailed information:
  ```json
  {
    "status": "faculty_present|faculty_absent",
    "mac": "12:34:56:78:9A:BC", 
    "timestamp": 1234567890
  }
  ```
- Automatic BLE ID updates in database
- System notifications for MAC-based status changes

### 3. Backward Compatibility
- Legacy BLE server mode still available
- Existing MQTT topics continue to work
- Gradual migration path for existing deployments

### 4. Configuration Flexibility
- Easy MAC address configuration in code
- Adjustable detection parameters
- Runtime mode switching capability

## Testing and Validation

### 1. Test Script
**File: `scripts/test_mac_detection.py`**
- Monitors MQTT messages for MAC status updates
- Verifies database status changes
- Provides debug information for troubleshooting
- Real-time faculty status monitoring

### 2. Documentation
**File: `faculty_desk_unit/MAC_ADDRESS_DETECTION_README.md`**
- Comprehensive implementation guide
- Configuration instructions
- Troubleshooting information
- Testing procedures

## Configuration Example

### Faculty Desk Unit (config.h)
```cpp
#define BLE_DETECTION_MODE_MAC_ADDRESS true
#define MAC_DETECTION_TIMEOUT 30000
#define MAC_DETECTION_DEBOUNCE 3
```

### MAC Address Array (faculty_desk_unit.ino)
```cpp
const char* FACULTY_MAC_ADDRESSES[MAX_FACULTY_MAC_ADDRESSES] = {
  "11:22:33:44:55:66",  // Dr. John Smith
  "AA:BB:CC:DD:EE:FF",  // Dr. Jane Doe
  "4F:AF:C2:01:1F:B5",  // Prof. Robert Chen
  "12:34:56:78:9A:BC",  // Jeysibn (FACULTY_ID 3)
  ""                    // Empty slot
};
```

## Benefits

1. **Improved Reliability**: No connection pairing required
2. **Multi-Faculty Support**: Can detect multiple faculty members
3. **Automatic Configuration**: Updates database with detected MAC addresses
4. **Flexible Detection**: Configurable proximity and debouncing
5. **Backward Compatible**: Existing functionality preserved
6. **Easy Testing**: Comprehensive test tools provided

## Next Steps

1. **Deploy and Test**: Upload modified firmware to ESP32 desk unit
2. **Configure MAC Addresses**: Add actual faculty device MAC addresses
3. **Monitor Performance**: Use test script to verify detection accuracy
4. **Adjust Parameters**: Fine-tune detection settings based on environment
5. **Production Deployment**: Roll out to additional desk units

## Security Considerations

- MAC addresses transmitted in plain text over MQTT
- Modern devices may use MAC randomization
- Consider dedicated BLE beacons for production use
- Implement MQTT encryption for sensitive deployments

The implementation provides a robust, flexible, and backward-compatible solution for MAC address-based faculty detection while maintaining all existing functionality.
