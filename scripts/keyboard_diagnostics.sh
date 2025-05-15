#!/bin/bash
# Keyboard diagnostics script for ConsultEase
# This script checks the status of on-screen keyboard components
# and provides detailed diagnostic information

echo "ConsultEase Keyboard Diagnostics"
echo "==============================="
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to print section headers
print_section() {
    echo
    echo "=== $1 ==="
    echo
}

# Check system information
print_section "System Information"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "Distribution: $(lsb_release -ds 2>/dev/null || cat /etc/*release 2>/dev/null | head -n1 || echo "Unknown")"
echo "Kernel: $(uname -r)"

# Check environment variables
print_section "Environment Variables"
echo "CONSULTEASE_KEYBOARD: ${CONSULTEASE_KEYBOARD:-Not set}"
echo "SQUEEKBOARD_FORCE: ${SQUEEKBOARD_FORCE:-Not set}"
echo "GDK_BACKEND: ${GDK_BACKEND:-Not set}"
echo "QT_QPA_PLATFORM: ${QT_QPA_PLATFORM:-Not set}"
echo "DISPLAY: ${DISPLAY:-Not set}"
echo "WAYLAND_DISPLAY: ${WAYLAND_DISPLAY:-Not set}"

# Check installed keyboards
print_section "Installed Keyboards"

if command_exists squeekboard; then
    SQUEEKBOARD_PATH=$(which squeekboard)
    echo "✓ Squeekboard is installed at: $SQUEEKBOARD_PATH"
    echo "  Version: $(squeekboard --version 2>&1 || echo "Unknown")"
else
    echo "✗ Squeekboard is not installed"
fi

if command_exists onboard; then
    ONBOARD_PATH=$(which onboard)
    echo "✓ Onboard is installed at: $ONBOARD_PATH"
    echo "  Version: $(onboard --version 2>&1 | head -n1 || echo "Unknown")"
else
    echo "✗ Onboard is not installed"
fi

if command_exists matchbox-keyboard; then
    MATCHBOX_PATH=$(which matchbox-keyboard)
    echo "✓ Matchbox-keyboard is installed at: $MATCHBOX_PATH"
else
    echo "✗ Matchbox-keyboard is not installed"
fi

# Check systemd services
print_section "Systemd Services"

if command_exists systemctl; then
    # Check squeekboard service
    echo "Squeekboard Service:"
    if systemctl --user list-unit-files | grep -q squeekboard.service; then
        echo "  ✓ Service unit file exists"
        
        # Check if enabled
        if systemctl --user is-enabled squeekboard.service &>/dev/null; then
            echo "  ✓ Service is enabled"
        else
            echo "  ✗ Service is not enabled"
        fi
        
        # Check if active
        if systemctl --user is-active squeekboard.service &>/dev/null; then
            echo "  ✓ Service is active and running"
        else
            echo "  ✗ Service is not active"
            echo "  Status: $(systemctl --user is-active squeekboard.service 2>&1)"
        fi
        
        # Show service details
        echo
        echo "  Service details:"
        systemctl --user status squeekboard.service
    else
        echo "  ✗ Service unit file does not exist"
        
        # Check if we can find the service file
        SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
        if [ -f "$SYSTEMD_USER_DIR/squeekboard.service" ]; then
            echo "  ✓ Found service file at: $SYSTEMD_USER_DIR/squeekboard.service"
            echo "  Content:"
            cat "$SYSTEMD_USER_DIR/squeekboard.service"
        else
            echo "  ✗ No service file found in user directory"
        fi
    fi
else
    echo "Systemctl not found, cannot check services"
fi

# Check running processes
print_section "Running Processes"

echo "Squeekboard processes:"
ps aux | grep squeekboard | grep -v grep || echo "No squeekboard processes found"

echo
echo "Onboard processes:"
ps aux | grep onboard | grep -v grep || echo "No onboard processes found"

# Check DBus
print_section "DBus Status"

if command_exists dbus-send; then
    echo "✓ dbus-send is available"
    
    # Try to query squeekboard
    echo
    echo "Querying squeekboard via DBus:"
    dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible 2>&1 || echo "Failed to query squeekboard"
else
    echo "✗ dbus-send is not available"
fi

# Check configuration files
print_section "Configuration Files"

# Check environment.d
ENV_DIR="$HOME/.config/environment.d"
ENV_FILE="$ENV_DIR/consultease-keyboard.conf"

if [ -f "$ENV_FILE" ]; then
    echo "✓ Found environment file: $ENV_FILE"
    echo "Content:"
    cat "$ENV_FILE"
else
    echo "✗ No environment file found at: $ENV_FILE"
fi

# Check .env file
if [ -f ".env" ]; then
    echo
    echo "✓ Found .env file in current directory"
    echo "Keyboard-related content:"
    grep -i "keyboard\|squeekboard\|onboard" .env || echo "No keyboard settings found in .env"
else
    echo
    echo "✗ No .env file found in current directory"
fi

# Check utility scripts
print_section "Utility Scripts"

SHOW_SCRIPT="$HOME/keyboard-show.sh"
HIDE_SCRIPT="$HOME/keyboard-hide.sh"
TOGGLE_SCRIPT="$HOME/keyboard-toggle.sh"

if [ -f "$SHOW_SCRIPT" ]; then
    echo "✓ Found keyboard show script: $SHOW_SCRIPT"
    echo "  Permissions: $(ls -l "$SHOW_SCRIPT" | awk '{print $1}')"
else
    echo "✗ No keyboard show script found"
fi

if [ -f "$HIDE_SCRIPT" ]; then
    echo "✓ Found keyboard hide script: $HIDE_SCRIPT"
    echo "  Permissions: $(ls -l "$HIDE_SCRIPT" | awk '{print $1}')"
else
    echo "✗ No keyboard hide script found"
fi

if [ -f "$TOGGLE_SCRIPT" ]; then
    echo "✓ Found keyboard toggle script: $TOGGLE_SCRIPT"
    echo "  Permissions: $(ls -l "$TOGGLE_SCRIPT" | awk '{print $1}')"
else
    echo "✗ No keyboard toggle script found"
fi

# Final recommendations
print_section "Recommendations"

if ! command_exists squeekboard; then
    echo "1. Install squeekboard: sudo apt install squeekboard"
fi

if ! systemctl --user list-unit-files | grep -q squeekboard.service; then
    echo "2. Create squeekboard service file using the fix_squeekboard.sh script"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "3. Set up environment variables for squeekboard"
fi

if [ ! -f "$SHOW_SCRIPT" ] || [ ! -f "$HIDE_SCRIPT" ]; then
    echo "4. Create keyboard utility scripts using the fix_squeekboard.sh script"
fi

echo
echo "To fix all issues automatically, run: ./scripts/fix_squeekboard.sh"
echo
echo "Diagnostics completed!"
