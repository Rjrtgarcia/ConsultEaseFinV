#!/bin/bash
# Script to remove onboard keyboard and related files from the system
# This script should be run after installing squeekboard

echo "ConsultEase Onboard Removal Script"
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

# Kill any running onboard instances
echo "Stopping any running onboard instances..."
pkill -f onboard || true
echo "✓ Onboard processes stopped."

# Disable onboard autostart
if [ -f ~/.config/autostart/onboard-autostart.desktop ]; then
    echo "Disabling onboard autostart..."
    mv ~/.config/autostart/onboard-autostart.desktop ~/.config/autostart/onboard-autostart.desktop.disabled
    echo "✓ Onboard autostart disabled."
fi

# Remove onboard configuration
if [ -d ~/.config/onboard ]; then
    echo "Removing onboard configuration..."
    rm -rf ~/.config/onboard
    echo "✓ Onboard configuration removed."
fi

# Remove onboard environment variables from .bashrc
echo "Removing onboard environment variables from .bashrc..."
if grep -q "ONBOARD_ENABLE_TOUCH" ~/.bashrc; then
    # Create a backup
    cp ~/.bashrc ~/.bashrc.bak
    
    # Remove onboard-specific lines
    sed -i '/ONBOARD_ENABLE_TOUCH/d' ~/.bashrc
    sed -i '/ONBOARD_XEMBED/d' ~/.bashrc
    sed -i '/CONSULTEASE_KEYBOARD=onboard/d' ~/.bashrc
    
    echo "✓ Onboard environment variables removed from .bashrc."
fi

# Remove onboard environment variables from environment.d
if [ -f ~/.config/environment.d/consultease-keyboard.conf ]; then
    echo "Updating environment.d configuration..."
    
    # Create a backup
    cp ~/.config/environment.d/consultease-keyboard.conf ~/.config/environment.d/consultease-keyboard.conf.bak
    
    # Remove onboard-specific lines and add onboard disable
    sed -i '/ONBOARD_ENABLE_TOUCH/d' ~/.config/environment.d/consultease-keyboard.conf
    sed -i '/ONBOARD_XEMBED/d' ~/.config/environment.d/consultease-keyboard.conf
    sed -i '/CONSULTEASE_KEYBOARD=onboard/d' ~/.config/environment.d/consultease-keyboard.conf
    
    # Add onboard disable if not already present
    if ! grep -q "ONBOARD_DISABLE=1" ~/.config/environment.d/consultease-keyboard.conf; then
        echo "ONBOARD_DISABLE=1" >> ~/.config/environment.d/consultease-keyboard.conf
    fi
    
    echo "✓ Environment.d configuration updated."
fi

# Remove onboard keyboard scripts
echo "Removing onboard keyboard scripts..."
if [ -f ~/keyboard-toggle.sh ] && grep -q "onboard" ~/keyboard-toggle.sh; then
    mv ~/keyboard-toggle.sh ~/keyboard-toggle.sh.bak
    echo "✓ Backed up and removed onboard keyboard toggle script."
fi

if [ -f ~/keyboard-show.sh ] && grep -q "onboard" ~/keyboard-show.sh; then
    mv ~/keyboard-show.sh ~/keyboard-show.sh.bak
    echo "✓ Backed up and removed onboard keyboard show script."
fi

if [ -f ~/keyboard-hide.sh ] && grep -q "onboard" ~/keyboard-hide.sh; then
    mv ~/keyboard-hide.sh ~/keyboard-hide.sh.bak
    echo "✓ Backed up and removed onboard keyboard hide script."
fi

# Update .env file if it exists
if [ -f .env ]; then
    echo "Updating .env file..."
    
    # Create a backup
    cp .env .env.bak
    
    # Remove onboard-specific lines and add squeekboard configuration
    sed -i '/CONSULTEASE_KEYBOARD=onboard/d' .env
    
    # Add squeekboard configuration if not already present
    if ! grep -q "CONSULTEASE_KEYBOARD=squeekboard" .env; then
        echo "CONSULTEASE_KEYBOARD=squeekboard" >> .env
    fi
    
    if ! grep -q "SQUEEKBOARD_FORCE=1" .env; then
        echo "SQUEEKBOARD_FORCE=1" >> .env
    fi
    
    if ! grep -q "ONBOARD_DISABLE=1" .env; then
        echo "ONBOARD_DISABLE=1" >> .env
    fi
    
    echo "✓ .env file updated."
fi

echo ""
echo "Onboard removal completed!"
echo ""
echo "For changes to fully take effect, please reboot your system."
echo ""
echo "If you want to completely uninstall onboard from the system, run:"
echo "sudo apt remove --purge onboard"
echo ""
