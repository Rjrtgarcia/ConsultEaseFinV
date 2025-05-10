import os
import subprocess
import logging
import signal
import time
import sys
from PyQt5.QtCore import QObject, QEvent, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QWidget
from PyQt5.QtGui import QGuiApplication

logger = logging.getLogger(__name__)

class KeyboardHandler(QObject):
    """
    Handler for virtual keyboard management on touchscreen interfaces.

    This class manages the auto-showing of on-screen keyboards when text input
    fields receive focus, and hiding them when focus is lost. It supports
    multiple virtual keyboard implementations (squeekboard, onboard, matchbox-keyboard).
    """

    def __init__(self, parent=None):
        """Initialize the keyboard handler.

        Args:
            parent: Parent QObject
        """
        super(KeyboardHandler, self).__init__(parent)

        # Set environment variables to help keyboard detection
        self._set_keyboard_environment()

        # Detect available keyboard
        self.keyboard_type = self._detect_keyboard()
        self.keyboard_process = None
        self.current_focus_widget = None
        self.keyboard_visible = False

        # Timer to add a slight delay for keyboard appearance
        self.keyboard_timer = QTimer(self)
        self.keyboard_timer.setSingleShot(True)
        self.keyboard_timer.timeout.connect(self._delayed_show_keyboard)

        # Debug mode - more verbose logging
        self.debug_mode = os.environ.get('CONSULTEASE_KEYBOARD_DEBUG', 'false').lower() == 'true'

        # Explicitly try to create keyboard once at startup
        self._ensure_keyboard_service()

        # Log detected keyboard
        if self.keyboard_type:
            keyboard_info = f"Initialized keyboard handler with keyboard type: {self.keyboard_type}"
            self._check_keyboard_availability()
        else:
            keyboard_info = "No on-screen keyboard detected. Touch keyboard functionality will be disabled."

        logger.info(keyboard_info)

    def _set_keyboard_environment(self):
        """Set environment variables to help with keyboard detection and usage"""
        # Set environment variables to ensure keyboard backends work properly
        # These can help squeekboard know when to appear
        if sys.platform.startswith('linux'):
            os.environ["GDK_BACKEND"] = "wayland,x11"
            os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"
            # Force squeekboard to appear (used by the show_keyboard method)
            os.environ["SQUEEKBOARD_FORCE"] = "1"

            # Check if we're running as root and warn if so
            if os.geteuid() == 0:
                logger.warning("Running as root may affect keyboard detection. Consider running as normal user.")

    def _ensure_keyboard_service(self):
        """Ensure the keyboard service is running properly on system"""
        if not sys.platform.startswith('linux'):
            return

        if self.keyboard_type == 'squeekboard':
            try:
                # Check if squeekboard service is running
                check_cmd = "systemctl --user is-active squeekboard.service"
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

                if "inactive" in result.stdout or "failed" in result.stdout:
                    logger.info("Squeekboard service not running, attempting to start it...")
                    start_cmd = "systemctl --user start squeekboard.service"
                    subprocess.run(start_cmd, shell=True)

                    # Check if it's now running
                    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                    if "active" in result.stdout:
                        logger.info("Squeekboard service started successfully")
                    else:
                        logger.warning("Failed to start squeekboard service, keyboard may not appear")
                else:
                    logger.info("Squeekboard service is already running")

            except Exception as e:
                logger.error(f"Error checking/starting squeekboard service: {e}")

    def _check_keyboard_availability(self):
        """Check if the detected keyboard can actually be launched"""
        try:
            # Try to start and immediately kill the keyboard process
            if self.keyboard_type == 'squeekboard':
                startup_check = subprocess.Popen(['squeekboard', '--help'],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
            elif self.keyboard_type == 'onboard':
                startup_check = subprocess.Popen(['onboard', '--help'],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
            elif self.keyboard_type == 'matchbox-keyboard':
                startup_check = subprocess.Popen(['matchbox-keyboard', '--help'],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
            else:
                return False

            # Wait briefly then kill the process
            time.sleep(0.5)
            startup_check.terminate()
            return_code = startup_check.wait(timeout=1)

            logger.info(f"Keyboard availability check completed with return code: {return_code}")
            return True
        except Exception as e:
            logger.error(f"Error checking keyboard availability: {e}")
            if isinstance(e, FileNotFoundError):
                logger.warning(f"Keyboard {self.keyboard_type} was found by 'which' but can't be executed.")
                self.keyboard_type = None
            return False

    def _detect_keyboard(self):
        """Detect which virtual keyboard is installed on the system.

        Returns:
            str: The keyboard type ('squeekboard', 'onboard', 'matchbox-keyboard', or None)
        """
        # If not on Linux, return None as on-screen keyboards are primarily for Linux-based systems
        if not sys.platform.startswith('linux'):
            logger.info("Not on Linux platform, on-screen keyboard detection skipped")
            return None

        # Check environment variable override
        env_keyboard = os.environ.get('CONSULTEASE_KEYBOARD', None)
        if env_keyboard:
            logger.info(f"Using keyboard specified in environment: {env_keyboard}")
            return env_keyboard

        # Check for each supported keyboard in order of preference
        keyboards = ['squeekboard', 'onboard', 'matchbox-keyboard']

        # Log all available keyboards for debugging
        logger.info("Checking for available on-screen keyboards...")

        for keyboard in keyboards:
            try:
                result = subprocess.run(['which', keyboard],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                if result.returncode == 0:
                    keyboard_path = result.stdout.decode('utf-8').strip()
                    logger.info(f"Found virtual keyboard: {keyboard} at {keyboard_path}")
                    return keyboard
                else:
                    logger.info(f"Keyboard not found: {keyboard}")
            except Exception as e:
                logger.debug(f"Error checking for keyboard {keyboard}: {e}")

        logger.warning("No supported virtual keyboard found")
        return None

    def eventFilter(self, obj, event):
        """Filter events to detect focus changes in text input widgets.

        Args:
            obj: The object that received the event
            event: The event

        Returns:
            bool: True if the event was handled and should be filtered out
        """
        # Check for explicit keyboardOnFocus property
        should_show_keyboard = False
        has_explicit_property = False

        if event.type() == QEvent.FocusIn:
            # Check for explicit keyboard property
            if hasattr(obj, 'property') and callable(getattr(obj, 'property')):
                try:
                    if obj.property("keyboardOnFocus"):
                        has_explicit_property = True
                        should_show_keyboard = True
                        if self.debug_mode:
                            logger.debug(f"Widget has explicit keyboardOnFocus property: {obj}")
                except Exception as e:
                    if self.debug_mode:
                        logger.debug(f"Error checking keyboardOnFocus property: {e}")

            # Check standard input widgets
            if isinstance(obj, QLineEdit) or isinstance(obj, QTextEdit):
                should_show_keyboard = True
                if self.debug_mode:
                    logger.debug(f"Input widget received focus: {obj.__class__.__name__}")

        # Handle focus in events for text input widgets
        if event.type() == QEvent.FocusIn and should_show_keyboard:
            if self.debug_mode:
                logger.debug(f"Focus in event for widget: {obj.__class__.__name__}")

            self.current_focus_widget = obj
            # Delay keyboard showing slightly to avoid rapid show/hide cycles
            if not self.keyboard_timer.isActive() and not self.keyboard_visible:
                if self.debug_mode:
                    logger.debug(f"Starting keyboard timer for widget: {obj.__class__.__name__}")
                self.keyboard_timer.start(200)  # 200ms delay

                # For squeekboard, we need to manually trigger it
                if self.keyboard_type == 'squeekboard':
                    # Try dbus method first (more reliable)
                    self._trigger_squeekboard_dbus()

        # Handle focus out events for text input widgets
        elif event.type() == QEvent.FocusOut and obj == self.current_focus_widget:
            if self.debug_mode:
                logger.debug(f"Focus out event for widget: {obj.__class__.__name__}")

            # Get the new focus widget
            focus_widget = QApplication.focusWidget()

            # Only hide keyboard if focus is not moving to another text input
            hide_keyboard = True

            if focus_widget:
                # Check if the new widget should show keyboard
                new_should_show = False

                # Check for explicit property
                if hasattr(focus_widget, 'property') and callable(getattr(focus_widget, 'property')):
                    try:
                        if focus_widget.property("keyboardOnFocus"):
                            new_should_show = True
                    except:
                        pass

                # Check if it's a standard input widget
                if isinstance(focus_widget, QLineEdit) or isinstance(focus_widget, QTextEdit):
                    new_should_show = True

                if new_should_show:
                    hide_keyboard = False
                    self.current_focus_widget = focus_widget
                    if self.debug_mode:
                        logger.debug(f"Focus moved to another input widget: {focus_widget.__class__.__name__}")

            if hide_keyboard:
                if self.debug_mode:
                    logger.debug("Hiding keyboard as focus moved to non-input widget")
                self.hide_keyboard()
                self.current_focus_widget = None

        # Detect clicks on the viewport which might be useful for keyboard control
        elif event.type() == QEvent.MouseButtonPress:
            # Log for debug
            if self.debug_mode:
                if isinstance(obj, QWidget):
                    logger.debug(f"Mouse press on widget: {obj.__class__.__name__}")

        # Pass the event along
        return super(KeyboardHandler, self).eventFilter(obj, event)

    def _trigger_squeekboard_dbus(self):
        """Attempt to show squeekboard via DBus (most reliable method on Linux)"""
        if sys.platform.startswith('linux') and self.keyboard_type == 'squeekboard':
            try:
                # Try to use dbus-send to force the keyboard
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:true"
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.debug("Sent dbus command to show squeekboard")
                return True
            except Exception as e:
                logger.debug(f"Error triggering squeekboard via dbus: {e}")
                return False
        return False

    def _delayed_show_keyboard(self):
        """Show keyboard after a short delay to prevent flicker"""
        if self.current_focus_widget and self.current_focus_widget.isVisible():
            if self.debug_mode:
                logger.debug("Delayed keyboard show triggered")
            self.show_keyboard()

    def show_keyboard(self):
        """Show the appropriate virtual keyboard."""
        if not self.keyboard_type:
            if self.debug_mode:
                logger.debug("Cannot show keyboard - no supported keyboard installed")
            return

        # Don't start another instance if already marked as visible
        if self.keyboard_visible:
            if self.debug_mode:
                logger.debug("Keyboard already visible")
            return

        # Check if process exists and is still running
        if self.keyboard_process:
            try:
                if self.keyboard_process.poll() is None:
                    if self.debug_mode:
                        logger.debug("Keyboard process still running")
                    self.keyboard_visible = True
                    return
            except Exception:
                # Process might be invalid, create a new one
                self.keyboard_process = None

        try:
            logger.info(f"Starting virtual keyboard: {self.keyboard_type}")

            if self.keyboard_type == 'squeekboard':
                # Try dbus method first (most reliable on Raspberry Pi OS)
                if not self._trigger_squeekboard_dbus():
                    # Use more robust method to launch squeekboard
                    self.keyboard_process = subprocess.Popen(
                        ['squeekboard'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=dict(os.environ, SQUEEKBOARD_FORCE="1"),
                        start_new_session=True  # Ensure it runs in its own session
                    )
            elif self.keyboard_type == 'onboard':
                # Onboard with more appropriate options for touch screens
                self.keyboard_process = subprocess.Popen(
                    ['onboard', '--size=small', '--layout=Phone', '--enable-background-transparency'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif self.keyboard_type == 'matchbox-keyboard':
                self.keyboard_process = subprocess.Popen(
                    ['matchbox-keyboard'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            self.keyboard_visible = True
            logger.info(f"Virtual keyboard started: {self.keyboard_type}")
        except Exception as e:
            logger.error(f"Failed to start virtual keyboard: {e}")
            self.keyboard_visible = False

    def hide_keyboard(self):
        """Hide the virtual keyboard."""
        if not self.keyboard_visible and not self.keyboard_process:
            return

        logger.info("Hiding virtual keyboard")

        # For squeekboard, try dbus method first
        if self.keyboard_type == 'squeekboard':
            try:
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:false"
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.keyboard_visible = False
                return
            except Exception as e:
                logger.debug(f"Error hiding squeekboard via dbus: {e}")
                # Fall through to process termination

        try:
            # Check if process is still running
            if self.keyboard_process and self.keyboard_process.poll() is None:
                # Try gentle termination first
                self.keyboard_process.terminate()

                # Wait briefly for termination
                try:
                    self.keyboard_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    # Force kill if not terminated
                    if self.keyboard_process.poll() is None:
                        try:
                            self.keyboard_process.kill()
                        except:
                            # On Linux, try using os.killpg as last resort
                            if hasattr(os, 'killpg'):
                                try:
                                    os.killpg(os.getpgid(self.keyboard_process.pid), signal.SIGKILL)
                                except:
                                    pass

                logger.info("Virtual keyboard terminated")
        except Exception as e:
            logger.error(f"Error terminating virtual keyboard: {e}")

        self.keyboard_process = None
        self.keyboard_visible = False

    def force_show_keyboard(self):
        """
        Force the keyboard to show regardless of focus state.
        This is useful for windows that need the keyboard to appear immediately.
        """
        logger.info("Force showing keyboard")

        # For squeekboard, use DBus method
        if self.keyboard_type == 'squeekboard':
            self._trigger_squeekboard_dbus()

        # Also use the normal show method as a backup
        self.show_keyboard()

        # Set the visible flag
        self.keyboard_visible = True

def install_keyboard_handler(app):
    """Install the keyboard handler for the application.

    Args:
        app: QApplication instance

    Returns:
        KeyboardHandler: The installed keyboard handler instance
    """
    handler = KeyboardHandler()

    # Install event filter on application to catch all events
    app.installEventFilter(handler)

    return handler