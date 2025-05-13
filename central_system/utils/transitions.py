"""
Window transition effects for ConsultEase.
Provides smooth transitions between windows for a better user experience.
Compatible with Wayland and other window systems that don't support opacity.
"""
import logging
import sys
import os
import platform
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt, QRect
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect, QApplication

logger = logging.getLogger(__name__)

class WindowTransitionManager:
    """
    Manages transitions between windows with compatible effects.
    """

    def __init__(self, duration=300):
        """
        Initialize the transition manager.

        Args:
            duration (int): Duration of transitions in milliseconds
        """
        self.duration = duration
        self.current_animation = None
        self.next_window = None
        self.current_window = None

        # Detect if we're on Wayland or another system with limitations
        self.use_simple_transitions = self._should_use_simple_transitions()
        logger.info(f"Using simple transitions: {self.use_simple_transitions}")

    def _should_use_simple_transitions(self):
        """Determine if we should use simple transitions based on platform."""
        # Check environment variable override
        if "CONSULTEASE_USE_TRANSITIONS" in os.environ:
            use_simple = os.environ["CONSULTEASE_USE_TRANSITIONS"].lower() == "false"
            logger.info(f"Using transition setting from environment: {not use_simple}")
            return use_simple

        # Check if we're on Linux and possibly using Wayland
        if sys.platform.startswith('linux'):
            # Check for Wayland environment variables
            for env_var in ['WAYLAND_DISPLAY', 'XDG_SESSION_TYPE']:
                if env_var in os.environ and 'wayland' in os.environ[env_var].lower():
                    logger.info("Detected Wayland session, using simple transitions")
                    return True

            # Check QT_QPA_PLATFORM
            if 'QT_QPA_PLATFORM' in os.environ and 'wayland' in os.environ['QT_QPA_PLATFORM'].lower():
                logger.info("Detected Wayland QPA platform, using simple transitions")
                return True

        # Check if we're on Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    logger.info("Detected Raspberry Pi, using simple transitions")
                    return True
        except:
            pass

        # Check if we're on Windows
        if sys.platform.startswith('win'):
            # Windows generally supports opacity animations well
            logger.info("Detected Windows platform, using advanced transitions")
            return False

        # Check if we're on macOS
        if sys.platform.startswith('darwin'):
            # macOS generally supports opacity animations well
            logger.info("Detected macOS platform, using advanced transitions")
            return False

        # Default to simple transitions for safety on unknown platforms
        logger.info("Unknown platform, defaulting to simple transitions for safety")
        return True

    def fade_out_in(self, current_window, next_window, on_finished=None):
        """
        Perform a transition from current window to next window.

        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            on_finished (callable, optional): Callback to execute when transition completes
        """
        logger.info(f"Starting transition from {current_window.__class__.__name__} to {next_window.__class__.__name__}")

        self.current_window = current_window
        self.next_window = next_window

        # Always ensure next window is ready to be shown but initially invisible
        if not self.use_simple_transitions:
            next_window.setWindowOpacity(0.0)
        next_window.show()
        next_window.raise_()  # Ensure it's on top

        # Set a failsafe timer to ensure transition completes
        QTimer.singleShot(self.duration * 2, lambda: self._ensure_transition_completed(next_window))

        if self.use_simple_transitions:
            # Simple transition with a slide effect
            try:
                # Get the screen geometry
                screen_width = current_window.width()

                # Position the next window off-screen to the right
                next_window_pos = next_window.pos()
                next_window.move(screen_width, next_window_pos.y())

                # Create animation to slide in the next window
                slide_in = QPropertyAnimation(next_window, b"pos")
                slide_in.setDuration(self.duration)
                slide_in.setStartValue(next_window.pos())
                slide_in.setEndValue(next_window_pos)
                slide_in.setEasingCurve(QEasingCurve.OutCubic)

                # Start the animation
                slide_in.start()

                # Hide the current window after a short delay
                QTimer.singleShot(int(self.duration * 0.5), lambda: current_window.hide())

                # Call on_finished after transition duration
                if on_finished:
                    QTimer.singleShot(self.duration, on_finished)
            except Exception as e:
                logger.warning(f"Slide animation failed, using simple transition: {e}")
                # Fall back to very simple transition
                QTimer.singleShot(100, lambda: current_window.hide())
                if on_finished:
                    QTimer.singleShot(self.duration, on_finished)
        else:
            try:
                # Try opacity-based transition with cross-fade
                # Create fade out animation for current window
                fade_out = QPropertyAnimation(current_window, b"windowOpacity")
                fade_out.setDuration(int(self.duration * 1.2))  # Slightly longer for overlap
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.OutCubic)

                # Create fade in animation for next window
                fade_in = QPropertyAnimation(next_window, b"windowOpacity")
                fade_in.setDuration(self.duration)
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(QEasingCurve.InCubic)

                # Start fade in after a short delay for cross-fade effect
                QTimer.singleShot(int(self.duration * 0.3), fade_in.start)

                # When fade out completes, hide the window
                def on_fade_out_finished():
                    current_window.hide()
                    current_window.setWindowOpacity(1.0)  # Reset for future use

                    # Call on_finished when both animations are done
                    if on_finished and fade_in.state() == QPropertyAnimation.Stopped:
                        on_finished()

                # When fade in completes, call on_finished if fade_out is done
                def on_fade_in_finished():
                    if on_finished and fade_out.state() == QPropertyAnimation.Stopped:
                        on_finished()

                fade_out.finished.connect(on_fade_out_finished)
                fade_in.finished.connect(on_fade_in_finished)

                # Start the fade out animation
                self.current_animation = fade_out
                fade_out.start()
            except Exception as e:
                logger.warning(f"Opacity animation failed, falling back to simple transition: {e}")
                # Fall back to simple transition
                current_window.hide()
                next_window.setWindowOpacity(1.0)  # Ensure next window is fully visible
                if on_finished:
                    QTimer.singleShot(self.duration, on_finished)

    def _start_fade_in(self, on_finished=None):
        """
        Start the fade in animation for the next window.

        Args:
            on_finished (callable, optional): Callback to execute when transition completes
        """
        try:
            # Hide the previous window
            if self.current_window:
                self.current_window.hide()
                # Reset opacity for future use
                self.current_window.setWindowOpacity(1.0)

            # Create fade in animation for next window
            fade_in = QPropertyAnimation(self.next_window, b"windowOpacity")
            fade_in.setDuration(self.duration)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.InCubic)

            # Connect finished signal
            if on_finished:
                fade_in.finished.connect(on_finished)

            # Start the animation
            self.current_animation = fade_in
            fade_in.start()
        except Exception as e:
            logger.warning(f"Fade in animation failed: {e}")
            # Ensure window is visible
            self.next_window.setWindowOpacity(1.0)
            if on_finished:
                on_finished()

    def fade_in(self, window, on_finished=None):
        """
        Perform a fade in effect on a window.

        Args:
            window (QWidget): The window to fade in
            on_finished (callable, optional): Callback to execute when fade completes
        """
        logger.info(f"Fading in {window.__class__.__name__}")

        if self.use_simple_transitions:
            # Simple show
            window.show()
            if on_finished:
                QTimer.singleShot(self.duration, on_finished)
        else:
            try:
                # Prepare window
                window.setWindowOpacity(0.0)
                window.show()

                # Create fade in animation
                fade_in = QPropertyAnimation(window, b"windowOpacity")
                fade_in.setDuration(self.duration)
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(QEasingCurve.InCubic)

                # Connect finished signal
                if on_finished:
                    fade_in.finished.connect(on_finished)

                # Start the animation
                self.current_animation = fade_in
                fade_in.start()
            except Exception as e:
                logger.warning(f"Fade in animation failed, using simple show: {e}")
                window.show()
                if on_finished:
                    QTimer.singleShot(self.duration, on_finished)

    def fade_out(self, window, on_finished=None):
        """
        Perform a fade out effect on a window.

        Args:
            window (QWidget): The window to fade out
            on_finished (callable, optional): Callback to execute when fade completes
        """
        logger.info(f"Fading out {window.__class__.__name__}")

        if self.use_simple_transitions:
            # Simple hide
            window.hide()
            if on_finished:
                QTimer.singleShot(self.duration, on_finished)
        else:
            try:
                # Create fade out animation
                fade_out = QPropertyAnimation(window, b"windowOpacity")
                fade_out.setDuration(self.duration)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.OutCubic)

                # When fade out completes, hide the window and reset opacity
                def on_fade_out_finished():
                    window.hide()
                    window.setWindowOpacity(1.0)
                    if on_finished:
                        on_finished()

                fade_out.finished.connect(on_fade_out_finished)

                # Start the animation
                self.current_animation = fade_out
                fade_out.start()
            except Exception as e:
                logger.warning(f"Fade out animation failed, using simple hide: {e}")
                window.hide()
                if on_finished:
                    QTimer.singleShot(self.duration, on_finished)

    def _ensure_transition_completed(self, next_window):
        """
        Failsafe method to ensure transition completes properly.
        This is called after a timeout to make sure the window is visible.

        Args:
            next_window (QWidget): The window that should be visible after transition
        """
        if next_window:
            # Check if window is visible and has proper opacity
            if not next_window.isVisible():
                logger.warning("Transition failsafe: Window not visible, forcing visibility")
                next_window.show()
                next_window.raise_()
                next_window.activateWindow()

            # Ensure opacity is set to 1.0 (fully visible)
            if hasattr(next_window, 'windowOpacity') and next_window.windowOpacity() < 1.0:
                logger.warning("Transition failsafe: Window opacity not 1.0, resetting")
                next_window.setWindowOpacity(1.0)

            # If current_window is still visible, hide it
            if self.current_window and self.current_window.isVisible():
                logger.warning("Transition failsafe: Previous window still visible, hiding")
                self.current_window.hide()
