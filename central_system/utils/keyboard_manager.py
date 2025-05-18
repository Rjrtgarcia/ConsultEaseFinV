"""
Unified keyboard manager for ConsultEase.
Provides a single, robust solution for on-screen keyboard management with fallback mechanisms.
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

class KeyboardManager(QObject):
    """
    Unified keyboard manager for on-screen keyboards.
    Provides a single interface for managing different on-screen keyboards with fallback mechanisms.
    """
    # Signal emitted when keyboard visibility changes
    keyboard_visibility_changed = pyqtSignal(bool)

    # Singleton instance
    _instance = None

    @classmethod
    def instance(cls):
        """Get the singleton instance of the keyboard manager."""
        if cls._instance is None:
            cls._instance = KeyboardManager()
        return cls._instance

    def __init__(self):
        """Initialize the keyboard manager."""
        super().__init__()

        # Prevent multiple initialization of the singleton
        if KeyboardManager._instance is not None:
            return

        # Set up keyboard properties
        self.keyboard_visible = False
        self.keyboard_process = None
        self.dbus_available = self._check_dbus_available()

        # Determine preferred keyboard type from environment
        self.preferred_keyboard = os.environ.get('CONSULTEASE_KEYBOARD', 'squeekboard')
        self.fallback_keyboard = 'onboard'

        # Detect available keyboards
        self._detect_available_keyboards()

        # Set up auto-hide timer
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self.hide_keyboard)
        self.auto_hide_timer.setSingleShot(True)

        # Log initialization
        logger.info(f"Keyboard manager initialized with {self.active_keyboard} keyboard")

    def _detect_available_keyboards(self):
        """Detect which keyboards are available on the system."""
        # Check for squeekboard
        self.squeekboard_available = self._check_keyboard_available('squeekboard')
        logger.info(f"Squeekboard available: {self.squeekboard_available}")

        # Check for onboard
        self.onboard_available = self._check_keyboard_available('onboard')
        logger.info(f"Onboard available: {self.onboard_available}")

        # Determine which keyboard to use
        self.active_keyboard = self._determine_active_keyboard()
        logger.info(f"Active keyboard: {self.active_keyboard}")

    def _check_keyboard_available(self, keyboard_type):
        """Check if a specific keyboard is available on the system."""
        try:
            if keyboard_type == 'squeekboard':
                # Check if squeekboard is installed
                result = subprocess.run(['which', 'squeekboard'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                return result.returncode == 0
            elif keyboard_type == 'onboard':
                # Check if onboard is installed
                result = subprocess.run(['which', 'onboard'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                return result.returncode == 0
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking {keyboard_type} availability: {e}")
            return False

    def _determine_active_keyboard(self):
        """Determine which keyboard to use based on availability and preference."""
        # First try preferred keyboard
        if self.preferred_keyboard == 'squeekboard' and self.squeekboard_available:
            return 'squeekboard'
        elif self.preferred_keyboard == 'onboard' and self.onboard_available:
            return 'onboard'

        # Fall back to any available keyboard
        if self.squeekboard_available:
            return 'squeekboard'
        elif self.onboard_available:
            return 'onboard'

        # No keyboard available
        logger.warning("No on-screen keyboard available")
        return None

    def _check_dbus_available(self):
        """Check if DBus is available for controlling squeekboard."""
        try:
            result = subprocess.run(['which', 'dbus-send'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False

    def show_keyboard(self):
        """Show the on-screen keyboard."""
        if self.keyboard_visible:
            return

        logger.info(f"Showing keyboard: {self.active_keyboard}")

        if not self.active_keyboard:
            logger.warning("No keyboard available to show")
            return

        if self.active_keyboard == 'squeekboard':
            self._show_squeekboard()
        elif self.active_keyboard == 'onboard':
            self._show_onboard()
        else:
            logger.warning(f"Unknown keyboard type: {self.active_keyboard}")
            return

        self.keyboard_visible = True
        self.keyboard_visibility_changed.emit(True)

    def hide_keyboard(self):
        """Hide the on-screen keyboard."""
        if not self.keyboard_visible:
            return

        logger.info(f"Hiding keyboard: {self.active_keyboard}")

        if not self.active_keyboard:
            return

        if self.active_keyboard == 'squeekboard':
            self._hide_squeekboard()
        elif self.active_keyboard == 'onboard':
            self._hide_onboard()
        else:
            logger.warning(f"Unknown keyboard type: {self.active_keyboard}")
            return

        self.keyboard_visible = False
        self.keyboard_visibility_changed.emit(False)

    def toggle_keyboard(self):
        """Toggle the on-screen keyboard visibility."""
        if self.keyboard_visible:
            self.hide_keyboard()
        else:
            self.show_keyboard()

    def _show_squeekboard(self):
        """Show squeekboard keyboard."""
        # First ensure squeekboard is running
        if not self._is_squeekboard_running():
            logger.info("Squeekboard not running, starting it...")
            try:
                subprocess.Popen(['squeekboard'],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               env=dict(os.environ, SQUEEKBOARD_FORCE="1"),
                               start_new_session=True)
                # Give it a moment to start
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error starting squeekboard: {e}")
                return

        # Now show the keyboard via DBus
        if self.dbus_available:
            try:
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:true"
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Showed squeekboard via DBus")
            except Exception as e:
                logger.error(f"Error showing squeekboard via DBus: {e}")
        else:
            logger.warning("DBus not available, cannot show squeekboard reliably")

    def _hide_squeekboard(self):
        """Hide squeekboard keyboard."""
        if self.dbus_available:
            try:
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:false"
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Hid squeekboard via DBus")
            except Exception as e:
                logger.error(f"Error hiding squeekboard via DBus: {e}")
        else:
            logger.warning("DBus not available, cannot hide squeekboard reliably")

    def _is_squeekboard_running(self):
        """Check if squeekboard is running."""
        try:
            result = subprocess.run(['pgrep', '-f', 'squeekboard'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False

    def _show_onboard(self):
        """Show onboard keyboard."""
        try:
            # Check if onboard is already running
            if not self._is_onboard_running():
                # Start onboard with appropriate options
                subprocess.Popen(
                    ['onboard', '--size=small', '--layout=Phone', '--enable-background-transparency'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logger.info("Started onboard")
        except Exception as e:
            logger.error(f"Error showing onboard: {e}")

    def _hide_onboard(self):
        """Hide onboard keyboard."""
        try:
            # Just kill the process
            subprocess.run(['pkill', '-f', 'onboard'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            logger.info("Killed onboard process")
        except Exception as e:
            logger.error(f"Error hiding onboard: {e}")

    def _is_onboard_running(self):
        """Check if onboard is running."""
        try:
            result = subprocess.run(['pgrep', '-f', 'onboard'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False

# Convenience function to get the keyboard manager instance
def get_keyboard_manager():
    """Get the keyboard manager instance."""
    return KeyboardManager.instance()

def install_keyboard_manager(app):
    """
    Install the keyboard manager for the application.
    This sets up event filters to show/hide the keyboard when text input widgets receive focus.

    Args:
        app: QApplication instance
    """
    from PyQt5.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit, QComboBox

    keyboard = get_keyboard_manager()

    # Original focus in/out event handlers
    original_focus_in = QLineEdit.focusInEvent
    original_focus_out = QLineEdit.focusOutEvent

    # Override focus in event for QLineEdit
    def line_edit_focus_in(self, event):
        # Call original handler
        original_focus_in(self, event)
        # Show keyboard
        keyboard.show_keyboard()

    # Override focus out event for QLineEdit
    def line_edit_focus_out(self, event):
        # Call original handler
        original_focus_out(self, event)
        # Hide keyboard
        keyboard.hide_keyboard()

    # Apply overrides
    QLineEdit.focusInEvent = line_edit_focus_in
    QLineEdit.focusOutEvent = line_edit_focus_out

    # Do the same for QTextEdit
    original_text_focus_in = QTextEdit.focusInEvent
    original_text_focus_out = QTextEdit.focusOutEvent

    def text_edit_focus_in(self, event):
        original_text_focus_in(self, event)
        keyboard.show_keyboard()

    def text_edit_focus_out(self, event):
        original_text_focus_out(self, event)
        keyboard.hide_keyboard()

    QTextEdit.focusInEvent = text_edit_focus_in
    QTextEdit.focusOutEvent = text_edit_focus_out

    # And for QPlainTextEdit
    original_plain_focus_in = QPlainTextEdit.focusInEvent
    original_plain_focus_out = QPlainTextEdit.focusOutEvent

    def plain_text_focus_in(self, event):
        original_plain_focus_in(self, event)
        keyboard.show_keyboard()

    def plain_text_focus_out(self, event):
        original_plain_focus_out(self, event)
        keyboard.hide_keyboard()

    QPlainTextEdit.focusInEvent = plain_text_focus_in
    QPlainTextEdit.focusOutEvent = plain_text_focus_out

    # And for QComboBox
    original_combo_focus_in = QComboBox.focusInEvent
    original_combo_focus_out = QComboBox.focusOutEvent

    def combo_focus_in(self, event):
        original_combo_focus_in(self, event)
        keyboard.show_keyboard()

    def combo_focus_out(self, event):
        original_combo_focus_out(self, event)
        keyboard.hide_keyboard()

    QComboBox.focusInEvent = combo_focus_in
    QComboBox.focusOutEvent = combo_focus_out

    logger.info("Keyboard manager installed for application")
    return keyboard
