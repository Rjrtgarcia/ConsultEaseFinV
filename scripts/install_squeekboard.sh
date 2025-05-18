#!/bin/bash
# ConsultEase - Squeekboard Installation Script
# This script installs and configures squeekboard for the ConsultEase system

# Exit on error
set -e

# Function to display status messages
status() {
    echo -e "\033[1;34m[*] $1\033[0m"
}

# Function to display success messages
success() {
    echo -e "\033[1;32m[✓] $1\033[0m"
}

# Function to display error messages
error() {
    echo -e "\033[1;31m[✗] $1\033[0m"
}

# Function to display warning messages
warning() {
    echo -e "\033[1;33m[!] $1\033[0m"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    warning "Running as root. Some operations may not work correctly with user services."
    warning "Consider running this script as a regular user with sudo privileges."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Installation aborted."
        exit 1
    fi
fi

# Check distribution
status "Detecting Linux distribution..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
    success "Detected distribution: $DISTRO $VERSION_ID"
else
    warning "Could not detect distribution, assuming Debian-based"
    DISTRO="debian"
fi

# Install squeekboard
status "Checking if squeekboard is installed..."
if ! command -v squeekboard &> /dev/null; then
    status "Squeekboard not found, installing..."
    
    case $DISTRO in
        debian|ubuntu|raspbian)
            sudo apt update
            sudo apt install -y squeekboard dbus-x11
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm squeekboard
            ;;
        fedora)
            sudo dnf install -y squeekboard
            ;;
        *)
            error "Unsupported distribution: $DISTRO"
            error "Please install squeekboard manually and run this script again."
            exit 1
            ;;
    esac
    
    success "Squeekboard installed successfully"
else
    success "Squeekboard is already installed"
fi

# Configure environment
status "Configuring environment for squeekboard..."

# Create environment.d directory if it doesn't exist
mkdir -p ~/.config/environment.d/

# Create environment configuration file
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
    status "Adding environment variables to .bashrc..."
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

# Create keyboard management scripts
status "Creating keyboard management scripts..."

# Create keyboard toggle script
cat > ~/keyboard-toggle.sh << EOF
#!/bin/bash
# Toggle squeekboard keyboard

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
EOF
chmod +x ~/keyboard-toggle.sh

# Create keyboard show script
cat > ~/keyboard-show.sh << EOF
#!/bin/bash
# Force show squeekboard keyboard

# Show squeekboard using DBus
if command -v dbus-send &> /dev/null; then
    # Make sure squeekboard is running
    if ! pgrep -f squeekboard > /dev/null; then
        # Start squeekboard with environment variables
        SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &
        sleep 0.5
    fi
    
    # Show squeekboard
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:true
    echo "Squeekboard shown"
else
    echo "DBus not available, cannot show squeekboard"
fi
EOF
chmod +x ~/keyboard-show.sh

# Create keyboard hide script
cat > ~/keyboard-hide.sh << EOF
#!/bin/bash
# Force hide squeekboard keyboard

# Hide squeekboard using DBus
if command -v dbus-send &> /dev/null; then
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    echo "Squeekboard hidden"
else
    echo "DBus not available, cannot hide squeekboard"
fi
EOF
chmod +x ~/keyboard-hide.sh

# Enable and start squeekboard service
status "Enabling squeekboard service..."
if command -v systemctl &> /dev/null; then
    systemctl --user enable squeekboard.service 2>/dev/null || true
    systemctl --user start squeekboard.service 2>/dev/null || true
    success "Squeekboard service enabled and started"
else
    warning "systemctl not found, could not enable squeekboard service"
    # Start squeekboard manually
    if ! pgrep -f squeekboard > /dev/null; then
        SQUEEKBOARD_FORCE=1 GDK_BACKEND=wayland,x11 QT_QPA_PLATFORM=wayland squeekboard &
        success "Started squeekboard manually"
    fi
fi

success "Squeekboard installation and configuration complete!"
echo
echo "To use the keyboard:"
echo "- Toggle: ~/keyboard-toggle.sh"
echo "- Show: ~/keyboard-show.sh"
echo "- Hide: ~/keyboard-hide.sh"
echo
echo "You may need to restart your session for all changes to take effect."
