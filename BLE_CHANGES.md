# BLE Functionality Changes

This document outlines the changes made to the BLE functionality in the ConsultEase system.

## Overview

The "Always Available" mode has been removed from the system. Faculty availability is now solely determined by BLE connection status. This change makes the system more reliable and consistent, as faculty status will always reflect their actual presence as detected by BLE.

## Changes Made

### 1. Faculty Desk Unit

#### 1.1 Configuration

- Updated `config.h` to set `ALWAYS_AVAILABLE` to `false`
- This ensures that faculty availability is determined by BLE connection status

#### 1.2 BLE Connection Handling

- Modified the BLE connection handling logic to always update faculty status based on BLE connection
- Removed conditional checks for `alwaysAvailable` flag
- Simplified status update messages and UI notifications

#### 1.3 Status Updates

- Updated periodic status updates to only consider BLE connection status
- Removed references to "Always Available" mode in status messages
- Simplified UI status display

### 2. Central System

#### 2.1 Faculty Model

- Kept the `always_available` field in the database for backward compatibility
- Added migration script to set `always_available=false` for all faculty members

#### 2.2 Faculty Controller

- Updated `update_faculty_status` method to always update status based on BLE connection
- Removed conditional checks for `always_available` flag
- Modified `add_faculty` and `update_faculty` methods to always set `always_available=false`
- Updated documentation to mark `always_available` parameter as deprecated

#### 2.3 Database Migration

- Created `db_migration.py` script to update all faculty members to set `always_available=false`
- Created `remove_always_available.py` script to remove the "Always Available" mode from all faculty members

#### 2.4 Jeysibn Faculty Update

- Updated `update_jeysibn_faculty.py` script to not set `always_available=true`
- Modified the script to use BLE for availability instead of "Always Available" mode

## How to Apply These Changes

1. Update the faculty desk unit configuration:
   ```
   # In faculty_desk_unit/config.h
   #define ALWAYS_AVAILABLE false
   ```

2. Flash the updated firmware to the faculty desk unit

3. Run the database migration script:
   ```
   python scripts/db_migration.py
   ```

4. Run the script to remove "Always Available" mode:
   ```
   python scripts/remove_always_available.py
   ```

5. Update the Jeysibn faculty:
   ```
   python scripts/update_jeysibn_faculty.py
   ```

## Testing

After applying these changes, test the system to ensure:

1. Faculty status correctly changes when BLE connection is established or lost
2. The faculty desk unit displays the correct status messages
3. The central system correctly updates faculty status in the database
4. The admin dashboard correctly displays faculty status
5. Students can only request consultations with faculty who are physically present (BLE connected)

## Troubleshooting

If you encounter issues with faculty status not updating correctly:

1. Check the BLE connection between the faculty desk unit and the BLE beacon
2. Verify that the faculty desk unit is publishing status updates to the correct MQTT topics
3. Check the MQTT broker logs to ensure messages are being received
4. Verify that the central system is subscribed to the correct MQTT topics
5. Check the database to ensure faculty status is being updated correctly

## Conclusion

These changes simplify the system by removing the "Always Available" mode and making faculty availability solely dependent on BLE connection status. This makes the system more reliable and consistent, as faculty status will always reflect their actual presence as detected by BLE.
