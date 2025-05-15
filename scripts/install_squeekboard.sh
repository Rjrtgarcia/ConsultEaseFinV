#!/bin/bash

# Script to install required on-screen keyboard utilities for ConsultEase
# This should be run on the Raspberry Pi device
# Note: This script has been updated to prioritize squeekboard over onboard

echo "Installing on-screen keyboard utilities for ConsultEase..."

# Create scripts directory if it doesn't exist
mkdir -p "$(dirname "$0")"

# Update package lists
echo "Updating package lists..."
sudo apt update

# Try to install squeekboard (preferred)
echo "Attempting to install squeekboard..."
if sudo apt install -y squeekboard; then
    echo "Squeekboard installed successfully."
else
    echo "Squeekboard installation failed, trying alternative keyboards..."

    # Try to install onboard (alternative)
    if sudo apt install -y onboard; then
        echo "Onboard installed successfully as fallback."
    else
        echo "Onboard installation failed, trying matchbox-keyboard..."

        # Try to install matchbox-keyboard (fallback)
        if sudo apt install -y matchbox-keyboard; then
            echo "Matchbox-keyboard installed successfully as fallback."
        else
            echo "Failed to install any virtual keyboard. Touch input may be limited."
        fi
    fi
fi

# Install other touch-related utilities
echo "Installing additional touch utilities..."
sudo apt install -y xserver-xorg-input-evdev

# Configure environment for squeekboard
if command -v squeekboard > /dev/null; then
    echo "Configuring environment for squeekboard..."

    # Set environment variables for squeekboard
    echo "Setting up environment variables..."
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
EOF
    echo "Environment variables set for squeekboard."

    # Also add to .bashrc for immediate effect
    if ! grep -q "CONSULTEASE_KEYBOARD=squeekboard" ~/.bashrc; then
        echo "Adding environment variables to .bashrc..."
        cat >> ~/.bashrc << EOF

# ConsultEase keyboard environment variables
export GDK_BACKEND=wayland,x11
export QT_QPA_PLATFORM=wayland;xcb
export SQUEEKBOARD_FORCE=1
export CONSULTEASE_KEYBOARD=squeekboard
export MOZ_ENABLE_WAYLAND=1
export QT_IM_MODULE=wayland
export CLUTTER_IM_MODULE=wayland
EOF
    fi

    # Create keyboard toggle script
    echo "Creating keyboard toggle script..."
    cat > ~/keyboard-toggle.sh << EOF
#!/bin/bash
# Toggle squeekboard keyboard

# Check if squeekboard is visible
if dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible | grep -q "boolean true"; then
    # Hide squeekboard
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    echo "Squeekboard hidden"
else
    # Show squeekboard
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    echo "Squeekboard shown"
fi
EOF
    chmod +x ~/keyboard-toggle.sh

    # Create keyboard show script
    echo "Creating keyboard show script..."
    cat > ~/keyboard-show.sh << EOF
#!/bin/bash
# Force show squeekboard keyboard

# Make sure squeekboard is running
if ! pgrep -f squeekboard > /dev/null; then
    # Start squeekboard with environment variables
    SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &
    sleep 0.5
fi

# Show squeekboard
dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
echo "Squeekboard shown"
EOF
    chmod +x ~/keyboard-show.sh

    # Create keyboard hide script
    echo "Creating keyboard hide script..."
    cat > ~/keyboard-hide.sh << EOF
#!/bin/bash
# Force hide squeekboard keyboard

# Hide squeekboard
dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
echo "Squeekboard hidden"
EOF
    chmod +x ~/keyboard-hide.sh
fi

# Configure auto-start for onboard (if squeekboard is not available but onboard is)
if ! command -v squeekboard > /dev/null && command -v onboard > /dev/null; then
    echo "Squeekboard not found but onboard is available. Configuring onboard as fallback..."
    mkdir -p ~/.config/autostart
    cat > ~/.config/autostart/onboard-autostart.desktop << EOF
[Desktop Entry]
Type=Application
Name=Onboard
Exec=onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade
Comment=Flexible on-screen keyboard
EOF
    echo "Onboard configured for auto-start as fallback."

    # Create onboard configuration directory
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
    echo "Onboard configured with touch-friendly settings."
fi

# Create .env file for ConsultEase if it doesn't exist
if [ -d "../central_system" ]; then
    echo "Creating/updating .env file for ConsultEase..."
    if [ ! -f "../.env" ]; then
        cat > "../.env" << EOF
# ConsultEase Configuration
# Generated by install_squeekboard.sh on $(date)

# Keyboard Configuration
CONSULTEASE_KEYBOARD=squeekboard
SQUEEKBOARD_FORCE=1
EOF
    else
        # Update existing .env file
        if grep -q "CONSULTEASE_KEYBOARD=" "../.env"; then
            sed -i 's/CONSULTEASE_KEYBOARD=.*/CONSULTEASE_KEYBOARD=squeekboard/' "../.env"
        else
            echo "CONSULTEASE_KEYBOARD=squeekboard" >> "../.env"
        fi

        if grep -q "SQUEEKBOARD_FORCE=" "../.env"; then
            sed -i 's/SQUEEKBOARD_FORCE=.*/SQUEEKBOARD_FORCE=1/' "../.env"
        else
            echo "SQUEEKBOARD_FORCE=1" >> "../.env"
        fi

        if grep -q "SQUEEKBOARD_DISABLE=" "../.env"; then
            sed -i 's/SQUEEKBOARD_DISABLE=.*/SQUEEKBOARD_DISABLE=0/' "../.env"
        fi
    fi
fi

echo "Installation completed."
echo "You may need to reboot your Raspberry Pi for all changes to take effect."