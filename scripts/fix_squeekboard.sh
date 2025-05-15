#!/bin/bash
# Script to fix squeekboard installation and configuration
# This script will:
# 1. Check if squeekboard is installed
# 2. Install it if not present
# 3. Create a proper systemd user service file
# 4. Configure environment variables
# 5. Test the installation

echo "ConsultEase Squeekboard Fix Script"
echo "=================================="
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

# Check if squeekboard is installed
echo "Checking if squeekboard is installed..."
if command_exists squeekboard; then
    echo "✓ Squeekboard is installed."
    SQUEEKBOARD_PATH=$(which squeekboard)
    echo "  Path: $SQUEEKBOARD_PATH"
else
    echo "✗ Squeekboard is not installed."
    echo "Installing squeekboard..."
    sudo apt update
    sudo apt install -y squeekboard

    if command_exists squeekboard; then
        echo "✓ Squeekboard installed successfully."
        SQUEEKBOARD_PATH=$(which squeekboard)
        echo "  Path: $SQUEEKBOARD_PATH"
    else
        echo "✗ Failed to install squeekboard."
        echo "Trying alternative installation methods..."

        # Try installing dependencies
        sudo apt install -y libgtk-3-0 libwayland-client0 libinput10

        echo "Installation failed. Please install squeekboard manually."
        exit 1
    fi
fi

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

        # Check if service started successfully
        if systemctl --user is-active squeekboard.service &> /dev/null; then
            echo "✓ Squeekboard service started successfully."
        else
            echo "✗ Failed to start squeekboard service."
            echo "Checking for errors..."
            systemctl --user status squeekboard.service

            echo "Trying direct launch as fallback..."
            # Kill any existing instances
            pkill -f squeekboard

            # Launch directly
            SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &

            echo "✓ Launched squeekboard directly."
        fi
    else
        echo "✗ Cannot write to $SQUEEKBOARD_SERVICE (permission denied)"
        echo "Skipping service file creation and using direct launch method instead."

        # Kill any existing instances
        pkill -f squeekboard 2>/dev/null

        # Launch directly
        echo "Launching squeekboard directly..."
        SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &

        echo "✓ Launched squeekboard directly."

        echo "Note: To create the service file, you may need to run this script with appropriate permissions."
    fi
else
    echo "✗ Cannot create directory $SYSTEMD_USER_DIR (permission denied)"
    echo "Skipping service file creation and using direct launch method instead."

    # Kill any existing instances
    pkill -f squeekboard 2>/dev/null

    # Launch directly
    echo "Launching squeekboard directly..."
    SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &

    echo "✓ Launched squeekboard directly."

    echo "Note: To create the service file, you may need to run this script with appropriate permissions."
fi

# Set up environment variables
echo "Setting up environment variables..."
ENV_DIR="$HOME/.config/environment.d"

# Check if we can create/write to the environment directory
if mkdir -p "$ENV_DIR" 2>/dev/null; then
    ENV_FILE="$ENV_DIR/consultease-keyboard.conf"
    echo "Creating environment file at $ENV_FILE"

    if touch "$ENV_FILE" 2>/dev/null; then
        # We have write permission, create the environment file
        cat > "$ENV_FILE" << EOF
# ConsultEase keyboard environment variables
GDK_BACKEND=wayland,x11
QT_QPA_PLATFORM=wayland;xcb
SQUEEKBOARD_FORCE=1
CONSULTEASE_KEYBOARD=squeekboard
MOZ_ENABLE_WAYLAND=1
QT_IM_MODULE=wayland
CLUTTER_IM_MODULE=wayland
EOF
        echo "✓ Environment file created."
    else
        echo "✗ Cannot write to $ENV_FILE (permission denied)"
        echo "Skipping environment file creation."
    fi
else
    echo "✗ Cannot create directory $ENV_DIR (permission denied)"
    echo "Skipping environment file creation."
fi

# Add to .bashrc for immediate effect - this should work even if the environment.d approach fails
if touch "$HOME/.bashrc" 2>/dev/null; then
    if ! grep -q "CONSULTEASE_KEYBOARD=squeekboard" "$HOME/.bashrc"; then
        echo "Adding environment variables to .bashrc..."
        cat >> "$HOME/.bashrc" << EOF

# ConsultEase keyboard environment variables
export GDK_BACKEND=wayland,x11
export QT_QPA_PLATFORM=wayland;xcb
export SQUEEKBOARD_FORCE=1
export CONSULTEASE_KEYBOARD=squeekboard
export MOZ_ENABLE_WAYLAND=1
export QT_IM_MODULE=wayland
export CLUTTER_IM_MODULE=wayland
EOF
        echo "✓ Added to .bashrc"
    else
        echo "✓ Environment variables already in .bashrc"
    fi
