"""
Window transition utilities for ConsultEase.
Provides smooth transitions between windows for a better user experience.
"""
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint, QRect

logger = logging.getLogger(__name__)

class TransitionType:
    """Transition type constants."""
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"

class WindowTransition:
    """
    Handles smooth transitions between windows.
    """
    
    @staticmethod
    def transition(current_window, next_window, transition_type=TransitionType.FADE, duration=300):
        """
        Perform a transition between two windows.
        
        Args:
            current_window (QWidget): The currently visible window
            next_window (QWidget): The window to transition to
            transition_type (str): Type of transition to perform
            duration (int): Duration of the transition in milliseconds
            
        Returns:
            QParallelAnimationGroup: The animation group that was started
        """
        if not current_window or not next_window:
            logger.warning("Cannot perform transition: one or both windows are None")
            if next_window:
                next_window.show()
            return None
            
        # Ensure next window is ready but not visible yet
        next_window.setWindowOpacity(0.0)
        next_window.show()
        
        # Create animation group
        animation_group = QParallelAnimationGroup()
        
        # Add animations based on transition type
        if transition_type == TransitionType.FADE:
            # Fade out current window
            fade_out = QPropertyAnimation(current_window, b"windowOpacity")
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setDuration(duration)
            fade_out.setEasingCurve(QEasingCurve.OutCubic)
            
            # Fade in next window
            fade_in = QPropertyAnimation(next_window, b"windowOpacity")
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setDuration(duration)
            fade_in.setEasingCurve(QEasingCurve.InCubic)
            
            animation_group.addAnimation(fade_out)
            animation_group.addAnimation(fade_in)
            
        elif transition_type in [TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT, 
                                TransitionType.SLIDE_UP, TransitionType.SLIDE_DOWN]:
            # Get screen dimensions
            screen_rect = QApplication.desktop().screenGeometry()
            
            # Prepare next window position
            next_window.setWindowOpacity(1.0)
            
            # Current window animation
            current_anim = QPropertyAnimation(current_window, b"geometry")
            current_anim.setStartValue(current_window.geometry())
            
            # Next window animation
            next_anim = QPropertyAnimation(next_window, b"geometry")
            next_anim.setEndValue(current_window.geometry())
            
            # Set start/end values based on direction
            if transition_type == TransitionType.SLIDE_LEFT:
                # Current window slides left (out)
                current_end = QRect(
                    -current_window.width(),
                    current_window.y(),
                    current_window.width(),
                    current_window.height()
                )
                current_anim.setEndValue(current_end)
                
                # Next window slides in from right
                next_start = QRect(
                    screen_rect.width(),
                    current_window.y(),
                    current_window.width(),
                    current_window.height()
                )
                next_anim.setStartValue(next_start)
                
            elif transition_type == TransitionType.SLIDE_RIGHT:
                # Current window slides right (out)
                current_end = QRect(
                    screen_rect.width(),
                    current_window.y(),
                    current_window.width(),
                    current_window.height()
                )
                current_anim.setEndValue(current_end)
                
                # Next window slides in from left
                next_start = QRect(
                    -current_window.width(),
                    current_window.y(),
                    current_window.width(),
                    current_window.height()
                )
                next_anim.setStartValue(next_start)
                
            elif transition_type == TransitionType.SLIDE_UP:
                # Current window slides up (out)
                current_end = QRect(
                    current_window.x(),
                    -current_window.height(),
                    current_window.width(),
                    current_window.height()
                )
                current_anim.setEndValue(current_end)
                
                # Next window slides in from bottom
                next_start = QRect(
                    current_window.x(),
                    screen_rect.height(),
                    current_window.width(),
                    current_window.height()
                )
                next_anim.setStartValue(next_start)
                
            elif transition_type == TransitionType.SLIDE_DOWN:
                # Current window slides down (out)
                current_end = QRect(
                    current_window.x(),
                    screen_rect.height(),
                    current_window.width(),
                    current_window.height()
                )
                current_anim.setEndValue(current_end)
                
                # Next window slides in from top
                next_start = QRect(
                    current_window.x(),
                    -current_window.height(),
                    current_window.width(),
                    current_window.height()
                )
                next_anim.setStartValue(next_start)
            
            # Set duration and easing curve
            current_anim.setDuration(duration)
            current_anim.setEasingCurve(QEasingCurve.OutCubic)
            next_anim.setDuration(duration)
            next_anim.setEasingCurve(QEasingCurve.OutCubic)
            
            animation_group.addAnimation(current_anim)
            animation_group.addAnimation(next_anim)
            
        elif transition_type in [TransitionType.ZOOM_IN, TransitionType.ZOOM_OUT]:
            # Prepare next window
            next_window.setWindowOpacity(1.0)
            
            if transition_type == TransitionType.ZOOM_IN:
                # Current window fades out
                fade_out = QPropertyAnimation(current_window, b"windowOpacity")
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setDuration(duration)
                
                # Next window zooms in
                zoom_in = QPropertyAnimation(next_window, b"geometry")
                center_x = current_window.x() + current_window.width() / 2
                center_y = current_window.y() + current_window.height() / 2
                
                # Start with a small centered rectangle
                start_width = current_window.width() * 0.3
                start_height = current_window.height() * 0.3
                start_x = center_x - start_width / 2
                start_y = center_y - start_height / 2
                
                zoom_in.setStartValue(QRect(int(start_x), int(start_y), int(start_width), int(start_height)))
                zoom_in.setEndValue(current_window.geometry())
                zoom_in.setDuration(duration)
                zoom_in.setEasingCurve(QEasingCurve.OutCubic)
                
                animation_group.addAnimation(fade_out)
                animation_group.addAnimation(zoom_in)
                
            else:  # ZOOM_OUT
                # Current window zooms out
                zoom_out = QPropertyAnimation(current_window, b"geometry")
                center_x = current_window.x() + current_window.width() / 2
                center_y = current_window.y() + current_window.height() / 2
                
                # End with a small centered rectangle
                end_width = current_window.width() * 0.3
                end_height = current_window.height() * 0.3
                end_x = center_x - end_width / 2
                end_y = center_y - end_height / 2
                
                zoom_out.setStartValue(current_window.geometry())
                zoom_out.setEndValue(QRect(int(end_x), int(end_y), int(end_width), int(end_height)))
                zoom_out.setDuration(duration)
                zoom_out.setEasingCurve(QEasingCurve.InCubic)
                
                # Next window fades in
                fade_in = QPropertyAnimation(next_window, b"windowOpacity")
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setDuration(duration)
                
                animation_group.addAnimation(zoom_out)
                animation_group.addAnimation(fade_in)
        
        # Connect finished signal to hide the current window
        animation_group.finished.connect(lambda: WindowTransition._finish_transition(current_window, next_window))
        
        # Start the animation
        animation_group.start()
        
        return animation_group
    
    @staticmethod
    def _finish_transition(current_window, next_window):
        """
        Finish the transition by hiding the current window and ensuring the next window is fully visible.
        
        Args:
            current_window (QWidget): The window to hide
            next_window (QWidget): The window to ensure is visible
        """
        # Hide the current window
        current_window.hide()
        
        # Reset opacity and ensure next window is visible
        current_window.setWindowOpacity(1.0)
        next_window.setWindowOpacity(1.0)
        next_window.raise_()
        
        # If next window should be fullscreen, ensure it is
        if hasattr(next_window, 'fullscreen') and next_window.fullscreen:
            next_window.showFullScreen()
