# ConsultEase - Active Context

## Current Focus
The application is now stable and fully functional after comprehensive bug fixing and feature enhancements. The focus has shifted to integration testing with hardware components and preparing for deployment. All core functionality is working properly, including RFID scanning, admin dashboard CRUD operations, database management, and system maintenance.

## Recent Changes
- **Enhanced Security**: Implemented bcrypt password hashing for admin accounts, replacing the less secure SHA-256 implementation.
- **Database Flexibility**: Added SQLite support for development and testing, while maintaining PostgreSQL compatibility for production.
- **CRUD Functionality**: Fixed issues with the admin dashboard CRUD operations for faculty and student management.
- **RFID Service Improvements**:
  - Enhanced callback management to prevent memory leaks
  - Improved error handling for different card types
  - Fixed student lookup to happen before notifying callbacks
- **MQTT Communication**: Improved error handling for network disconnections with exponential backoff for reconnection attempts.
- **UI Consistency**: Set the theme to light as specified in the technical context document.
- **Resource Management**: Implemented proper cleanup methods to ensure resources are released when no longer needed.
- **Database Management**: Added backup and restore functionality with support for both SQLite and PostgreSQL.
- **Error Handling**: Added comprehensive error handling throughout the application with informative error messages.

## Next Steps
- Conduct integration testing with the actual 13.56 MHz RFID reader.
- Begin integration testing with ESP32 Faculty Desk Unit.
- Implement TLS/SSL for MQTT communication.
- Finalize user guides and training materials.
- Prepare deployment scripts and procedures.
- Conduct user acceptance testing with faculty and students.

## Active Decisions and Considerations
- **UI Design Pattern**: Using PyQt5 with a modular design pattern separating models, views, and controllers (MVC).
- **UI Theme**: Using light theme (white/navy/gold) as specified in the technical context document.
- **Database Access**: Using SQLAlchemy ORM for database operations with support for both SQLite (development) and PostgreSQL (production).
- **Inter-device Communication**: Using MQTT as the backbone for communication between Central System and Faculty Desk Units with improved error handling.
- **Authentication Flow**: Two separate authentication paths - RFID for students and username/password for admins. Student RFID lookup happens earlier in the `RFIDService`.
- **Security**: Using bcrypt for password hashing with fallback for backward compatibility.
- **Thread Safety**: Using Qt's signal-slot mechanism to ensure thread-safe UI updates with proper callback management.
- **Deployment Strategy**: Automated setup scripts for the Raspberry Pi with fullscreen toggle (F11) and environment variable configuration.
- **Admin Interface**: Comprehensive dashboard with tabs for managing faculty, students, and system maintenance with complete CRUD functionality.
- **Database Management**: Backup and restore functionality with support for both SQLite and PostgreSQL.
- **Touch Optimization**: Enhanced UI elements with larger touch targets and optimized spacing.
- **Keyboard Integration**: Auto-showing virtual keyboard for text input fields (squeekboard).

## Learnings and Project Insights
- **Callback Management**: Asynchronous operations (like RFID reading) require careful handling of callbacks to prevent memory leaks and ensure proper registration/unregistration.
- **Hardware Interaction**: RFID readers require specific character mapping and handling based on the reader and card type. Providing manual input fallbacks is crucial for reliability.
- **Security Best Practices**: Using modern password hashing algorithms like bcrypt is essential for security. Always include fallback mechanisms for backward compatibility.
- **Database Flexibility**: Supporting multiple database backends (SQLite for development, PostgreSQL for production) provides flexibility and simplifies development.
- **Error Handling**: Comprehensive error handling with informative messages improves user experience and simplifies debugging.
- **Resource Management**: Proper cleanup of resources (especially in PyQt) is essential to prevent memory leaks and ensure application stability.
- **UI Consistency**: Maintaining a consistent UI theme and design language improves user experience and reduces confusion.
- **Testing Strategy**: Thorough testing of all components, especially those involving hardware interaction, is essential for reliability.
- **Documentation**: Keeping documentation up-to-date with the latest changes is crucial for maintainability and knowledge transfer.

## Important Patterns and Preferences

### Code Organization
- Python code follows PEP 8 style guide.
- Modular architecture with clear separation of concerns (models, views, controllers, services, utils).
- Proper error handling with informative error messages.
- Resource cleanup with destructors and cleanup methods.

### UI Patterns
- Consistent light theme styling applied via `BaseWindow` and stylesheets.
- Fullscreen toggle via F11 key.
- Manual input fallback provided for hardware-dependent features (RFID scan).
- Status indicators use consistent color coding (green for success, red for error).
- Confirmations required for destructive actions (delete, restore).
- Auto-appearing on-screen keyboard for text input.
- Informative error messages with suggestions for resolution.

### Database Patterns
- SQLAlchemy ORM for database operations.
- Support for both SQLite (development) and PostgreSQL (production).
- Backup and restore functionality with proper error handling.
- Default data creation for easier testing and development.

### Security Patterns
- Bcrypt password hashing for admin accounts.
- Fallback mechanisms for backward compatibility.
- Proper validation of user input.
- Secure credential storage.

### Naming Conventions
- CamelCase for class names.
- snake_case for variables and function names.
- UPPERCASE for constants.
- Descriptive names that reflect purpose.

### Testing and Debugging
- Comprehensive error logging.
- Simulation modes for hardware-dependent features.
- Manual input fallbacks for testing.
- Environment variable configuration for different environments.