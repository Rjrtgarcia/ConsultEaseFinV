#!/bin/bash
# ConsultEase Unified Keyboard Setup Script
# This script consolidates all keyboard-related setup into a single script
# It supports both squeekboard and onboard with automatic fallback

# Set script to exit on error
set -e

# Print header
echo "ConsultEase Keyboard Setup"
echo "=========================="
echo "This script will set up the on-screen keyboard for ConsultEase."
echo

# Function to detect the current desktop environment
detect_desktop_environment() {
    if [ -n "$XDG_CURRENT_DESKTOP" ]; then
        echo "$XDG_CURRENT_DESKTOP"
    elif [ -n "$DESKTOP_SESSION" ]; then
        echo "$DESKTOP_SESSION"
    elif [ -n "$GDMSESSION" ]; then
        echo "$GDMSESSION"
    else
        # Try to detect based on running processes
        if pgrep -f "gnome-shell" > /dev/null; then
            echo "GNOME"
        elif pgrep -f "plasmashell" > /dev/null; then
            echo "KDE"
        elif pgrep -f "xfce4-session" > /dev/null; then
            echo "XFCE"
        elif pgrep -f "lxsession" > /dev/null; then
            echo "LXDE"
        elif pgrep -f "mate-session" > /dev/null; then
            echo "MATE"
        elif pgrep -f "cinnamon" > /dev/null; then
            echo "Cinnamon"
        elif pgrep -f "phosh" > /dev/null; then
            echo "Phosh"
        else
            echo "Unknown"
        fi
    fi
}

# Function to install keyboard packages
install_keyboard() {
    local keyboard_type=$1
    local fallback=$2

    echo "Attempting to install $keyboard_type..."
    if sudo apt update && sudo apt install -y $keyboard_type; then
        echo "✓ $keyboard_type installed successfully."
        return 0
    else
        echo "✗ $keyboard_type installation failed."
        if [ -n "$fallback" ]; then
            echo "Trying fallback keyboard: $fallback..."
            if sudo apt install -y $fallback; then
                echo "✓ $fallback installed successfully as fallback."
                return 1  # Return 1 to indicate fallback was used
            else
                echo "✗ $fallback installation failed."
                return 2  # Return 2 to indicate both failed
            fi
        else
            return 2  # Return 2 to indicate failure with no fallback
        fi
    fi
}

# Function to configure environment for squeekboard
configure_squeekboard() {
    echo "Configuring environment for squeekboard..."

    # Set environment variables
    mkdir -p ~/.config/environment.d/
    cat > ~/.config/environment.d/consultease-keyboard.conf << EOF
# ConsultEase keyboard environment variables
GDK_BACKEND=wayland,x11
QT_QPA_PLATFORM=wayland;xcb
SQUEEKBOARD_FORCE=1
CONSULTEASE_KEYBOARD=squeekboard
MOZ_ENABLE_WAYLAND=1
QT_IM_MODULE=wayland
CLUTTER_IM_MODULE=wayland
# Disable onboard
ONBOARD_DISABLE=1
EOF

    # Add to .bashrc for immediate effect
    if ! grep -q "CONSULTEASE_KEYBOARD=squeekboard" ~/.bashrc; then
        echo "Adding environment variables to .bashrc..."
        cat >> ~/.bashrc << EOF

# ConsultEase keyboard environment variables
export GDK_BACKEND=wayland,x11
export QT_QPA_PLATFORM="wayland;xcb"
export SQUEEKBOARD_FORCE=1
export CONSULTEASE_KEYBOARD=squeekboard
export MOZ_ENABLE_WAYLAND=1
export QT_IM_MODULE=wayland
export CLUTTER_IM_MODULE=wayland
# Disable onboard
export ONBOARD_DISABLE=1
EOF
    fi

    echo "✓ Environment configured for squeekboard."
}

# Function to configure environment for onboard
configure_onboard() {
    echo "Configuring environment for onboard..."

    # Set environment variables
    mkdir -p ~/.config/environment.d/
    cat > ~/.config/environment.d/consultease-keyboard.conf << EOF
# ConsultEase keyboard environment variables
GDK_BACKEND=wayland,x11
QT_QPA_PLATFORM=wayland;xcb
ONBOARD_ENABLE_TOUCH=1
ONBOARD_XEMBED=1
CONSULTEASE_KEYBOARD=onboard
# Disable squeekboard
SQUEEKBOARD_DISABLE=1
EOF

    # Add to .bashrc for immediate effect
    if ! grep -q "CONSULTEASE_KEYBOARD=onboard" ~/.bashrc; then
        echo "Adding environment variables to .bashrc..."
        cat >> ~/.bashrc << EOF

# ConsultEase keyboard environment variables
export GDK_BACKEND=wayland,x11
export QT_QPA_PLATFORM=wayland;xcb
export ONBOARD_ENABLE_TOUCH=1
export ONBOARD_XEMBED=1
export CONSULTEASE_KEYBOARD=onboard
# Disable squeekboard
export SQUEEKBOARD_DISABLE=1
EOF
    fi

    # Create onboard configuration directory if it doesn't exist
    mkdir -p ~/.config/onboard

    # Create onboard configuration file with touch-friendly settings
    cat > ~/.config/onboard/onboard.conf << EOF
[main]
layout=Phone
theme=Nightshade
key-size=small
enable-background-transparency=true
show-status-icon=true
start-minimized=false
show-tooltips=false
auto-show=true
auto-show-delay=500
auto-hide=true
auto-hide-delay=1000
xembed-onboard=true
enable-touch-input=true
touch-feedback-enabled=true
touch-feedback-size=small
EOF

    echo "✓ Environment configured for onboard."
}

