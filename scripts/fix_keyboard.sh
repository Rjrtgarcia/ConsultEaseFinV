#!/bin/bash
# Emergency fix for on-screen keyboard issues
echo "ConsultEase Keyboard Fixer"
echo "==========================="

# Check if onboard is installed
if ! command -v onboard &> /dev/null; then
    echo "Onboard not found, installing..."
    sudo apt update
    sudo apt install -y onboard

    # If onboard installation fails, try squeekboard
    if ! command -v onboard &> /dev/null; then
        echo "Onboard installation failed, trying squeekboard..."
        sudo apt install -y squeekboard
    fi
else
    echo "Onboard is installed."
fi

# Configure onboard
if command -v onboard &> /dev/null; then
    echo "Configuring onboard..."

    # Create autostart entry
    mkdir -p ~/.config/autostart
    cat > ~/.config/autostart/onboard-autostart.desktop << EOF
[Desktop Entry]
Type=Application
Name=Onboard
Exec=onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade
Comment=Flexible on-screen keyboard
EOF

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
fi

# Check for squeekboard as fallback
if command -v squeekboard &> /dev/null; then
    echo "Checking squeekboard service..."
    if systemctl --user is-active squeekboard.service &> /dev/null; then
        echo "Squeekboard service is running. Restarting it..."
        systemctl --user restart squeekboard.service
    else
        echo "Squeekboard service is not running. Starting it..."
        systemctl --user start squeekboard.service
        systemctl --user enable squeekboard.service
    fi
fi

# Set correct permissions for input devices
echo "Setting input device permissions..."
if [ -d "/dev/input" ]; then
    sudo chmod -R a+rw /dev/input/
fi

# Create environment setup
echo "Setting up environment variables..."
mkdir -p ~/.config/environment.d/
cat > ~/.config/environment.d/consultease-keyboard.conf << EOF
# ConsultEase keyboard environment variables
ONBOARD_ENABLE_TOUCH=1
ONBOARD_XEMBED=1
GDK_BACKEND=wayland,x11
QT_QPA_PLATFORM=wayland;xcb
CONSULTEASE_KEYBOARD=onboard
EOF

# Also add to .bashrc for immediate effect
if ! grep -q "CONSULTEASE_KEYBOARD" ~/.bashrc; then
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

# Try to show keyboard now
echo "Attempting to show keyboard..."
if command -v onboard &> /dev/null; then
    # Start onboard
    pkill -f onboard
    onboard --size=small --layout=Phone --enable-background-transparency &
    echo "Started onboard"
elif command -v dbus-send &> /dev/null; then
    # Try squeekboard
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    echo "Attempted to show squeekboard"
fi

echo ""
echo "Setup complete! Here's what to do next:"
echo "1. Reboot your system: sudo reboot"
echo "2. If keyboard still doesn't appear after reboot:"
echo "   - Press F5 in the application to toggle the keyboard"
echo "   - Run ~/keyboard-toggle.sh from a terminal"
echo "3. Make sure you're running the application as a regular user, not as root"
echo ""
echo "If nothing works, you may need to check if your system is running Wayland or X11."