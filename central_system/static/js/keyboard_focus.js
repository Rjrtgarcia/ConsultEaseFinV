/**
 * keyboard_focus.js
 * 
 * This script handles keyboard focus events for the ConsultEase system.
 * It ensures that the on-screen keyboard (squeekboard) appears when input fields are focused.
 * 
 * Usage:
 * 1. Include this script in your HTML file
 * 2. Call initKeyboardFocus() to initialize keyboard focus handling
 */

// Global state
let keyboardVisible = false;
let keyboardType = 'squeekboard'; // Default to squeekboard
let lastFocusedElement = null;

/**
 * Initialize keyboard focus handling
 * This function should be called when the page loads
 */
function initKeyboardFocus() {
    console.log('Initializing keyboard focus handling');
    
    // Detect keyboard type from environment
    detectKeyboardType();
    
    // Add focus event listeners to all input fields
    addFocusListeners();
    
    // Add click event listener to document to handle focus on click
    document.addEventListener('click', handleDocumentClick);
    
    // Add touch event listener to document to handle focus on touch
    document.addEventListener('touchstart', handleDocumentTouch);
    
    console.log(`Keyboard focus handling initialized with keyboard type: ${keyboardType}`);
}

/**
 * Detect the keyboard type from the environment
 */
function detectKeyboardType() {
    // Check if we're in a Qt WebEngine environment
    if (typeof window.qt !== 'undefined') {
        console.log('Qt WebEngine environment detected');
        
        // Try to get keyboard type from Qt
        try {
            if (window.qt.webChannelTransport) {
                // Use squeekboard by default in Qt environment
                keyboardType = 'squeekboard';
                console.log('Using squeekboard in Qt environment');
            }
        } catch (e) {
            console.error('Error detecting keyboard type:', e);
        }
    } else {
        // Check if we're in a mobile environment
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        if (isMobile) {
            // Use native keyboard on mobile devices
            keyboardType = 'native';
            console.log('Using native keyboard on mobile device');
        } else {
            // Default to squeekboard on desktop
            keyboardType = 'squeekboard';
            console.log('Using squeekboard on desktop');
        }
    }
}

/**
 * Add focus event listeners to all input fields
 */
function addFocusListeners() {
    // Get all input fields
    const inputFields = document.querySelectorAll('input, textarea, [contenteditable="true"]');
    
    // Add focus and blur event listeners to each input field
    inputFields.forEach(field => {
        // Add data attribute to mark as keyboard-enabled
        field.setAttribute('data-keyboard-focus', 'true');
        
        // Add focus event listener
        field.addEventListener('focus', handleInputFocus);
        
        // Add blur event listener
        field.addEventListener('blur', handleInputBlur);
        
        console.log(`Added keyboard focus handlers to ${field.tagName.toLowerCase()} element`);
    });
}

/**
 * Handle input field focus event
 * @param {Event} event - The focus event
 */
function handleInputFocus(event) {
    const target = event.target;
    console.log(`Input field focused: ${target.tagName.toLowerCase()}`);
    
    // Store last focused element
    lastFocusedElement = target;
    
    // Show keyboard
    showKeyboard();
}

/**
 * Handle input field blur event
 * @param {Event} event - The blur event
 */
function handleInputBlur(event) {
    console.log(`Input field blurred: ${event.target.tagName.toLowerCase()}`);
    
    // Clear last focused element
    lastFocusedElement = null;
    
    // Don't hide keyboard on blur, let it be handled manually
    // This prevents the keyboard from disappearing when switching between fields
}

/**
 * Handle document click event
 * @param {Event} event - The click event
 */
function handleDocumentClick(event) {
    const target = event.target;
    
    // Check if the clicked element is an input field or has a keyboard-focus attribute
    const isInputField = target.tagName === 'INPUT' || 
                         target.tagName === 'TEXTAREA' || 
                         target.getAttribute('contenteditable') === 'true' ||
                         target.getAttribute('data-keyboard-focus') === 'true';
    
    if (isInputField) {
        // Show keyboard for input fields
        showKeyboard();
    } else {
        // Hide keyboard for non-input fields
        hideKeyboard();
    }
}

/**
 * Handle document touch event
 * @param {Event} event - The touch event
 */
function handleDocumentTouch(event) {
    // Use the same logic as click events
    handleDocumentClick(event);
}

/**
 * Show the on-screen keyboard
 */
function showKeyboard() {
    if (keyboardVisible) {
        // Keyboard is already visible
        return;
    }
    
    console.log(`Showing ${keyboardType} keyboard`);
    
    if (keyboardType === 'squeekboard') {
        // Show squeekboard using Qt WebChannel if available
        if (typeof window.qt !== 'undefined' && window.qt.webChannelTransport) {
            try {
                // Try to call the showKeyboard method on the Qt object
                window.qt.showKeyboard();
                console.log('Called qt.showKeyboard()');
            } catch (e) {
                console.error('Error calling qt.showKeyboard():', e);
            }
        }
        
        // Also try to send a message to the parent window
        try {
            window.parent.postMessage({ action: 'showKeyboard', type: 'squeekboard' }, '*');
            console.log('Sent showKeyboard message to parent window');
        } catch (e) {
            console.error('Error sending message to parent window:', e);
        }
    }
    
    // Mark keyboard as visible
    keyboardVisible = true;
}

/**
 * Hide the on-screen keyboard
 */
function hideKeyboard() {
    if (!keyboardVisible) {
        // Keyboard is already hidden
        return;
    }
    
    console.log(`Hiding ${keyboardType} keyboard`);
    
    if (keyboardType === 'squeekboard') {
        // Hide squeekboard using Qt WebChannel if available
        if (typeof window.qt !== 'undefined' && window.qt.webChannelTransport) {
            try {
                // Try to call the hideKeyboard method on the Qt object
                window.qt.hideKeyboard();
                console.log('Called qt.hideKeyboard()');
            } catch (e) {
                console.error('Error calling qt.hideKeyboard():', e);
            }
        }
        
        // Also try to send a message to the parent window
        try {
            window.parent.postMessage({ action: 'hideKeyboard', type: 'squeekboard' }, '*');
            console.log('Sent hideKeyboard message to parent window');
        } catch (e) {
            console.error('Error sending message to parent window:', e);
        }
    }
    
    // Mark keyboard as hidden
    keyboardVisible = false;
}

// Initialize keyboard focus handling when the page loads
document.addEventListener('DOMContentLoaded', initKeyboardFocus);
