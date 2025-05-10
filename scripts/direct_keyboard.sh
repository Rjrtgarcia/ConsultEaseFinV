#!/bin/bash
# Direct keyboard launcher script for ConsultEase
# This script directly manages the on-screen keyboard without relying on systemd services

# Function to check if a process is running
is_running() {
    pgrep -f "$1" >/dev/null
    return $?
}

# Function to show the keyboard
show_keyboard() {
    echo "Attempting to show keyboard..."
    
    # Try multiple methods to ensure the keyboard appears
    
    # Method 1: Try DBus if available
    if command -v dbus-send &>/dev/null; then
        echo "Using DBus method..."
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    fi
    
    # Method 2: Check if squeekboard is running, if not start it
    if ! is_running "squeekboard"; then
        echo "Squeekboard not running, starting it..."
        # Kill any zombie processes first
        pkill -f squeekboard
        
        # Start squeekboard with environment variables
        SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland nohup squeekboard >/dev/null 2>&1 &
        
        # Give it a moment to start
        sleep 1
        
        # Try DBus again after starting
        if command -v dbus-send &>/dev/null; then
            dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
        fi
    fi
    
    # Method 3: Try alternative on-screen keyboards if squeekboard fails
    if ! is_running "squeekboard"; then
        echo "Trying alternative keyboards..."
        
        # Try onboard
        if command -v onboard &>/dev/null; then
            echo "Starting onboard..."
            nohup onboard --size=small --layout=Phone >/dev/null 2>&1 &
        # Try matchbox-keyboard
        elif command -v matchbox-keyboard &>/dev/null; then
            echo "Starting matchbox-keyboard..."
            nohup matchbox-keyboard >/dev/null 2>&1 &
        # Try florence
        elif command -v florence &>/dev/null; then
            echo "Starting florence..."
            nohup florence >/dev/null 2>&1 &
        else
            echo "No on-screen keyboard found. Installing squeekboard..."
            # Try to install squeekboard
            sudo apt-get update
            sudo apt-get install -y squeekboard
            
            # Start it if installation succeeded
            if command -v squeekboard &>/dev/null; then
                SQUEEKBOARD_FORCE=1 nohup squeekboard >/dev/null 2>&1 &
                sleep 1
                if command -v dbus-send &>/dev/null; then
                    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
                fi
            fi
        fi
    fi
}

# Function to hide the keyboard
hide_keyboard() {
    echo "Hiding keyboard..."
    
    # Try DBus if available
    if command -v dbus-send &>/dev/null; then
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    fi
}

# Function to toggle the keyboard
toggle_keyboard() {
    echo "Toggling keyboard..."
    
    # Check if keyboard is visible
    if command -v dbus-send &>/dev/null; then
        if dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible | grep -q "boolean true"; then
            hide_keyboard
        else
            show_keyboard
        fi
    else
        # If we can't check, just try to show it
        show_keyboard
    fi
}

# Function to restart the keyboard
restart_keyboard() {
    echo "Restarting keyboard..."
    
    # Kill any existing keyboard processes
    pkill -f squeekboard
    pkill -f onboard
    pkill -f matchbox-keyboard
    pkill -f florence
    
    # Wait a moment
    sleep 1
    
    # Start the keyboard again
    show_keyboard
}

# Main script logic
case "$1" in
    show)
        show_keyboard
        ;;
    hide)
        hide_keyboard
        ;;
    toggle)
        toggle_keyboard
        ;;
    restart)
        restart_keyboard
        ;;
    *)
        echo "Usage: $0 {show|hide|toggle|restart}"
        echo "  show    - Show the on-screen keyboard"
        echo "  hide    - Hide the on-screen keyboard"
        echo "  toggle  - Toggle keyboard visibility"
        echo "  restart - Restart the keyboard service"
        exit 1
        ;;
esac

exit 0