# Function to create keyboard toggle scripts
create_keyboard_scripts() {
    local keyboard_type=$1

    echo "Creating keyboard toggle scripts..."

    # Create keyboard toggle script
    cat > ~/keyboard-toggle.sh << EOF
#!/bin/bash
# Toggle $keyboard_type keyboard

if [ "$keyboard_type" = "squeekboard" ]; then
    # Toggle squeekboard using DBus
    if command -v dbus-send &> /dev/null; then
        # Check current state
        if dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible | grep -q "boolean true"; then
            # Hide keyboard
            dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
            echo "Squeekboard hidden"
        else
            # Show keyboard
            dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
            echo "Squeekboard shown"
        fi
    else
        echo "DBus not available, cannot toggle squeekboard"
    fi
elif [ "$keyboard_type" = "onboard" ]; then
    # Toggle onboard
    if pgrep -f onboard > /dev/null; then
        pkill -f onboard
        echo "Onboard keyboard hidden"
    else
        onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade &
        echo "Onboard keyboard shown"
    fi
fi
EOF
    chmod +x ~/keyboard-toggle.sh

    # Create keyboard show script
    cat > ~/keyboard-show.sh << EOF
#!/bin/bash
# Force show $keyboard_type keyboard

if [ "$keyboard_type" = "squeekboard" ]; then
    # Try multiple methods to ensure squeekboard is shown

    # First ensure squeekboard is running
    if ! pgrep -f squeekboard > /dev/null; then
        echo "Squeekboard not running, starting it..."
        # Set up environment variables
        export SQUEEKBOARD_FORCE=1
        export GDK_BACKEND=wayland,x11
        export QT_QPA_PLATFORM=wayland;xcb

        # Start squeekboard
        squeekboard &
        sleep 0.5
    fi

    # Method 1: Standard DBus call
    if command -v dbus-send &> /dev/null; then
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
        echo "Squeekboard shown via standard DBus call"
    else
        echo "DBus not available, cannot show squeekboard via standard method"
    fi

    # Method 2: Try with session bus explicitly
    if command -v dbus-send &> /dev/null; then
        dbus-send --session --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
        echo "Squeekboard shown via session DBus call"
    fi

    # Method 3: Try with print-reply to see any errors
    if command -v dbus-send &> /dev/null; then
        dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
        echo "Squeekboard shown via print-reply DBus call"
    fi
elif [ "$keyboard_type" = "onboard" ]; then
    # Show onboard
    if ! pgrep -f onboard > /dev/null; then
        onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade &
        echo "Onboard keyboard shown"
    else
        echo "Onboard keyboard already running"
    fi
fi
EOF
    chmod +x ~/keyboard-show.sh

    # Create keyboard hide script
    cat > ~/keyboard-hide.sh << EOF
#!/bin/bash
# Force hide $keyboard_type keyboard

if [ "$keyboard_type" = "squeekboard" ]; then
    # Hide squeekboard using DBus
    if command -v dbus-send &> /dev/null; then
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
        echo "Squeekboard hidden"
    else
        echo "DBus not available, cannot hide squeekboard"
    fi
elif [ "$keyboard_type" = "onboard" ]; then
    # Hide onboard
    if pgrep -f onboard > /dev/null; then
        pkill -f onboard
        echo "Onboard keyboard hidden"
    else
        echo "Onboard keyboard not running"
    fi
fi
EOF
    chmod +x ~/keyboard-hide.sh

    echo "✓ Keyboard toggle scripts created."
}

