import os
import subprocess
import logging
import signal
import time
import sys
import json
import threading
from PyQt5.QtCore import QObject, QEvent, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QWidget
from PyQt5.QtGui import QGuiApplication

logger = logging.getLogger(__name__)

class KeyboardHandler(QObject):
    """
    Enhanced handler for virtual keyboard management on touchscreen interfaces.

    This class manages the auto-showing of on-screen keyboards when text input
    fields receive focus, and hiding them when focus is lost. It supports
    multiple virtual keyboard implementations with special focus on squeekboard.
    """
    # Signal emitted when keyboard visibility changes
    keyboard_visibility_changed = pyqtSignal(bool)

    # List of widget types that should trigger the keyboard
    INPUT_WIDGET_TYPES = (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox)

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
        self.keyboard_status_check_time = 0
        self.dbus_available = self._check_dbus_available()

        # Timer to add a slight delay for keyboard appearance
        self.keyboard_timer = QTimer(self)
        self.keyboard_timer.setSingleShot(True)
        self.keyboard_timer.timeout.connect(self._delayed_show_keyboard)

        # Timer for periodic status checks
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._check_keyboard_status)
        self.status_timer.start(5000)  # Check every 5 seconds

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

        # Start a thread to monitor squeekboard status if using squeekboard
        if self.keyboard_type == 'squeekboard' and self.dbus_available:
            self._start_squeekboard_monitor()

    def _set_keyboard_environment(self):
        """Set environment variables to help with keyboard detection and usage"""
        # Set environment variables to ensure keyboard backends work properly
        if sys.platform.startswith('linux'):
            os.environ["GDK_BACKEND"] = "wayland,x11"
            os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

            # Set environment variables for squeekboard (primary)
            os.environ["SQUEEKBOARD_FORCE"] = "1"
            os.environ["MOZ_ENABLE_WAYLAND"] = "1"
            os.environ["QT_IM_MODULE"] = "wayland"
            os.environ["CLUTTER_IM_MODULE"] = "wayland"

            # Set environment variables for onboard (fallback)
            os.environ["ONBOARD_ENABLE_TOUCH"] = "1"
            os.environ["ONBOARD_XEMBED"] = "1"

            # Check if we're running as root and warn if so
            if os.geteuid() == 0:
                logger.warning("Running as root may affect keyboard detection. Consider running as normal user.")

    def _ensure_keyboard_service(self):
        """Ensure the keyboard service is running properly on system"""
        if not sys.platform.startswith('linux'):
            return

        # Handle squeekboard (preferred)
        if self.keyboard_type == 'squeekboard':
            try:
                # First check if squeekboard is already running as a process
                check_cmd = "pgrep -f squeekboard"
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info("Squeekboard is already running as a process")
                    return

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
                        logger.warning("Failed to start squeekboard service, trying direct launch")
                        # Try starting squeekboard directly
                        subprocess.Popen(['squeekboard'],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,
                                       env=dict(os.environ, SQUEEKBOARD_FORCE="1"),
                                       start_new_session=True)
                        logger.info("Started squeekboard directly")
                else:
                    logger.info("Squeekboard service is already running")

                # Create autostart entry for squeekboard if it doesn't exist
                try:
                    autostart_path = os.path.expanduser("~/.config/autostart/squeekboard-autostart.desktop")
                    if not os.path.exists(autostart_path):
                        # Create autostart entry
                        os.makedirs(os.path.dirname(autostart_path), exist_ok=True)
                        with open(autostart_path, 'w') as f:
                            f.write("""[Desktop Entry]
Type=Application
Name=Squeekboard
Exec=squeekboard
Comment=On-screen keyboard for Wayland
X-GNOME-Autostart-enabled=true
""")
                        logger.info("Created squeekboard autostart configuration")

                        # Disable onboard autostart if it exists
                        onboard_autostart = os.path.expanduser("~/.config/autostart/onboard-autostart.desktop")
                        if os.path.exists(onboard_autostart):
                            try:
                                os.rename(onboard_autostart, onboard_autostart + ".disabled")
                                logger.info("Disabled onboard autostart")
                            except Exception as e:
                                logger.debug(f"Error disabling onboard autostart: {e}")
                except Exception as e:
                    logger.debug(f"Error setting up squeekboard autostart: {e}")
            except Exception as e:
                logger.error(f"Error ensuring squeekboard service: {e}")

                # Try direct launch as last resort
                try:
                    subprocess.Popen(['squeekboard'],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   env=dict(os.environ, SQUEEKBOARD_FORCE="1"),
                                   start_new_session=True)
                    logger.info("Started squeekboard directly as last resort")
                except Exception as e2:
                    logger.error(f"Failed to start squeekboard: {e2}")

        # Handle onboard (fallback)
        elif self.keyboard_type == 'onboard':
            try:
                # Check if onboard is already running
                check_cmd = "pgrep -f onboard"
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

                if result.returncode != 0:
                    logger.info("Onboard not running, attempting to start it...")
                    # Try to start onboard
                    try:
                        # Check if onboard is in autostart
                        autostart_path = os.path.expanduser("~/.config/autostart/onboard-autostart.desktop")
                        if os.path.exists(autostart_path):
                            logger.info("Onboard autostart configuration found")
                        else:
                            # Create autostart entry
                            os.makedirs(os.path.dirname(autostart_path), exist_ok=True)
                            with open(autostart_path, 'w') as f:
                                f.write("""[Desktop Entry]
Type=Application
Name=Onboard
Exec=onboard --size=small --layout=Phone --enable-background-transparency --theme=Nightshade
Comment=Flexible on-screen keyboard
""")

                            # Create onboard configuration directory
                            try:
                                config_dir = os.path.expanduser("~/.config/onboard")
                                os.makedirs(config_dir, exist_ok=True)

                                # Create onboard configuration file with touch-friendly settings
                                config_path = os.path.join(config_dir, "onboard.conf")
                                with open(config_path, 'w') as f:
                                    f.write("""[main]
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
""")
                                logger.info("Created onboard configuration file")
                            except Exception as e:
                                logger.debug(f"Error setting up onboard configuration: {e}")
                            logger.info("Created onboard autostart configuration")
                    except Exception as e:
                        logger.debug(f"Error setting up onboard autostart: {e}")
                else:
                    logger.info("Onboard is already running")
            except Exception as e:
                logger.error(f"Error checking/starting onboard: {e}")

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
        # Prioritize squeekboard over onboard
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

        if event.type() == QEvent.FocusIn:
            # Check for explicit keyboard property
            if hasattr(obj, 'property') and callable(getattr(obj, 'property')):
                try:
                    # First check for explicit keyboard control
                    if obj.property("keyboardOnFocus") is not None:
                        # Use the explicit property value (True or False)
                        should_show_keyboard = bool(obj.property("keyboardOnFocus"))
                        if self.debug_mode:
                            logger.debug(f"Widget has explicit keyboardOnFocus={should_show_keyboard}: {obj}")
                except Exception as e:
                    if self.debug_mode:
                        logger.debug(f"Error checking keyboardOnFocus property: {e}")

            # If no explicit property, check if it's a standard input widget
            if not should_show_keyboard:
                for widget_type in self.INPUT_WIDGET_TYPES:
                    if isinstance(obj, widget_type):
                        should_show_keyboard = True
                        if self.debug_mode:
                            logger.debug(f"Input widget received focus: {obj.__class__.__name__}")
                        break

            # Special handling for custom widgets that might contain input fields
            if not should_show_keyboard and hasattr(obj, 'focusWidget') and callable(getattr(obj, 'focusWidget')):
                try:
                    inner_focus = obj.focusWidget()
                    if inner_focus:
                        for widget_type in self.INPUT_WIDGET_TYPES:
                            if isinstance(inner_focus, widget_type):
                                should_show_keyboard = True
                                if self.debug_mode:
                                    logger.debug(f"Container widget has input focus: {inner_focus.__class__.__name__}")
                                break
                except Exception as e:
                    if self.debug_mode:
                        logger.debug(f"Error checking inner focus widget: {e}")

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
                # For onboard, we'll let the timer handle it
            elif self.keyboard_type == 'squeekboard' and not self._is_squeekboard_visible():
                # If keyboard should be visible but isn't, force it
                logger.debug("Keyboard should be visible but isn't - forcing it to show")
                self._trigger_squeekboard_dbus()
            elif self.keyboard_type == 'onboard':
                # For onboard, make sure it's running
                self.show_keyboard()

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
                        if focus_widget.property("keyboardOnFocus") is not None:
                            new_should_show = bool(focus_widget.property("keyboardOnFocus"))
                    except Exception:
                        pass

                # Check if it's a standard input widget
                if not new_should_show:
                    for widget_type in self.INPUT_WIDGET_TYPES:
                        if isinstance(focus_widget, widget_type):
                            new_should_show = True
                            break

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

        # Detect clicks on input widgets that might need keyboard
        elif event.type() == QEvent.MouseButtonPress:
            # Check if the clicked widget is an input that should show keyboard
            clicked_should_show = False

            # Check for explicit property
            if hasattr(obj, 'property') and callable(getattr(obj, 'property')):
                try:
                    if obj.property("keyboardOnFocus") is not None:
                        clicked_should_show = bool(obj.property("keyboardOnFocus"))
                except Exception:
                    pass

            # Check if it's a standard input widget
            if not clicked_should_show:
                for widget_type in self.INPUT_WIDGET_TYPES:
                    if isinstance(obj, widget_type):
                        clicked_should_show = True
                        break

            # If it's an input widget and keyboard isn't visible, show it
            if clicked_should_show and not self.keyboard_visible:
                if self.debug_mode:
                    logger.debug(f"Mouse click on input widget: {obj.__class__.__name__}")
                if self.keyboard_type == 'squeekboard':
                    self._trigger_squeekboard_dbus()
                elif self.keyboard_type == 'onboard':
                    self.show_keyboard()

        # Pass the event along
        return super(KeyboardHandler, self).eventFilter(obj, event)

    def _check_dbus_available(self):
        """Check if DBus is available for squeekboard communication"""
        if not sys.platform.startswith('linux'):
            return False

        try:
            # Check if dbus-send is available
            result = subprocess.run(['which', 'dbus-send'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Error checking DBus availability: {e}")
            return False

    def _start_squeekboard_monitor(self):
        """Start a thread to monitor squeekboard status"""
        def monitor_thread():
            while True:
                try:
                    # Check if squeekboard is visible
                    current_visible = self._is_squeekboard_visible()

                    # If our internal state doesn't match reality, update it
                    if current_visible != self.keyboard_visible:
                        logger.debug(f"Keyboard visibility mismatch detected: internal={self.keyboard_visible}, actual={current_visible}")
                        self.keyboard_visible = current_visible
                        self.keyboard_visibility_changed.emit(current_visible)

                except Exception as e:
                    if self.debug_mode:
                        logger.debug(f"Error in squeekboard monitor thread: {e}")

                # Sleep to avoid excessive CPU usage
                time.sleep(1)

        # Start the monitor thread
        monitor = threading.Thread(target=monitor_thread, daemon=True)
        monitor.start()
        logger.debug("Started squeekboard monitor thread")

    def _is_squeekboard_visible(self):
        """Check if squeekboard is currently visible via DBus"""
        if not self.dbus_available or self.keyboard_type != 'squeekboard':
            return self.keyboard_visible

        try:
            # Use dbus-send to query keyboard visibility
            cmd = [
                "dbus-send", "--print-reply", "--type=method_call",
                "--dest=sm.puri.OSK0", "/sm/puri/OSK0",
                "sm.puri.OSK0.GetVisible"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Parse the result
            if "boolean true" in result.stdout:
                return True
            elif "boolean false" in result.stdout:
                return False
            else:
                logger.debug(f"Unexpected response from squeekboard GetVisible: {result.stdout}")
                return self.keyboard_visible
        except Exception as e:
            logger.debug(f"Error checking squeekboard visibility: {e}")
            return self.keyboard_visible

    def integrate_with_webview(self, webview):
        """
        Integrate keyboard handling with a QWebEngineView.
        This allows the keyboard to be shown when input fields in the web view are focused.

        Args:
            webview: The QWebEngineView to integrate with
        """
        if not webview:
            logger.warning("Cannot integrate with None webview")
            return

        logger.info(f"Integrating keyboard handler with webview: {webview}")

        try:
            # Add JavaScript files to the web view
            js_files = [
                "keyboard_focus.js",
                "keyboard_integration.js"
            ]

            # Get the base URL for static files
            import os
            base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            static_dir = os.path.join(base_dir, 'static', 'js')

            # Create a bridge object to communicate with JavaScript
            from PyQt5.QtWebChannel import QWebChannel
            from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

            class WebBridge(QObject):
                # Signals
                keyboardRequested = pyqtSignal()
                keyboardHidden = pyqtSignal()

                def __init__(self, keyboard_handler, parent=None):
                    super().__init__(parent)
                    self.keyboard_handler = keyboard_handler

                @pyqtSlot()
                def showKeyboard(self):
                    """Show the keyboard when requested from JavaScript"""
                    logger.info("Keyboard show requested from JavaScript")
                    if self.keyboard_handler:
                        self.keyboard_handler.show_keyboard()
                        self.keyboardRequested.emit()

                @pyqtSlot()
                def hideKeyboard(self):
                    """Hide the keyboard when requested from JavaScript"""
                    logger.info("Keyboard hide requested from JavaScript")
                    if self.keyboard_handler:
                        self.keyboard_handler.hide_keyboard()
                        self.keyboardHidden.emit()

                @pyqtSlot(str)
                def inputFocused(self, element_info):
                    """Handle input field focus in the web view"""
                    logger.info(f"Input field focused in web view: {element_info}")
                    if self.keyboard_handler:
                        self.keyboard_handler.show_keyboard()

                @pyqtSlot(str)
                def inputBlurred(self, element_info):
                    """Handle input field blur in the web view"""
                    logger.info(f"Input field blurred in web view: {element_info}")
                    # Don't hide keyboard on blur, let it be handled manually

            # Create the bridge object
            bridge = WebBridge(self)

            # Create a web channel
            channel = QWebChannel(webview)
            channel.registerObject("keyboardBridge", bridge)

            # Set the web channel on the web view
            webview.page().setWebChannel(channel)

            # Inject the JavaScript files
            for js_file in js_files:
                js_path = os.path.join(static_dir, js_file)
                if os.path.exists(js_path):
                    with open(js_path, 'r') as f:
                        js_code = f.read()
                        webview.page().runJavaScript(js_code)
                        logger.info(f"Injected {js_file} into webview")
                else:
                    logger.warning(f"JavaScript file not found: {js_path}")

            # Initialize the keyboard integration
            init_js = """
            if (typeof initKeyboardIntegration === 'function') {
                initKeyboardIntegration(keyboardBridge);
                console.log('Keyboard integration initialized');
            } else {
                console.error('initKeyboardIntegration function not found');
            }
            """
            webview.page().runJavaScript(init_js)

            logger.info("Keyboard integration with webview completed")

        except Exception as e:
            logger.error(f"Error integrating keyboard with webview: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _check_keyboard_status(self):
        """Periodically check keyboard status and ensure it's running"""
        # Only check every 5 seconds to avoid excessive overhead
        current_time = time.time()
        if current_time - self.keyboard_status_check_time < 5:
            return

        self.keyboard_status_check_time = current_time

        # Ensure the appropriate keyboard service is running
        self._ensure_keyboard_service()

        # For squeekboard, check visibility via DBus
        if self.keyboard_type == 'squeekboard':
            # If keyboard should be visible but isn't, try to show it
            if self.keyboard_visible and not self._is_squeekboard_visible() and self.current_focus_widget:
                logger.debug("Keyboard should be visible but isn't - attempting to show it")
                self._trigger_squeekboard_dbus()

        # For onboard, check if it's running
        elif self.keyboard_type == 'onboard' and self.keyboard_visible:
            try:
                # Check if onboard is running
                check_cmd = "pgrep -f onboard"
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

                # If not running but should be visible, restart it
                if result.returncode != 0 and self.current_focus_widget:
                    logger.debug("Onboard should be visible but isn't running - attempting to start it")
                    self.show_keyboard()
            except Exception as e:
                logger.debug(f"Error checking onboard status: {e}")

    def _trigger_squeekboard_dbus(self):
        """
        Attempt to show squeekboard via DBus (most reliable method on Linux).
        This method has been enhanced to be more robust and handle various edge cases.
        """
        if sys.platform.startswith('linux') and self.keyboard_type == 'squeekboard' and self.dbus_available:
            try:
                # First, ensure squeekboard service is running
                try:
                    # Check if squeekboard service is running
                    check_cmd = "systemctl --user is-active squeekboard.service"
                    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

                    if "inactive" in result.stdout or "failed" in result.stdout:
                        logger.info("Squeekboard service not running, attempting to start it...")
                        start_cmd = "systemctl --user start squeekboard.service"
                        subprocess.run(start_cmd, shell=True)

                        # Give it a moment to start
                        time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"Error checking squeekboard service: {e}")

                # Try to use dbus-send to force the keyboard
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:true"
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.debug("Sent dbus command to show squeekboard")

                # Try an alternative method as well (for some systems)
                try:
                    alt_cmd = [
                        "gdbus", "call", "--session", "--dest=sm.puri.OSK0",
                        "--object-path=/sm/puri/OSK0", "--method=sm.puri.OSK0.SetVisible", "true"
                    ]
                    subprocess.Popen(alt_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.debug("Sent gdbus command to show squeekboard")
                except Exception:
                    pass

                # Also try using the keyboard-show.sh script if it exists
                try:
                    home_dir = os.path.expanduser("~")
                    script_path = os.path.join(home_dir, "keyboard-show.sh")
                    if os.path.exists(script_path):
                        logger.debug("Using keyboard-show.sh script")
                        subprocess.Popen([script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

                # Update our internal state
                self.keyboard_visible = True
                self.keyboard_visibility_changed.emit(True)

                # Verify that the keyboard is actually visible after a short delay
                QTimer.singleShot(500, self._verify_keyboard_visible)

                return True
            except Exception as e:
                logger.debug(f"Error triggering squeekboard via dbus: {e}")
                return False
        return False

    def _verify_keyboard_visible(self):
        """Verify that the keyboard is actually visible after a show request"""
        if self.keyboard_type == 'squeekboard' and self.dbus_available:
            is_visible = self._is_squeekboard_visible()
            if not is_visible and self.keyboard_visible:
                logger.debug("Keyboard should be visible but isn't - trying again")
                # Try again with more force
                try:
                    # Try direct process launch
                    subprocess.Popen(
                        ['squeekboard'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=dict(os.environ, SQUEEKBOARD_FORCE="1"),
                        start_new_session=True
                    )

                    # Try DBus again after a short delay
                    QTimer.singleShot(300, lambda: subprocess.Popen([
                        "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                        "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:true"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                except Exception as e:
                    logger.debug(f"Error in second attempt to show keyboard: {e}")

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

        # Don't start another instance if already marked as visible and actually is visible
        if self.keyboard_visible and (self.keyboard_type != 'squeekboard' or self._is_squeekboard_visible()):
            if self.debug_mode:
                logger.debug("Keyboard already visible")
            return

        # For squeekboard, always try DBus method first
        if self.keyboard_type == 'squeekboard' and self.dbus_available:
            if self._trigger_squeekboard_dbus():
                # Successfully shown via DBus
                return

        # Check if process exists and is still running
        if self.keyboard_process:
            try:
                if self.keyboard_process.poll() is None:
                    if self.debug_mode:
                        logger.debug("Keyboard process still running")
                    self.keyboard_visible = True
                    self.keyboard_visibility_changed.emit(True)
                    return
            except Exception:
                # Process might be invalid, create a new one
                self.keyboard_process = None

        try:
            logger.info(f"Starting virtual keyboard: {self.keyboard_type}")

            if self.keyboard_type == 'squeekboard':
                # Ensure the service is running
                self._ensure_keyboard_service()

                # Use more robust method to launch squeekboard
                self.keyboard_process = subprocess.Popen(
                    ['squeekboard'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=dict(os.environ, SQUEEKBOARD_FORCE="1"),
                    start_new_session=True  # Ensure it runs in its own session
                )

                # Try DBus method again after launching process
                QTimer.singleShot(500, self._trigger_squeekboard_dbus)

            elif self.keyboard_type == 'onboard':
                # Check if onboard is already running
                try:
                    check_cmd = "pgrep -f onboard"
                    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

                    if result.returncode != 0:
                        # Onboard with more appropriate options for touch screens
                        self.keyboard_process = subprocess.Popen(
                            ['onboard', '--size=small', '--layout=Phone', '--enable-background-transparency', '--theme=Nightshade'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                        logger.info("Started onboard with enhanced settings")
                    else:
                        logger.debug("Onboard is already running")
                except Exception as e:
                    logger.error(f"Error checking onboard status: {e}")
                    # Fallback to simple launch
                    self.keyboard_process = subprocess.Popen(
                        ['onboard', '--size=small', '--layout=Phone', '--enable-background-transparency', '--theme=Nightshade'],
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
            self.keyboard_visibility_changed.emit(True)
            logger.info(f"Virtual keyboard started: {self.keyboard_type}")
        except Exception as e:
            logger.error(f"Failed to start virtual keyboard: {e}")
            self.keyboard_visible = False

    def hide_keyboard(self):
        """Hide the virtual keyboard."""
        if not self.keyboard_visible and not self.keyboard_process:
            return

        logger.info("Hiding virtual keyboard")

        # For onboard, kill the process directly
        if self.keyboard_type == 'onboard':
            try:
                # Kill any running onboard processes
                subprocess.run(['pkill', '-f', 'onboard'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
                self.keyboard_visible = False
                self.keyboard_visibility_changed.emit(False)
                logger.info("Killed onboard process")
                return
            except Exception as e:
                logger.debug(f"Error killing onboard: {e}")
                # Fall through to process termination

        # For squeekboard, try dbus method first
        elif self.keyboard_type == 'squeekboard' and self.dbus_available:
            try:
                cmd = [
                    "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                    "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:false"
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.keyboard_visible = False
                self.keyboard_visibility_changed.emit(False)

                # Check if it actually hid
                QTimer.singleShot(500, self._verify_keyboard_hidden)
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
        self.keyboard_visibility_changed.emit(False)

    def _verify_keyboard_hidden(self):
        """Verify that the keyboard was actually hidden"""
        if self.keyboard_type == 'squeekboard' and self.dbus_available:
            is_visible = self._is_squeekboard_visible()
            if is_visible and self.debug_mode:
                logger.debug("Keyboard still visible after hide request - forcing hide")
                # Try again with more force
                try:
                    cmd = [
                        "dbus-send", "--type=method_call", "--dest=sm.puri.OSK0",
                        "/sm/puri/OSK0", "sm.puri.OSK0.SetVisible", "boolean:false"
                    ]
                    subprocess.run(cmd, check=True)
                except Exception as e:
                    logger.debug(f"Error in second attempt to hide keyboard: {e}")

    def force_show_keyboard(self):
        """
        Force the keyboard to show regardless of focus state.
        This is useful for windows that need the keyboard to appear immediately.
        """
        logger.info("Force showing keyboard")

        # For squeekboard, use DBus method
        if self.keyboard_type == 'squeekboard' and self.dbus_available:
            # Try multiple times with a slight delay to ensure it appears
            self._trigger_squeekboard_dbus()

            # Schedule another attempt after a short delay
            QTimer.singleShot(300, self._trigger_squeekboard_dbus)

            # And one more for good measure
            QTimer.singleShot(600, self._trigger_squeekboard_dbus)

        # For onboard, make multiple attempts
        elif self.keyboard_type == 'onboard':
            # Try to show keyboard multiple times
            self.show_keyboard()

            # Schedule additional attempts
            QTimer.singleShot(300, self.show_keyboard)
            QTimer.singleShot(600, self.show_keyboard)

        # Also use the normal show method as a backup
        self.show_keyboard()

        # Set the visible flag
        self.keyboard_visible = True
        self.keyboard_visibility_changed.emit(True)

        # Return success based on keyboard type
        return self.keyboard_type is not None

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