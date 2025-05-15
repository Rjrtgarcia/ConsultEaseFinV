# BLE Functionality Update Instructions

This document provides instructions for updating the ConsultEase system to remove the "always on" functionality for faculty consultation availability and fix BLE connection issues.

## Overview of Changes

1. **Removed "Always On" Functionality**:
   - Modified the faculty controller to respect BLE connection status for all faculty members.
   - Removed code that kept faculty members permanently available regardless of BLE connection status.
   - Updated the database to set `always_available` to False for all faculty members.

2. **Fixed UUID Configuration**:
   - Updated the UUIDs in the faculty desk unit's Arduino file to match the BLE beacon's UUIDs.
   - Updated the faculty's BLE ID in the database to match the BLE beacon's UUID.

## Applying the Changes

### 1. Update the Faculty Desk Unit

1. Connect the faculty desk unit to your computer.
2. Open the Arduino IDE.
3. Open the `faculty_desk_unit.ino` file.
4. Verify that the BLE UUIDs match the BLE beacon's UUIDs:
   ```c
   // BLE UUIDs
   #define SERVICE_UUID        "91BAD35B-F3CB-4FC1-8603-88D5137892A6"
   #define CHARACTERISTIC_UUID "D9473AA3-E6F4-424B-B6E7-A5F94FDDA285"
   ```
5. Compile and upload the code to the faculty desk unit.

### 2. Update the Central System

1. Run the script to update the faculty's BLE ID in the database:
   ```bash
   python scripts/update_faculty_ble_id.py
   ```

2. Run the script to update the `always_available` flag for all faculty members:
   ```bash
   python scripts/update_faculty_always_available.py
   ```

3. Restart the central system:
   ```bash
   python central_system/main.py
   ```

## Testing the Changes

1. **Test BLE Connection**:
   - Bring the BLE beacon close to the faculty desk unit.
   - Verify that the faculty desk unit detects the BLE beacon and displays "Keychain connected".
   - Verify that the central system updates the faculty's status to "Available".
   - Move the BLE beacon away from the faculty desk unit.
   - Verify that the faculty desk unit detects the BLE beacon disconnection and displays "Keychain disconnected".
   - Verify that the central system updates the faculty's status to "Unavailable".

2. **Test Faculty Status Updates**:
   - Log in to the admin dashboard.
   - Verify that the faculty's status is correctly displayed based on the BLE connection status.
   - Verify that the "Always Available" flag is set to "No" for all faculty members.

## Troubleshooting

If the BLE connection is still not working correctly, check the following:

1. **BLE Beacon Battery**: Make sure the BLE beacon has sufficient battery power.
2. **BLE Beacon Proximity**: Make sure the BLE beacon is within range of the faculty desk unit.
3. **BLE UUIDs**: Verify that the UUIDs in the faculty desk unit's Arduino file match the BLE beacon's UUIDs.
4. **Faculty BLE ID**: Verify that the faculty's BLE ID in the database matches the BLE beacon's UUID.
5. **MQTT Connection**: Verify that the faculty desk unit is connected to the MQTT broker.
6. **Central System Logs**: Check the central system logs for any errors related to BLE connection status updates.

## Additional Notes

- The "always on" functionality has been completely removed from the system.
- Faculty availability is now solely determined by the physical presence of the BLE beacon.
- The admin dashboard still shows the "Always Available" column, but it is no longer functional.
- Future updates may remove the "Always Available" column from the admin dashboard.
