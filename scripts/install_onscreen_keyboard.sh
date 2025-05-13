#!/bin/bash

# Script to install required on-screen keyboard utilities for ConsultEase
# This should be run on the Raspberry Pi device
# Note: This script prioritizes onboard over squeekboard

echo "Installing on-screen keyboard utilities for ConsultEase..."

# Create scripts directory if it doesn't exist
mkdir -p "$(dirname "$0")"

# Update package lists
echo "Updating package lists..."
sudo apt update

# Try to install onboard (preferred)
echo "Attempting to install onboard..."
if sudo apt install -y onboard; then
    echo "Onboard installed successfully."
else
    echo "Onboard installation failed, trying alternative keyboards..."
    
    # Try to install squeekboard (alternative)
    if sudo apt install -y squeekboard; then
        echo "Squeekboard installed successfully."
    else
        echo "Squeekboard installation failed, trying matchbox-keyboard..."
        
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
Exec=onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade
Comment=Flexible on-screen keyboard
EOF
    echo "Onboard configured for auto-start."
    
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
    
    # Set environment variables for onboard
    echo "Setting up environment variables for onboard..."
    mkdir -p ~/.config/environment.d/
    cat > ~/.config/environment.d/consultease-keyboard.conf << EOF
# ConsultEase keyboard environment variables
ONBOARD_ENABLE_TOUCH=1
ONBOARD_XEMBED=1
GDK_BACKEND=wayland,x11
QT_QPA_PLATFORM=wayland;xcb
EOF
    echo "Environment variables set for onboard."
    
    # Add to .bashrc for immediate effect
    if ! grep -q "ONBOARD_ENABLE_TOUCH" ~/.bashrc; then
        echo "Adding environment variables to .bashrc..."
        cat >> ~/.bashrc << EOF

# ConsultEase keyboard environment variables
export ONBOARD_ENABLE_TOUCH=1
export ONBOARD_XEMBED=1
export GDK_BACKEND=wayland,x11
export QT_QPA_PLATFORM=wayland;xcb
export CONSULTEASE_KEYBOARD=onboard
EOF
    fi
fi

# Create keyboard toggle script
echo "Creating keyboard toggle script..."
cat > ~/keyboard-toggle.sh << EOF
#!/bin/bash
# Toggle on-screen keyboard visibility

# Check for onboard first
if command -v onboard &> /dev/null; then
    if pgrep -f onboard > /dev/null; then
        pkill -f onboard
        echo "Onboard keyboard hidden"
    else
        onboard --size=small --layout=Phone --enable-background-transparency &
        echo "Onboard keyboard shown"
    fi
# Check for squeekboard
elif command -v dbus-send &> /dev/null; then
    if dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible | grep -q "boolean true"; then
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
        echo "Squeekboard hidden"
    else
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
        echo "Squeekboard shown"
    fi
# Try matchbox as last resort
elif command -v matchbox-keyboard &> /dev/null; then
    if pgrep -f matchbox-keyboard > /dev/null; then
        pkill -f matchbox-keyboard
        echo "Matchbox keyboard hidden"
    else
        matchbox-keyboard &
        echo "Matchbox keyboard shown"
    fi
else
    echo "No supported on-screen keyboard found"
fi
EOF
chmod +x ~/keyboard-toggle.sh

echo "Installation completed."
echo "You may need to reboot your Raspberry Pi for all changes to take effect."
