# ConsultEase - System Patterns

## System Architecture

### High-Level Architecture
```
┌─────────────────────────┐      MQTT      ┌───────────────────┐
│    Central System       │◄──────────────►│  Faculty Desk Unit │
│    (Raspberry Pi)       │                │     (ESP32)        │
└─────────────┬───────────┘                └───────────────────┘
              │
              │ SQL
              ▼
┌─────────────────────────┐
│      Database           │
│    (PostgreSQL)         │
└─────────────────────────┘
```

### Central System Architecture (PyQt)

```
┌─────────────────────────────────────────────────────┐
│                   UI Layer                           │
├─────────────┬───────────────┬───────────────────────┤
│ Login/RFID  │  Dashboard    │ Admin Interface       │
│  Screen     │               │                       │
└─────┬───────┴───────┬───────┴───────────────┬───────┘
      │               │                       │
┌─────▼───────┬───────▼───────┐       ┌───────▼───────┐
│ RFID        │ Consultation  │       │ Faculty       │
│ Controller  │ Controller    │       │ Management    │
└─────┬───────┴───────┬───────┘       └───────┬───────┘
      │               │                       │
┌─────▼───────────────▼───────────────────────▼───────┐
│                   Service Layer                      │
├─────────────┬───────────────┬───────────────────────┤
│ Database    │ MQTT          │ Authentication        │
│ Service     │ Service       │ Service               │
└─────────────┴───────────────┴───────────────────────┘
```

### Faculty Desk Unit Architecture (ESP32)

```
┌─────────────────────────┐
│     Display Controller  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│     Main Controller     │
├─────────────┬───────────┤
│  BLE        │  MQTT     │
│  Scanner    │  Client   │
└─────────────┴───────────┘
```

## Design Patterns

### Central System
1. **Model-View-Controller (MVC)**
   - Models: Faculty, Student, Consultation
   - Views: Login, Dashboard, Admin Interface
   - Controllers: RFID, Consultation, Faculty Management

2. **Observer Pattern**
   - MQTT service subscribes to updates
   - UI components observe model changes

3. **Singleton Pattern**
   - Database connection
   - MQTT client

4. **Factory Pattern**
   - UI screen creation
   - Database model creation

### Faculty Desk Unit
1. **State Pattern**
   - Faculty presence states (Present, Unavailable)
   - Connection states (Connected, Disconnecting, Reconnecting)

2. **Command Pattern**
   - Display update commands
   - MQTT publish commands

## Data Flow

### Student Consultation Request Flow
1. Student scans RFID at Central System
2. System validates student ID in database
3. Student selects faculty and submits consultation request
4. Request is stored in database
5. Request is published via MQTT
6. Faculty Desk Unit receives request and displays it
7. Faculty returns (BLE beacon detected)
8. Faculty Desk Unit updates status to "Present"
9. Status change is published via MQTT
10. Central System updates faculty status display

### Faculty Presence Detection Flow
1. Faculty BLE beacon is detected by ESP32
2. Faculty Desk Unit updates local status display
3. Status change is published via MQTT
4. Central System receives update
5. Database is updated with new status
6. Dashboard UI refreshes to show current status

## Critical Implementation Paths

1. **RFID Authentication**
   - RFID reader integration with Raspberry Pi
   - Student validation against database
   - Error handling for failed reads

2. **BLE Presence Detection**
   - Reliable beacon scanning on ESP32
   - Configurable detection thresholds
   - Status transition logic
   - Battery management for faculty beacons
   - LED indicators for beacon status and battery level

3. **MQTT Communication**
   - Reliable message passing between components
   - Reconnection logic
   - Message format standardization

4. **Real-time UI Updates**
   - Thread-safe UI operations
   - Asynchronous data loading
   - Responsive feedback mechanisms

5. **User Documentation**
   - Quick Start Guide for new users
   - BLE Beacon maintenance instructions for faculty
   - Technical specifications for administrators
   - Troubleshooting procedures for common issues 