# Function to update ConsultEase .env file
update_env_file() {
    local keyboard_type=$1

    # Find the ConsultEase directory
    local consultease_dir=""
    if [ -d "central_system" ]; then
        consultease_dir="."
    elif [ -d "../central_system" ]; then
        consultease_dir=".."
    else
        echo "⚠ ConsultEase directory not found, skipping .env file update."
        return
    fi

    echo "Creating/updating .env file for ConsultEase..."

    # Create or update .env file
    if [ ! -f "$consultease_dir/.env" ]; then
        cat > "$consultease_dir/.env" << EOF
# ConsultEase Configuration
# Generated by keyboard_setup.sh on $(date)

# Keyboard Configuration
CONSULTEASE_KEYBOARD=$keyboard_type
EOF
        if [ "$keyboard_type" = "squeekboard" ]; then
            echo "ONBOARD_DISABLE=1" >> "$consultease_dir/.env"
        else
            echo "SQUEEKBOARD_DISABLE=1" >> "$consultease_dir/.env"
        fi
    else
        # Update existing .env file
        if grep -q "CONSULTEASE_KEYBOARD=" "$consultease_dir/.env"; then
            sed -i "s/CONSULTEASE_KEYBOARD=.*/CONSULTEASE_KEYBOARD=$keyboard_type/" "$consultease_dir/.env"
        else
            echo "CONSULTEASE_KEYBOARD=$keyboard_type" >> "$consultease_dir/.env"
        fi

        if [ "$keyboard_type" = "squeekboard" ]; then
            if grep -q "ONBOARD_DISABLE=" "$consultease_dir/.env"; then
                sed -i "s/ONBOARD_DISABLE=.*/ONBOARD_DISABLE=1/" "$consultease_dir/.env"
            else
                echo "ONBOARD_DISABLE=1" >> "$consultease_dir/.env"
            fi
            if grep -q "SQUEEKBOARD_DISABLE=" "$consultease_dir/.env"; then
                sed -i "s/SQUEEKBOARD_DISABLE=.*/SQUEEKBOARD_DISABLE=0/" "$consultease_dir/.env"
            else
                echo "SQUEEKBOARD_DISABLE=0" >> "$consultease_dir/.env"
            fi
        else
            if grep -q "SQUEEKBOARD_DISABLE=" "$consultease_dir/.env"; then
                sed -i "s/SQUEEKBOARD_DISABLE=.*/SQUEEKBOARD_DISABLE=1/" "$consultease_dir/.env"
            else
                echo "SQUEEKBOARD_DISABLE=1" >> "$consultease_dir/.env"
            fi
            if grep -q "ONBOARD_DISABLE=" "$consultease_dir/.env"; then
                sed -i "s/ONBOARD_DISABLE=.*/ONBOARD_DISABLE=0/" "$consultease_dir/.env"
            else
                echo "ONBOARD_DISABLE=0" >> "$consultease_dir/.env"
            fi
        fi
    fi

    echo "✓ ConsultEase .env file updated."
}

# Main script execution starts here

# Detect desktop environment
desktop=$(detect_desktop_environment)
echo "Detected desktop environment: $desktop"

# Determine preferred keyboard based on desktop environment
preferred_keyboard="squeekboard"
fallback_keyboard="onboard"

# For Phosh (mobile-friendly) environments, prefer squeekboard
# For traditional desktop environments, prefer onboard
if [[ "$desktop" == *"GNOME"* ]] || [[ "$desktop" == *"KDE"* ]] || [[ "$desktop" == *"XFCE"* ]]; then
    preferred_keyboard="onboard"
    fallback_keyboard="squeekboard"
fi

echo "Preferred keyboard: $preferred_keyboard"
echo "Fallback keyboard: $fallback_keyboard"

# Install preferred keyboard with fallback
result=$(install_keyboard $preferred_keyboard $fallback_keyboard)
keyboard_type=$preferred_keyboard

if [ "$result" -eq 1 ]; then
    # Fallback was used
    keyboard_type=$fallback_keyboard
    echo "Using fallback keyboard: $keyboard_type"
elif [ "$result" -eq 2 ]; then
    # Both failed, try matchbox as last resort
    echo "Trying matchbox-keyboard as last resort..."
    if sudo apt install -y matchbox-keyboard; then
        keyboard_type="matchbox-keyboard"
        echo "✓ Matchbox-keyboard installed as last resort."
    else
        echo "✗ Failed to install any virtual keyboard. Touch input may be limited."
        exit 1
    fi
fi

# Configure environment for the selected keyboard
if [ "$keyboard_type" = "squeekboard" ]; then
    configure_squeekboard
elif [ "$keyboard_type" = "onboard" ]; then
    configure_onboard
fi

# Create keyboard toggle scripts
create_keyboard_scripts $keyboard_type

# Update ConsultEase .env file
update_env_file $keyboard_type

echo
echo "Keyboard setup complete!"
echo "Selected keyboard: $keyboard_type"
echo
echo "You can toggle the keyboard with: ~/keyboard-toggle.sh"
echo "You can show the keyboard with: ~/keyboard-show.sh"
echo "You can hide the keyboard with: ~/keyboard-hide.sh"
echo
echo "Please log out and log back in for all settings to take effect."