else
    echo "✗ Cannot write to .bashrc (permission denied)"
    echo "Setting environment variables for current session only..."

    # Set for current session
    export GDK_BACKEND=wayland,x11
    export QT_QPA_PLATFORM=wayland;xcb
    export SQUEEKBOARD_FORCE=1
    export CONSULTEASE_KEYBOARD=squeekboard
    export MOZ_ENABLE_WAYLAND=1
    export QT_IM_MODULE=wayland
    export CLUTTER_IM_MODULE=wayland

    echo "✓ Environment variables set for current session"
    echo "Note: These settings will be lost when you log out."
fi

# Create keyboard toggle scripts
echo "Creating keyboard utility scripts..."

# Create keyboard show script
SHOW_SCRIPT="$HOME/keyboard-show.sh"
echo "Creating show script at $SHOW_SCRIPT"

if touch "$SHOW_SCRIPT" 2>/dev/null; then
    cat > "$SHOW_SCRIPT" << EOF
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
    chmod +x "$SHOW_SCRIPT" 2>/dev/null || echo "Warning: Could not make script executable"
    echo "✓ Show script created."
else
    echo "✗ Cannot write to $SHOW_SCRIPT (permission denied)"
    echo "Skipping show script creation."
fi

# Create keyboard hide script
HIDE_SCRIPT="$HOME/keyboard-hide.sh"
echo "Creating hide script at $HIDE_SCRIPT"

if touch "$HIDE_SCRIPT" 2>/dev/null; then
    cat > "$HIDE_SCRIPT" << EOF
#!/bin/bash
# Force hide squeekboard keyboard

# Hide squeekboard
dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
echo "Squeekboard hidden"
EOF
    chmod +x "$HIDE_SCRIPT" 2>/dev/null || echo "Warning: Could not make script executable"
    echo "✓ Hide script created."
else
    echo "✗ Cannot write to $HIDE_SCRIPT (permission denied)"
    echo "Skipping hide script creation."
fi

# Create keyboard toggle script
TOGGLE_SCRIPT="$HOME/keyboard-toggle.sh"
echo "Creating toggle script at $TOGGLE_SCRIPT"

if touch "$TOGGLE_SCRIPT" 2>/dev/null; then
    cat > "$TOGGLE_SCRIPT" << EOF
#!/bin/bash
# Toggle squeekboard keyboard

# Make sure squeekboard is running
if ! pgrep -f squeekboard > /dev/null; then
    # Start squeekboard with environment variables
    SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &
    sleep 0.5
fi

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
    chmod +x "$TOGGLE_SCRIPT" 2>/dev/null || echo "Warning: Could not make script executable"
    echo "✓ Toggle script created."
else
    echo "✗ Cannot write to $TOGGLE_SCRIPT (permission denied)"
    echo "Skipping toggle script creation."
fi

# Create a script in the current directory as a fallback
CURRENT_DIR_SCRIPT="./show-keyboard.sh"
echo "Creating fallback script in current directory at $CURRENT_DIR_SCRIPT"

if touch "$CURRENT_DIR_SCRIPT" 2>/dev/null; then
    cat > "$CURRENT_DIR_SCRIPT" << EOF
#!/bin/bash
# Force show squeekboard keyboard (fallback script)

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
    chmod +x "$CURRENT_DIR_SCRIPT" 2>/dev/null || echo "Warning: Could not make script executable"
    echo "✓ Fallback script created in current directory."
else
    echo "✗ Cannot write to $CURRENT_DIR_SCRIPT (permission denied)"
    echo "Skipping fallback script creation."
fi

echo "Keyboard utility scripts setup completed."

# Update .env file if it exists
if [ -f ".env" ]; then
    echo "Updating .env file..."
    if grep -q "CONSULTEASE_KEYBOARD=" ".env"; then
        sed -i 's/CONSULTEASE_KEYBOARD=.*/CONSULTEASE_KEYBOARD=squeekboard/' ".env"
    else
        echo "CONSULTEASE_KEYBOARD=squeekboard" >> ".env"
    fi

    if grep -q "SQUEEKBOARD_FORCE=" ".env"; then
        sed -i 's/SQUEEKBOARD_FORCE=.*/SQUEEKBOARD_FORCE=1/' ".env"
    else
        echo "SQUEEKBOARD_FORCE=1" >> ".env"
    fi
    echo "✓ .env file updated."
else
    echo "Creating .env file..."
    cat > ".env" << EOF
# ConsultEase Configuration
# Generated by fix_squeekboard.sh on $(date)

# Keyboard Configuration
CONSULTEASE_KEYBOARD=squeekboard
SQUEEKBOARD_FORCE=1
EOF
    echo "✓ .env file created."
fi

echo
echo "Squeekboard setup completed!"
echo "You may need to restart your application or log out and back in for all changes to take effect."
echo "To test squeekboard, run: $HOME/keyboard-show.sh"
