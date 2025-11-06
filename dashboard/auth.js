// Authentication System for Certificate Management Dashboard
// Simple hardcoded user authentication

// User database (hardcoded - 3 users with full access)
const USERS = {
    'admin': {
        password: 'admin123',
        name: 'Administrator'
    },
    'manager': {
        password: 'manager123',
        name: 'Manager User'
    },
    'editor': {
        password: 'editor123',
        name: 'Editor User'
    }
};

// Session management
const SESSION_KEY = 'cert_dashboard_session';
const SESSION_TIMEOUT = 8 * 60 * 60 * 1000; // 8 hours in milliseconds

// Login form handling
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Check if already logged in
    if (isLoggedIn()) {
        window.location.href = 'index.html';
    }
});

function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    
    // Hide previous error
    errorMessage.classList.remove('show');
    
    // Validate credentials
    if (authenticateUser(username, password)) {
        const user = USERS[username];
        
        // Create session
        const session = {
            username: username,
            name: user.name,
            loginTime: new Date().toISOString(),
            expiresAt: new Date(Date.now() + SESSION_TIMEOUT).toISOString()
        };
        
        // Save session to sessionStorage
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
        
        // Also save to localStorage for persistence across tabs
        localStorage.setItem(SESSION_KEY, JSON.stringify(session));
        
        // Redirect to dashboard
        window.location.href = 'index.html';
    } else {
        // Show error message
        errorMessage.classList.add('show');
        
        // Clear password field
        document.getElementById('password').value = '';
        document.getElementById('password').focus();
    }
}

function authenticateUser(username, password) {
    const user = USERS[username];
    
    if (!user) {
        return false;
    }
    
    return user.password === password;
}

function isLoggedIn() {
    const session = getSession();
    
    if (!session) {
        return false;
    }
    
    // Check if session is expired
    const now = new Date();
    const expiresAt = new Date(session.expiresAt);
    
    if (now > expiresAt) {
        clearSession();
        return false;
    }
    
    return true;
}

function getSession() {
    // Try sessionStorage first
    let sessionData = sessionStorage.getItem(SESSION_KEY);
    
    // Fallback to localStorage
    if (!sessionData) {
        sessionData = localStorage.getItem(SESSION_KEY);
        if (sessionData) {
            // Restore to sessionStorage
            sessionStorage.setItem(SESSION_KEY, sessionData);
        }
    }
    
    if (!sessionData) {
        return null;
    }
    
    try {
        return JSON.parse(sessionData);
    } catch (e) {
        console.error('Error parsing session data:', e);
        clearSession();
        return null;
    }
}

function clearSession() {
    sessionStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(SESSION_KEY);
}

function logout() {
    clearSession();
    window.location.href = 'login.html';
}

function getCurrentUser() {
    return getSession();
}

// Export functions for use in other scripts
if (typeof window !== 'undefined') {
    window.auth = {
        isLoggedIn,
        logout,
        getCurrentUser,
        getSession
    };
}
