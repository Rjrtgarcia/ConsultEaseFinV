#!/bin/bash
# Emergency fix for squeekboard issues
echo "ConsultEase Keyboard Fixer"
echo "==========================="

# Check if squeekboard is installed
if ! command -v squeekboard &> /dev/null; then
    echo "Squeekboard not found, installing..."
    sudo apt update
    sudo apt install -y squeekboard
else
    echo "Squeekboard is installed."
fi

# Ensure service is running
echo "Checking squeekboard service..."
if systemctl --user is-active squeekboard.service &> /dev/null; then
    echo "Squeekboard service is running. Restarting it..."
    systemctl --user restart squeekboard.service
else
    echo "Squeekboard service is not running. Starting it..."
    systemctl --user start squeekboard.service
    systemctl --user enable squeekboard.service
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
GDK_BACKEND=wayland,x11
QT_QPA_PLATFORM=wayland;xcb
SQUEEKBOARD_FORCE=1
EOF

# Create keyboard toggle script
echo "Creating keyboard toggle script..."
cat > ~/keyboard-toggle.sh << EOF
#!/bin/bash
# Toggle squeekboard visibility
if dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible | grep -q "boolean true"; then
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    echo "Keyboard hidden"
else
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    echo "Keyboard shown"
fi
EOF
chmod +x ~/keyboard-toggle.sh

# Try to show keyboard now
echo "Attempting to show keyboard..."
dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true

echo ""
echo "Setup complete! Here's what to do next:"
echo "1. Reboot your system: sudo reboot"
echo "2. If keyboard still doesn't appear after reboot:"
echo "   - Press F5 in the application to toggle the keyboard"
echo "   - Run ~/keyboard-toggle.sh from a terminal"
echo "3. Make sure you're running the application as a regular user, not as root"
echo ""
echo "If nothing works, you may need to check if your system is running Wayland or X11." 