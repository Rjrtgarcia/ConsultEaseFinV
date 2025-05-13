#!/bin/bash
# fix_onboard_keyboard.sh
# Script to fix onboard keyboard issues and improve its functionality
# Created based on user feedback that onboard is not working as well as squeekboard

echo "ConsultEase Onboard Keyboard Fix Script"
echo "======================================="
echo "This script will fix issues with the onboard keyboard and improve its functionality."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo "Please do not run this script as root or with sudo."
  echo "It should be run as a regular user."
  exit 1
fi

# Function to check if a package is installed
check_package() {
  if command -v dpkg-query &> /dev/null; then
    dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"
  else
    command -v "$1" &> /dev/null
  fi
}

# Install required packages
echo "Checking and installing required packages..."
PACKAGES_TO_INSTALL=""

# Check for onboard
if ! check_package onboard; then
  PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL onboard"
fi

# Check for additional dependencies
for pkg in at-spi2-core libcanberra-gtk-module libatk-adaptor; do
  if ! check_package $pkg; then
    PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL $pkg"
  fi
done

# Install missing packages if any
if [ -n "$PACKAGES_TO_INSTALL" ]; then
  echo "Installing missing packages: $PACKAGES_TO_INSTALL"
  sudo apt update
  sudo apt install -y $PACKAGES_TO_INSTALL
  echo "Package installation completed."
else
  echo "All required packages are already installed."
fi

# Stop any running keyboard instances
echo "Stopping any running keyboard instances..."
pkill -f onboard || true
pkill -f squeekboard || true

# Create improved onboard configuration
echo "Creating improved onboard configuration..."
mkdir -p ~/.config/onboard

# Create enhanced onboard configuration file with better touch settings
cat > ~/.config/onboard/onboard.conf << EOF
[main]
layout=Phone
theme=Nightshade
key-size=medium
enable-background-transparency=true
show-status-icon=true
start-minimized=false
show-tooltips=false
auto-show=true
auto-show-delay=300
auto-hide=true
auto-hide-delay=1500
xembed-onboard=true
enable-touch-input=true
touch-feedback-enabled=true
touch-feedback-size=medium
touch-input=multi
show-click-buttons=true
window-decoration=false
force-to-top=true
keep-aspect-ratio=false
resize-handles=none
docking-enabled=true
dock-expand=true
dock-height=300
dock-width=700
key-label-font=Normal bold
key-label-overrides=True
key-style=gradient
key-fill-gradient=20
key-stroke-gradient=30
key-gradient-direction=0.0
key-shadow-strength=70.0
key-shadow-size=5.0
key-stroke-width=0.0
roundrect-radius=20.0
color-scheme=Nightshade
background-gradient=0.0
key-size=94.0
key-stroke-width=0.0
key-fill-gradient=5.0
key-stroke-gradient=25.0
key-gradient-direction=5.0
key-label-font=Sans bold
key-shadow-strength=0.0
key-shadow-size=0.0
key-caption-font=Sans
key-shadow-strength=30.0
key-shadow-size=5.0

[window]
window-state-sticky=True
force-to-top=True
window-decoration=False
transparency=20
background-transparency=20
enable-inactive-transparency=False
inactive-transparency=50
transparent-background=True

[keyboard]
touch-feedback-enabled=True
touch-feedback-size=medium
touch-input=multi
show-click-buttons=True

[auto-show]
enabled=True
hide-on-key-press=True

[typing-assistance]
auto-capitalization=False
auto-correction=False
EOF

# Create autostart entry
echo "Setting up autostart..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/onboard-autostart.desktop << EOF
[Desktop Entry]
Type=Application
Name=Onboard
Exec=onboard --size=medium --layout=Phone --enable-background-transparency --theme=Nightshade
Comment=Flexible on-screen keyboard
X-GNOME-Autostart-enabled=true
EOF

# Set environment variables
echo "Setting up environment variables..."
mkdir -p ~/.config/environment.d/
cat > ~/.config/environment.d/consultease-keyboard.conf << EOF
# ConsultEase keyboard environment variables
ONBOARD_ENABLE_TOUCH=1
ONBOARD_XEMBED=1
GDK_BACKEND=wayland,x11
QT_QPA_PLATFORM=wayland;xcb
CONSULTEASE_KEYBOARD=onboard
# Disable squeekboard
SQUEEKBOARD_DISABLE=1
EOF

