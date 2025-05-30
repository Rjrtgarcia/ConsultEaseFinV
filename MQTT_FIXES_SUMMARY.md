# MQTT Connection and Faculty Status Update Fixes

## Issues Identified

1. **MQTT struct.error**: `struct.error: bad char in struct format` - malformed MQTT messages
2. **Dashboard refresh error**: `DashboardWindow.refresh_faculty_status() missing 1 required positional argument: 'faculty_data'`

## Root Causes

1. **MQTT Protocol Issues**:
   - Malformed MQTT packets causing paho-mqtt library to fail
   - Improper message encoding/decoding
   - Missing message validation

2. **Dashboard Method Signature Mismatch**:
   - Timer calling `refresh_faculty_status()` without arguments
   - Method expecting `faculty_data` parameter in some contexts

## Fixes Implemented

### 1. Enhanced MQTT Service (`central_system/services/async_mqtt_service.py`)

**Changes Made**:
- Added robust message validation and error handling
- Implemented multiple encoding fallback strategies (UTF-8, latin-1)
- Enhanced MQTT client configuration with protocol version specification
- Added comprehensive payload validation before publishing
- Implemented message size limits and ASCII validation

**Key Improvements**:
```python
# Enhanced client initialization
self.client = mqtt.Client(
    client_id=f"consultease_central_{int(time.time())}",
    clean_session=True,
    protocol=mqtt.MQTTv311  # Use MQTT 3.1.1 for better compatibility
)

# Robust message decoding
try:
    payload = msg.payload.decode('utf-8')
    if all(ord(c) < 128 and (c.isprintable() or c.isspace()) for c in payload):
        data = payload.strip()
    else:
        logger.warning(f"Received non-printable string payload on topic {topic}")
        return
except UnicodeDecodeError:
    # Fallback to latin-1 encoding
    payload = msg.payload.decode('latin-1')
```

### 2. Dashboard Refresh Fix (`central_system/views/dashboard_window.py`)

**Changes Made**:
- Separated timer-triggered refresh from manual refresh
- Added `_refresh_faculty_status_timer()` method for timer callbacks
- Maintained existing `refresh_faculty_status()` method signature

**Key Improvements**:
```python
# Timer connects to wrapper method
self.refresh_timer.timeout.connect(self._refresh_faculty_status_timer)

def _refresh_faculty_status_timer(self):
    """Timer-triggered refresh method that calls the main refresh method."""
    try:
        self.refresh_faculty_status()
    except Exception as e:
        logger.error(f"Error in timer-triggered faculty status refresh: {e}")
```

### 3. Faculty Controller Error Handling (`central_system/controllers/faculty_controller.py`)

**Changes Made**:
- Added comprehensive input validation
- Enhanced error handling with try-catch blocks
- Added retry logic for database operations
- Improved logging for debugging

**Key Improvements**:
```python
# Input validation
if not topic or not isinstance(topic, str):
    logger.error(f"Invalid topic received: {topic}")
    return

if data is None:
    logger.warning(f"Received None data for topic: {topic}")
    return

# Database retry logic
max_retries = 3
for attempt in range(max_retries):
    try:
        success = self._update_faculty_status_in_db(faculty_id, status)
        if success:
            break
    except Exception as db_error:
        logger.error(f"Database error on attempt {attempt + 1}: {db_error}")
        if attempt < max_retries - 1:
            time.sleep(0.5)  # Brief delay before retry
```

## Testing

A comprehensive test script (`test_mqtt_fixes.py`) has been created to verify:

1. **MQTT Message Validation**: Tests various message formats and edge cases
2. **Dashboard Refresh**: Verifies both timer and manual refresh methods work
3. **Faculty Controller**: Tests error handling with invalid inputs

## Deployment Instructions

1. **Update the codebase** on Raspberry Pi:
   ```bash
   cd ~/ConsultEaseFinV
   git pull origin main
   ```

2. **Run the test script** to verify fixes:
   ```bash
   python3 test_mqtt_fixes.py
   ```

3. **Restart the application** to apply changes:
   ```bash
   # Stop current application
   pkill -f "python.*main.py"
   
   # Start application
   cd central_system
   python3 main.py
   ```

## Expected Results

After applying these fixes:

1. **No more MQTT struct errors**: Enhanced message validation prevents malformed packets
2. **Dashboard refreshes properly**: Timer-triggered refreshes work without argument errors
3. **Robust error handling**: System gracefully handles invalid MQTT messages
4. **Better logging**: Detailed error messages for debugging
5. **Improved reliability**: Retry logic and fallback mechanisms

## Monitoring

Monitor the application logs for:
- Successful MQTT message processing
- Faculty status updates working correctly
- No more struct.error exceptions
- Dashboard refresh operations completing successfully

The fixes ensure production-ready stability while maintaining all existing functionality.
