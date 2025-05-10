"""
Window transition effects for ConsultEase.
Provides smooth transitions between windows for a better user experience.
"""
import logging
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect

logger = logging.getLogger(__name__)

class WindowTransitionManager:
    """
    Manages transitions between windows with fade effects.
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
    
    def fade_out_in(self, current_window, next_window, on_finished=None):
        """
        Perform a fade out of current window followed by fade in of next window.
        
        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            on_finished (callable, optional): Callback to execute when transition completes
        """
        logger.info(f"Starting transition from {current_window.__class__.__name__} to {next_window.__class__.__name__}")
        
        self.current_window = current_window
        self.next_window = next_window
        
        # Prepare next window but keep it hidden
        next_window.setWindowOpacity(0.0)
        next_window.show()
        
        # Create fade out animation for current window
        fade_out = QPropertyAnimation(current_window, b"windowOpacity")
        fade_out.setDuration(self.duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutCubic)
        
        # When fade out completes, start fade in
        fade_out.finished.connect(lambda: self._start_fade_in(on_finished))
        
        # Start the animation
        self.current_animation = fade_out
        fade_out.start()
    
    def _start_fade_in(self, on_finished=None):
        """
        Start the fade in animation for the next window.
        
        Args:
            on_finished (callable, optional): Callback to execute when transition completes
        """
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
    
    def fade_in(self, window, on_finished=None):
        """
        Perform a fade in effect on a window.
        
        Args:
            window (QWidget): The window to fade in
            on_finished (callable, optional): Callback to execute when fade completes
        """
        logger.info(f"Fading in {window.__class__.__name__}")
        
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
    
    def fade_out(self, window, on_finished=None):
        """
        Perform a fade out effect on a window.
        
        Args:
            window (QWidget): The window to fade out
            on_finished (callable, optional): Callback to execute when fade completes
        """
        logger.info(f"Fading out {window.__class__.__name__}")
        
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
