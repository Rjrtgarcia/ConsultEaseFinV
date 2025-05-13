#!/bin/bash
# Direct keyboard launcher script for ConsultEase
# This script directly manages the on-screen keyboard without relying on systemd services
# Updated to prioritize onboard over squeekboard

# Function to check if a process is running
is_running() {
    pgrep -f "$1" >/dev/null
    return $?
}

# Function to show the keyboard
show_keyboard() {
    echo "Attempting to show keyboard..."

    # Try multiple methods to ensure the keyboard appears

    # Method 1: Check if onboard is available and start it (preferred)
    if command -v onboard &>/dev/null; then
        echo "Using onboard (preferred)..."

        # Check if onboard is already running
        if ! is_running "onboard"; then
            echo "Starting onboard..."
            # Kill any zombie processes first
            pkill -f onboard

            # Start onboard with appropriate options
            nohup onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade >/dev/null 2>&1 &

            # Set environment variables
            export ONBOARD_ENABLE_TOUCH=1
            export ONBOARD_XEMBED=1
        else
            echo "Onboard is already running"
        fi

        # Successfully started onboard
        return
    fi

    # Method 2: Try DBus for squeekboard if available
    if command -v dbus-send &>/dev/null; then
        echo "Using DBus method for squeekboard..."
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    fi

    # Method 3: Check if squeekboard is running, if not start it
    if command -v squeekboard &>/dev/null && ! is_running "squeekboard"; then
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

    # Method 4: Try alternative on-screen keyboards if no keyboard is running
    if ! is_running "onboard" && ! is_running "squeekboard"; then
        echo "No keyboard running, trying alternatives..."

        # Try to install onboard if not available
        if ! command -v onboard &>/dev/null; then
            echo "Onboard not found. Installing onboard..."
            sudo apt-get update
            sudo apt-get install -y onboard

            # Start it if installation succeeded
            if command -v onboard &>/dev/null; then
                echo "Starting newly installed onboard..."
                nohup onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade >/dev/null 2>&1 &
                return
            fi
        fi

        # Try matchbox-keyboard
        if command -v matchbox-keyboard &>/dev/null; then
            echo "Starting matchbox-keyboard..."
            nohup matchbox-keyboard >/dev/null 2>&1 &
        # Try florence
        elif command -v florence &>/dev/null; then
            echo "Starting florence..."
            nohup florence >/dev/null 2>&1 &
        # Last resort: try to install squeekboard
        elif ! command -v squeekboard &>/dev/null; then
            echo "No on-screen keyboard found. Installing squeekboard..."
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

    # Method 1: Kill onboard if running
    if is_running "onboard"; then
        echo "Killing onboard..."
        pkill -f onboard
    fi

    # Method 2: Try DBus for squeekboard if available
    if command -v dbus-send &>/dev/null; then
        echo "Using DBus method to hide squeekboard..."
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    fi

    # Method 3: Kill other keyboards if running
    if is_running "matchbox-keyboard"; then
        echo "Killing matchbox-keyboard..."
        pkill -f matchbox-keyboard
    fi

    if is_running "florence"; then
        echo "Killing florence..."
        pkill -f florence
    fi
}

# Function to toggle the keyboard
toggle_keyboard() {
    echo "Toggling keyboard..."

    # Method 1: Toggle onboard if available
    if command -v onboard &>/dev/null; then
        if is_running "onboard"; then
            echo "Onboard is running, hiding it..."
            hide_keyboard
        else
            echo "Onboard is not running, showing it..."
            show_keyboard
        fi
        return
    fi

    # Method 2: Toggle squeekboard via DBus if available
    if command -v dbus-send &>/dev/null; then
        if dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible | grep -q "boolean true"; then
            echo "Squeekboard is visible, hiding it..."
            hide_keyboard
        else
            echo "Squeekboard is not visible, showing it..."
            show_keyboard
        fi
        return
    fi

    # Method 3: Toggle other keyboards
    if is_running "matchbox-keyboard" || is_running "florence"; then
        echo "Alternative keyboard is running, hiding it..."
        hide_keyboard
    else
        echo "No keyboard is running, showing one..."
        show_keyboard
    fi
}

# Function to restart the keyboard
restart_keyboard() {
    echo "Restarting keyboard..."

    # Remember which keyboard was running
    onboard_was_running=0
    squeekboard_was_running=0

    if is_running "onboard"; then
        onboard_was_running=1
    fi

    if is_running "squeekboard"; then
        squeekboard_was_running=1
    fi

    # Kill any existing keyboard processes
    echo "Killing all keyboard processes..."
    pkill -f onboard
    pkill -f squeekboard
    pkill -f matchbox-keyboard
    pkill -f florence

    # Wait a moment
    sleep 1

    # Start the keyboard again, prioritizing what was running before
    if [ $onboard_was_running -eq 1 ]; then
        echo "Restarting onboard..."
        nohup onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade >/dev/null 2>&1 &
    elif [ $squeekboard_was_running -eq 1 ]; then
        echo "Restarting squeekboard..."
        SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland nohup squeekboard >/dev/null 2>&1 &

        # Try DBus again after starting
        if command -v dbus-send &>/dev/null; then
            sleep 1
            dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
        fi
    else
        # Start the keyboard using the standard method
        show_keyboard
    fi
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
