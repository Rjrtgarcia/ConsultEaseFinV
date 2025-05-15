/**
 * keyboard_integration.js
 * 
 * This script provides integration between the Qt application and the web-based keyboard handling.
 * It allows the Qt application to control the keyboard and receive events from the web view.
 * 
 * Usage:
 * 1. Include this script in your HTML file
 * 2. The Qt application can call the global functions defined here
 */

// Global state
let keyboardIntegration = {
    initialized: false,
    keyboardVisible: false,
    keyboardType: 'squeekboard', // Default to squeekboard
    focusedElement: null,
    qtBridge: null
};

/**
 * Initialize the keyboard integration
 * This function is called by the Qt application
 * @param {Object} bridge - The Qt WebChannel bridge object
 */
function initKeyboardIntegration(bridge) {
    if (keyboardIntegration.initialized) {
        console.log('Keyboard integration already initialized');
        return;
    }
    
    console.log('Initializing keyboard integration');
    
    // Store the Qt bridge
    keyboardIntegration.qtBridge = bridge;
    
    // Set up message listener for communication with the Qt application
    window.addEventListener('message', handleQtMessage);
    
    // Add event listeners to input fields
    setupInputFieldListeners();
    
    // Mark as initialized
    keyboardIntegration.initialized = true;
    
    console.log('Keyboard integration initialized');
}

/**
 * Set up event listeners for input fields
 */
function setupInputFieldListeners() {
    // Function to add listeners to all input fields
    function addListeners() {
        const inputFields = document.querySelectorAll('input, textarea, [contenteditable="true"]');
        
        inputFields.forEach(field => {
            // Skip if already processed
            if (field.hasAttribute('data-keyboard-integrated')) {
                return;
            }
            
            // Mark as processed
            field.setAttribute('data-keyboard-integrated', 'true');
            
            // Add focus event listener
            field.addEventListener('focus', handleInputFocus);
            
            // Add blur event listener
            field.addEventListener('blur', handleInputBlur);
            
            console.log(`Added keyboard integration to ${field.tagName.toLowerCase()} element`);
        });
    }
    
    // Add listeners now
    addListeners();
    
    // Also set up a MutationObserver to handle dynamically added input fields
    const observer = new MutationObserver(mutations => {
        let shouldAddListeners = false;
        
        mutations.forEach(mutation => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                shouldAddListeners = true;
            }
        });
        
        if (shouldAddListeners) {
            addListeners();
        }
    });
    
    // Start observing the document
    observer.observe(document.body, { 
        childList: true, 
        subtree: true 
    });
}

/**
 * Handle input field focus event
 * @param {Event} event - The focus event
 */
function handleInputFocus(event) {
    const target = event.target;
    console.log(`Input field focused: ${target.tagName.toLowerCase()}`);
    
    // Store focused element
    keyboardIntegration.focusedElement = target;
    
    // Notify Qt application
    notifyQtInputFocused(target);
    
    // Show keyboard
    showKeyboard();
}

/**
 * Handle input field blur event
 * @param {Event} event - The blur event
 */
function handleInputBlur(event) {
    console.log(`Input field blurred: ${event.target.tagName.toLowerCase()}`);
    
    // Clear focused element
    keyboardIntegration.focusedElement = null;
    
    // Notify Qt application
    notifyQtInputBlurred(event.target);
    
    // Don't hide keyboard on blur, let it be handled manually
}

/**
 * Notify Qt application that an input field was focused
 * @param {Element} element - The focused input element
 */
function notifyQtInputFocused(element) {
    if (!keyboardIntegration.qtBridge) {
        return;
    }
    
    try {
        // Get element information
        const elementInfo = {
            tagName: element.tagName.toLowerCase(),
            type: element.type || 'text',
            id: element.id || '',
            name: element.name || '',
            className: element.className || ''
        };
        
        // Call the Qt method
        if (keyboardIntegration.qtBridge.inputFocused) {
            keyboardIntegration.qtBridge.inputFocused(JSON.stringify(elementInfo));
        }
    } catch (e) {
        console.error('Error notifying Qt of input focus:', e);
    }
}

/**
 * Notify Qt application that an input field was blurred
 * @param {Element} element - The blurred input element
 */
function notifyQtInputBlurred(element) {
    if (!keyboardIntegration.qtBridge) {
        return;
    }
    
    try {
        // Get element information
        const elementInfo = {
            tagName: element.tagName.toLowerCase(),
            type: element.type || 'text',
            id: element.id || '',
            name: element.name || '',
            className: element.className || ''
        };
        
        // Call the Qt method
        if (keyboardIntegration.qtBridge.inputBlurred) {
            keyboardIntegration.qtBridge.inputBlurred(JSON.stringify(elementInfo));
        }
    } catch (e) {
        console.error('Error notifying Qt of input blur:', e);
    }
}

/**
 * Handle messages from the Qt application
 * @param {MessageEvent} event - The message event
 */
function handleQtMessage(event) {
    const data = event.data;
    
    if (!data || typeof data !== 'object') {
        return;
    }
    
    console.log('Received message from Qt:', data);
    
    switch (data.action) {
        case 'showKeyboard':
            showKeyboard();
            break;
        case 'hideKeyboard':
            hideKeyboard();
            break;
        case 'setKeyboardType':
            setKeyboardType(data.type);
            break;
        case 'focusInput':
            focusInput(data.selector);
            break;
    }
}

/**
 * Show the on-screen keyboard
 * This function can be called directly by the Qt application
 */
function showKeyboard() {
    if (keyboardIntegration.keyboardVisible) {
        // Keyboard is already visible
        return;
    }
    
    console.log(`Showing ${keyboardIntegration.keyboardType} keyboard`);
    
    // Notify Qt application
    if (keyboardIntegration.qtBridge && keyboardIntegration.qtBridge.showKeyboard) {
        keyboardIntegration.qtBridge.showKeyboard();
    }
    
    // Mark keyboard as visible
    keyboardIntegration.keyboardVisible = true;
}

/**
 * Hide the on-screen keyboard
 * This function can be called directly by the Qt application
 */
function hideKeyboard() {
    if (!keyboardIntegration.keyboardVisible) {
        // Keyboard is already hidden
        return;
    }
    
    console.log(`Hiding ${keyboardIntegration.keyboardType} keyboard`);
    
    // Notify Qt application
    if (keyboardIntegration.qtBridge && keyboardIntegration.qtBridge.hideKeyboard) {
        keyboardIntegration.qtBridge.hideKeyboard();
    }
    
    // Mark keyboard as hidden
    keyboardIntegration.keyboardVisible = false;
}

/**
 * Set the keyboard type
 * @param {string} type - The keyboard type ('squeekboard' or 'onboard')
 */
function setKeyboardType(type) {
    if (type !== 'squeekboard' && type !== 'onboard') {
        console.error(`Invalid keyboard type: ${type}`);
        return;
    }
    
    console.log(`Setting keyboard type to ${type}`);
    keyboardIntegration.keyboardType = type;
}

/**
 * Focus an input element
 * @param {string} selector - CSS selector for the input element
 */
function focusInput(selector) {
    try {
        const element = document.querySelector(selector);
        if (element) {
            element.focus();
        } else {
            console.error(`Element not found: ${selector}`);
        }
    } catch (e) {
        console.error('Error focusing input:', e);
    }
}

// Export global functions for Qt to call
window.initKeyboardIntegration = initKeyboardIntegration;
window.showKeyboard = showKeyboard;
window.hideKeyboard = hideKeyboard;
window.setKeyboardType = setKeyboardType;
window.focusInput = focusInput;
