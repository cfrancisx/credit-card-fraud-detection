// Main JavaScript for Fraud Detection System
console.log('FraudGuard AI System Loaded');

// Safe URL navigation
function navigateTo(url) {
    try {
        window.location.href = url;
    } catch (error) {
        console.error('Navigation error:', error);
        alert('Navigation error. Please refresh the page.');
    }
}

// Safe form submission
function safeSubmit(formId, callback) {
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            try {
                callback();
            } catch (error) {
                console.error('Form submission error:', error);
                alert('Error submitting form. Please try again.');
            }
        });
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded successfully');
    
    // Add any global initialization here
    initializeGlobalFeatures();
});

function initializeGlobalFeatures() {
    // Global features initialization
    console.log('Initializing global features...');
}