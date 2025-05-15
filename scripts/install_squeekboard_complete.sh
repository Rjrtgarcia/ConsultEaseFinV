#!/bin/bash
# Comprehensive Squeekboard Installation and Configuration Script for ConsultEase
# This script will:
# 1. Install squeekboard if not already installed
# 2. Configure systemd service for squeekboard
# 3. Set up environment variables
# 4. Create utility scripts for keyboard management
# 5. Configure autostart
# 6. Test the installation

echo "ConsultEase Squeekboard Installation Script"
echo "=========================================="
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Warning: This script should not be run as root."
    echo "Please run it as the normal user who will use the system."
    exit 1
fi

# Install squeekboard if not already installed
if ! command_exists squeekboard; then
    echo "Squeekboard not found. Installing..."
    sudo apt update
    sudo apt install -y squeekboard
    
    if ! command_exists squeekboard; then
        echo "Failed to install squeekboard. Please install it manually."
        exit 1
    fi
    echo "✓ Squeekboard installed successfully."
else
    echo "✓ Squeekboard is already installed."
fi

# Install other touch-related utilities
echo "Installing additional touch utilities..."
sudo apt install -y xserver-xorg-input-evdev

# Create systemd user directory if it doesn't exist
echo "Setting up systemd user service..."
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

# Check if we can create/write to the directory
if mkdir -p "$SYSTEMD_USER_DIR" 2>/dev/null; then
    # Create squeekboard service file
    SQUEEKBOARD_SERVICE="$SYSTEMD_USER_DIR/squeekboard.service"
    echo "Creating service file at $SQUEEKBOARD_SERVICE"

    if touch "$SQUEEKBOARD_SERVICE" 2>/dev/null; then
        # We have write permission, create the service file
        cat > "$SQUEEKBOARD_SERVICE" << EOF
[Unit]
Description=On-screen keyboard for Wayland
PartOf=graphical-session.target

[Service]
ExecStart=/usr/bin/squeekboard
Restart=on-failure
Environment=SQUEEKBOARD_FORCE=1
Environment=GDK_BACKEND=wayland,x11
Environment=QT_QPA_PLATFORM=wayland;xcb

[Install]
WantedBy=graphical-session.target
EOF
        echo "✓ Service file created."

        # Reload systemd user daemon
        echo "Reloading systemd user daemon..."
        systemctl --user daemon-reload
        echo "✓ Daemon reloaded."

        # Enable and start the service
        echo "Enabling and starting squeekboard service..."
        systemctl --user enable squeekboard.service
        systemctl --user start squeekboard.service
        echo "✓ Service enabled and started."
    else
        echo "✗ Cannot write to $SQUEEKBOARD_SERVICE"
        echo "Will try alternative methods."
    fi
else
    echo "✗ Cannot create directory $SYSTEMD_USER_DIR"
    echo "Will try alternative methods."
fi

# Configure environment for squeekboard
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
# Disable onboard
ONBOARD_DISABLE=1
EOF
echo "✓ Environment variables set for squeekboard."

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
# Disable onboard
export ONBOARD_DISABLE=1
EOF
    echo "✓ Environment variables added to .bashrc."
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
    # Make sure squeekboard is running
    if ! pgrep -f squeekboard > /dev/null; then
        # Start squeekboard with environment variables
        SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &
        sleep 0.5
    fi
    
    # Show squeekboard
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    echo "Squeekboard shown"
fi
EOF
chmod +x ~/keyboard-toggle.sh
echo "✓ Keyboard toggle script created."

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
echo "✓ Keyboard show script created."

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
echo "✓ Keyboard hide script created."

# Disable onboard autostart if it exists
if [ -f ~/.config/autostart/onboard-autostart.desktop ]; then
    echo "Disabling onboard autostart..."
    mv ~/.config/autostart/onboard-autostart.desktop ~/.config/autostart/onboard-autostart.desktop.disabled
    echo "✓ Onboard autostart disabled."
fi

# Create autostart entry for squeekboard
echo "Setting up autostart for squeekboard..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/squeekboard-autostart.desktop << EOF
[Desktop Entry]
Type=Application
Name=Squeekboard
Exec=squeekboard
Comment=On-screen keyboard for Wayland
X-GNOME-Autostart-enabled=true
EOF
echo "✓ Squeekboard autostart configured."

# Create .env file for ConsultEase if it doesn't exist
if [ -d "../central_system" ]; then
    echo "Creating/updating .env file for ConsultEase..."
    if [ ! -f "../.env" ]; then
        cat > "../.env" << EOF
# ConsultEase Configuration
# Generated by install_squeekboard_complete.sh on $(date)

# Keyboard Configuration
CONSULTEASE_KEYBOARD=squeekboard
SQUEEKBOARD_FORCE=1
ONBOARD_DISABLE=1
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

        if grep -q "ONBOARD_DISABLE=" "../.env"; then
            sed -i 's/ONBOARD_DISABLE=.*/ONBOARD_DISABLE=1/' "../.env"
        else
            echo "ONBOARD_DISABLE=1" >> "../.env"
        fi
    fi
    echo "✓ .env file updated."
fi

# Test squeekboard
echo "Testing squeekboard..."
if pgrep -f squeekboard > /dev/null; then
    echo "✓ Squeekboard is running."
    
    # Try to show the keyboard
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    echo "✓ Attempted to show squeekboard."
    
    # Wait a moment
    sleep 1
    
    # Check if visible
    if dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible | grep -q "boolean true"; then
        echo "✓ Squeekboard is visible."
    else
        echo "✗ Squeekboard is not visible. This might be normal if no input field is focused."
    fi
else
    echo "✗ Squeekboard is not running. Starting it now..."
    SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &
    sleep 1
    
    if pgrep -f squeekboard > /dev/null; then
        echo "✓ Squeekboard started successfully."
    else
        echo "✗ Failed to start squeekboard."
    fi
fi

echo ""
echo "Installation completed!"
echo ""
echo "Keyboard management scripts created:"
echo "  ~/keyboard-toggle.sh - Toggle keyboard visibility"
echo "  ~/keyboard-show.sh - Force show keyboard"
echo "  ~/keyboard-hide.sh - Force hide keyboard"
echo ""
echo "For changes to fully take effect, please reboot your system."
echo ""