# Add to .bashrc for immediate effect
if ! grep -q "CONSULTEASE_KEYBOARD=onboard" ~/.bashrc; then
    echo "Adding environment variables to .bashrc..."
    cat >> ~/.bashrc << EOF

# ConsultEase keyboard environment variables
export ONBOARD_ENABLE_TOUCH=1
export ONBOARD_XEMBED=1
export GDK_BACKEND=wayland,x11
export QT_QPA_PLATFORM=wayland;xcb
export CONSULTEASE_KEYBOARD=onboard
# Disable squeekboard
export SQUEEKBOARD_DISABLE=1
EOF
fi

# Create improved keyboard toggle script
echo "Creating improved keyboard toggle script..."
cat > ~/keyboard-toggle.sh << EOF
#!/bin/bash
# Toggle onboard keyboard with improved settings

# First, make sure squeekboard is not running
if command -v squeekboard &> /dev/null; then
    pkill -f squeekboard

    # Also try DBus method to hide squeekboard
    if command -v dbus-send &> /dev/null; then
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    fi
fi

# Now toggle onboard
if pgrep -f onboard > /dev/null; then
    pkill -f onboard
    echo "Onboard keyboard hidden"
else
    onboard --size=medium --layout=Phone --enable-background-transparency --theme=Nightshade &
    echo "Onboard keyboard shown"
fi
EOF
chmod +x ~/keyboard-toggle.sh

# Create improved keyboard show script
echo "Creating improved keyboard show script..."
cat > ~/keyboard-show.sh << EOF
#!/bin/bash
# Force show onboard keyboard with improved settings

# First, make sure squeekboard is not running
if command -v squeekboard &> /dev/null; then
    pkill -f squeekboard

    # Also try DBus method to hide squeekboard
    if command -v dbus-send &> /dev/null; then
        dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    fi
fi

# Kill any existing onboard instances
pkill -f onboard

# Start onboard with improved options
onboard --size=medium --layout=Phone --enable-background-transparency --theme=Nightshade &
echo "Onboard keyboard shown"
EOF
chmod +x ~/keyboard-show.sh

# Create keyboard hide script
echo "Creating keyboard hide script..."
cat > ~/keyboard-hide.sh << EOF
#!/bin/bash
# Force hide all on-screen keyboards

# Hide onboard
if pgrep -f onboard > /dev/null; then
    pkill -f onboard
    echo "Onboard keyboard hidden"
fi

# Hide squeekboard
if command -v dbus-send &> /dev/null; then
    dbus-send --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.SetVisible boolean:false
    echo "Squeekboard hidden"
fi
EOF
chmod +x ~/keyboard-hide.sh

# Create .env file for ConsultEase if it doesn't exist
if [ -d "central_system" ]; then
    echo "Creating/updating .env file for ConsultEase..."
    if [ ! -f ".env" ]; then
        cat > ".env" << EOF
# ConsultEase Configuration
# Generated by fix_onboard_keyboard.sh on $(date)

# Keyboard Configuration
CONSULTEASE_KEYBOARD=onboard
SQUEEKBOARD_DISABLE=1

# Other settings
CONSULTEASE_THEME=light
EOF
        echo ".env file created."
    else
        # Update existing .env file
        if ! grep -q "CONSULTEASE_KEYBOARD=onboard" ".env"; then
            echo "CONSULTEASE_KEYBOARD=onboard" >> ".env"
            echo "Added CONSULTEASE_KEYBOARD to .env file."
        fi
        if ! grep -q "SQUEEKBOARD_DISABLE=1" ".env"; then
            echo "SQUEEKBOARD_DISABLE=1" >> ".env"
            echo "Added SQUEEKBOARD_DISABLE to .env file."
        fi
    fi
fi

# Start onboard with improved settings
echo "Starting onboard with improved settings..."
pkill -f onboard
onboard --size=medium --layout=Phone --enable-background-transparency --theme=Nightshade &

echo ""
echo "Onboard keyboard fix completed!"
echo ""
echo "Keyboard management scripts created/updated:"
echo "  ~/keyboard-toggle.sh - Toggle keyboard visibility"
echo "  ~/keyboard-show.sh - Force show keyboard"
echo "  ~/keyboard-hide.sh - Force hide keyboard"
echo ""
echo "If the keyboard doesn't appear automatically, try:"
echo "1. Run ~/keyboard-show.sh to manually show it"
echo "2. Press F5 in the application to toggle the keyboard"
echo ""
echo "For changes to fully take effect, please reboot your system."
echo ""
