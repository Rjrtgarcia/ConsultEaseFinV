#!/bin/bash

# Script to install required on-screen keyboard utilities for ConsultEase
# This should be run on the Raspberry Pi device

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
        echo "Onboard installed successfully."
    else
        echo "Onboard installation failed, trying matchbox-keyboard..."
        
        # Try to install matchbox-keyboard (fallback)
        if sudo apt install -y matchbox-keyboard; then
            echo "Matchbox-keyboard installed successfully."
        else
            echo "Failed to install any virtual keyboard. Touch input may be limited."
        fi
    fi
fi

# Install other touch-related utilities
echo "Installing additional touch utilities..."
sudo apt install -y xserver-xorg-input-evdev

# Configure auto-start for the keyboard (if using onboard)
if command -v onboard > /dev/null; then
    echo "Configuring onboard to auto-start..."
    mkdir -p ~/.config/autostart
    cat > ~/.config/autostart/onboard-autostart.desktop << EOF
[Desktop Entry]
Type=Application
Name=Onboard
Exec=onboard --size=small --layout=Phone
Comment=Flexible on-screen keyboard
EOF
    echo "Onboard configured for auto-start."
fi

echo "Installation completed."
echo "You may need to reboot your Raspberry Pi for all changes to take effect." 