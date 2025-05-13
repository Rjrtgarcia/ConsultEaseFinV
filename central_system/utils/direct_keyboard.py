"""
Direct keyboard integration for ConsultEase.
This module provides direct keyboard integration with onboard and other on-screen keyboards
that works on all platforms. Prioritizes onboard over squeekboard as per user preference.
"""
import os
import sys
import time
import logging
import subprocess
import threading
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QPlainTextEdit

logger = logging.getLogger(__name__)

class DirectKeyboard(QObject):
    """
    Direct keyboard integration for on-screen keyboards.
    This class provides direct keyboard integration that works on all platforms.
    Prioritizes onboard over squeekboard as per user preference.
    """
    # Signal emitted when keyboard visibility changes
    keyboard_visibility_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        """Initialize the direct keyboard integration."""
        super(DirectKeyboard, self).__init__(parent)

        # Initialize state
        self.keyboard_visible = False
        self.last_show_attempt = 0
        self.show_attempts = 0

        # Determine which keyboard to use (prioritize onboard)
        self.keyboard_type = self._detect_keyboard()

        # Set up timer for periodic checks
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_keyboard)
        self.check_timer.start(5000)  # Check every 5 seconds

        # Log initialization
        logger.info(f"Direct keyboard integration initialized. Using: {self.keyboard_type}")

        # Ensure keyboard is installed
        self._ensure_keyboard_installed()

    def _detect_keyboard(self):
        """Detect which keyboard to use, prioritizing onboard."""
        # Check environment variable first
        if "CONSULTEASE_KEYBOARD" in os.environ:
            keyboard_type = os.environ["CONSULTEASE_KEYBOARD"].lower()
            if keyboard_type in ["onboard", "squeekboard"]:
                logger.info(f"Using keyboard from environment variable: {keyboard_type}")
                return keyboard_type

        # Check if onboard is installed (preferred)
        try:
            result = subprocess.run(['which', 'onboard'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            if result.returncode == 0:
                logger.info("Detected onboard keyboard")
                return "onboard"
        except Exception:
            pass

        # Check if squeekboard is installed (fallback)
        try:
            result = subprocess.run(['which', 'squeekboard'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            if result.returncode == 0:
                logger.info("Detected squeekboard keyboard")
                return "squeekboard"
        except Exception:
            pass

        # Default to onboard even if not installed yet
        logger.info("No keyboard detected, defaulting to onboard")
        return "onboard"

    def _ensure_keyboard_installed(self):
        """Ensure the selected keyboard is installed."""
        if not sys.platform.startswith('linux'):
            return

        if self.keyboard_type == "onboard":
            try:
                # Check if onboard is installed
                result = subprocess.run(['which', 'onboard'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                if result.returncode != 0:
                    logger.warning("Onboard not installed. Creating installation script...")

                    # Create a script to install onboard
                    script_path = os.path.expanduser("~/install-onboard.sh")
                    with open(script_path, 'w') as f:
                        f.write("""#!/bin/bash
echo "Installing onboard keyboard..."
sudo apt update
sudo apt install -y onboard
echo "Creating autostart entry..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/onboard-autostart.desktop << EOL
[Desktop Entry]
Type=Application
Name=Onboard
Exec=onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade
Comment=Flexible on-screen keyboard
EOL
echo "Onboard installation complete!"
""")
                    os.chmod(script_path, 0o755)
                    logger.info(f"Created onboard installation script at {script_path}")
                    logger.info("Please run the script to install onboard")
            except Exception as e:
                logger.error(f"Error checking/installing onboard: {e}")

    def _check_keyboard(self):
        """Periodically check if the keyboard is running and restart if needed."""
        # Only run on Linux
        if not sys.platform.startswith('linux'):
            return

        try:
            # First check if onboard is running
            result = subprocess.run(['pgrep', '-f', 'onboard'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

            # If onboard is not running, check for squeekboard
            if result.returncode != 0:
                result = subprocess.run(['pgrep', '-f', 'squeekboard'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

            # If no keyboard is running and should be visible, restart it
            if result.returncode != 0 and self.keyboard_visible:
                logger.info("Keyboard process not found but should be visible, restarting...")
                self.show_keyboard()
        except Exception as e:
            logger.debug(f"Error checking keyboard status: {e}")

    def show_keyboard(self):
        """Show the on-screen keyboard using the preferred method."""
        # Limit show attempts to avoid excessive calls
        current_time = time.time()
        if current_time - self.last_show_attempt < 0.5:
            self.show_attempts += 1
            if self.show_attempts > 5:
                # Too many attempts in a short time, wait a bit
                return
        else:
            self.last_show_attempt = current_time
            self.show_attempts = 1

        logger.info(f"Showing keyboard: {self.keyboard_type}")
        self.keyboard_visible = True

        # Only run on Linux
        if not sys.platform.startswith('linux'):
            return

        if self.keyboard_type == "onboard":
            self._show_onboard()
        elif self.keyboard_type == "squeekboard":
            self._show_squeekboard()
        else:
            # Try all methods as fallback
            self._show_onboard()
            self._show_squeekboard()
            self._try_matchbox_keyboard()

        # Emit signal
        self.keyboard_visibility_changed.emit(True)

    def _show_onboard(self):
        """Show onboard keyboard."""
        try:
            # Check if onboard is already running
            result = subprocess.run(['pgrep', '-f', 'onboard'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

            # If not running, start it
            if result.returncode != 0:
                # Start onboard with appropriate options
                subprocess.Popen(
                    ['onboard', '--size=small', '--layout=Phone', '--enable-background-transparency', '--theme=Nightshade'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logger.info("Started onboard keyboard")
        except Exception as e:
            logger.error(f"Error launching onboard: {e}")

    def _show_squeekboard(self):
        """Show squeekboard keyboard."""
        try:
            # Try DBus method first
            try:
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:true"
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Sent DBus command to show squeekboard")
            except Exception as e:
                logger.debug(f"Error showing squeekboard via DBus: {e}")

            # Also try direct launch
            result = subprocess.run(['pgrep', '-f', 'squeekboard'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

            # If not running, start it
            if result.returncode != 0:
                # Kill any existing instances first
                subprocess.run(['pkill', '-f', 'squeekboard'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

                # Start squeekboard with environment variables
                env = dict(os.environ)
                env['SQUEEKBOARD_FORCE'] = '1'
                env['GDK_BACKEND'] = 'wayland,x11'
                env['QT_QPA_PLATFORM'] = 'wayland;xcb'

                subprocess.Popen(['squeekboard'],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               env=env,
                               start_new_session=True)

                # Try DBus again after a short delay
                QTimer.singleShot(500, lambda: self._try_dbus_show())
                logger.info("Started squeekboard directly")
        except Exception as e:
            logger.error(f"Error launching squeekboard: {e}")

    def _try_matchbox_keyboard(self):
        """Try matchbox-keyboard as a last resort."""
        try:
            # Check if any keyboard is running
            onboard_result = subprocess.run(['pgrep', '-f', 'onboard'],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
            squeekboard_result = subprocess.run(['pgrep', '-f', 'squeekboard'],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)

            # If neither is running, try matchbox-keyboard
            if onboard_result.returncode != 0 and squeekboard_result.returncode != 0:
                try:
                    subprocess.Popen(['matchbox-keyboard'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    logger.info("Started matchbox-keyboard as fallback")
                except Exception:
                    logger.warning("Failed to start any on-screen keyboard")
        except Exception as e:
            logger.debug(f"Error checking keyboard status: {e}")

    def _try_dbus_show(self):
        """Try to show the keyboard using DBus after a delay."""
        try:
            cmd = [
                "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:true"
            ]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def hide_keyboard(self):
        """Hide the on-screen keyboard."""
        if not self.keyboard_visible:
            return

        logger.info(f"Hiding keyboard: {self.keyboard_type}")
        self.keyboard_visible = False

        # Only run on Linux
        if not sys.platform.startswith('linux'):
            return

        if self.keyboard_type == "onboard":
            self._hide_onboard()
        elif self.keyboard_type == "squeekboard":
            self._hide_squeekboard()
        else:
            # Try all methods as fallback
            self._hide_onboard()
            self._hide_squeekboard()
            self._hide_other_keyboards()

        # Emit signal
        self.keyboard_visibility_changed.emit(False)

    def _hide_onboard(self):
        """Hide onboard keyboard."""
        try:
            subprocess.run(['pkill', '-f', 'onboard'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            logger.info("Killed onboard process")
        except Exception as e:
            logger.error(f"Error killing onboard: {e}")

    def _hide_squeekboard(self):
        """Hide squeekboard keyboard."""
        try:
            # Try DBus method first
            try:
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:false"
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Sent DBus command to hide squeekboard")
            except Exception as e:
                logger.debug(f"Error hiding squeekboard via DBus: {e}")

            # Also try killing the process
            subprocess.run(['pkill', '-f', 'squeekboard'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            logger.info("Killed squeekboard process")
        except Exception as e:
            logger.error(f"Error killing squeekboard: {e}")

    def _hide_other_keyboards(self):
        """Hide any other keyboard processes."""
        try:
            subprocess.run(['pkill', '-f', 'matchbox-keyboard'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            logger.debug("Killed matchbox-keyboard process")
        except Exception:
            pass

# Global direct keyboard instance
_direct_keyboard = None

def get_direct_keyboard():
    """Get the global direct keyboard instance."""
    global _direct_keyboard
    if _direct_keyboard is None:
        _direct_keyboard = DirectKeyboard()
    return _direct_keyboard

def setup_input_hooks():
    """Set up hooks for all input fields to show keyboard."""
    # Get the direct keyboard
    keyboard = get_direct_keyboard()

    # Get the application instance
    app = QApplication.instance()
    if not app:
        logger.error("No QApplication instance found")
        return

    # Original focus in/out event handlers
    original_line_focus_in = QLineEdit.focusInEvent

    # Override focus in event for QLineEdit
    def line_edit_focus_in(self, event):
        # Call original handler
        original_line_focus_in(self, event)
        # Show keyboard
        keyboard.show_keyboard()

    # Apply the override
    QLineEdit.focusInEvent = line_edit_focus_in

    # Do the same for QTextEdit
    original_text_focus_in = QTextEdit.focusInEvent

    def text_edit_focus_in(self, event):
        original_text_focus_in(self, event)
        keyboard.show_keyboard()

    QTextEdit.focusInEvent = text_edit_focus_in

    # And for QPlainTextEdit
    original_plain_focus_in = QPlainTextEdit.focusInEvent

    def plain_text_focus_in(self, event):
        original_plain_focus_in(self, event)
        keyboard.show_keyboard()

    QPlainTextEdit.focusInEvent = plain_text_focus_in

    logger.info("Input hooks set up successfully")
