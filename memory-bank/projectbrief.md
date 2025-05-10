# ConsultEase - Project Brief

## Overview
ConsultEase is a comprehensive student-faculty interaction system designed to streamline consultation requests and faculty availability management. The system consists of two main components:

1. **Central System** (Raspberry Pi with PyQt UI)
2. **Faculty Desk Unit** (ESP32-based)

## Core Requirements

### Central System
- RFID-based student authentication
- Real-time faculty availability display
- Consultation request management
- Admin interface for faculty information management
- Touchscreen-optimized UI
- PostgreSQL database integration
- MQTT communication

### Faculty Desk Unit
- Display consultation requests
- Real-time status updates
- BLE-based faculty presence detection
- MQTT integration with Central System

## Hardware Components
- Raspberry Pi 4 (Bookworm 64-bit)
- ESP32
- 10.1-inch touchscreen (1024x600 resolution)
- USB RFID IC Reader
- 2.4-inch TFT SPI Screen (ST7789)

## Target Users
- Students: Request consultations with faculty
- Faculty: Manage their availability status
- Administrators: Manage faculty information

## Project Goals
- Create an intuitive, responsive UI for student interaction
- Implement secure admin functionality
- Develop reliable faculty presence detection
- Ensure real-time communication between system components
- Build a robust, maintainable codebase with comprehensive documentation 