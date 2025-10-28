// app.js - Main Application Controller

const app = {
    currentView: 'dashboard',

    // Initialize application
    init() {
        console.log('🚀 Initializing AlphaBase Console v4.0...');

        // Setup login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Setup register form
        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });

        console.log('✅ Application initialized');
    },

    // Handle login
    async handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const result = await api.login(username, password);

            if (result.success) {
                // Hide login, show console
                document.getElementById('loginScreen').style.display = 'none';
                document.getElementById('console').style.display = 'block';
                document.getElementById('currentUser').textContent = username;

                // Connect to WebSocket for real-time updates
                wsManager.connect();

                // Load initial dashboard
                await dashboard.loadDashboard();

                // Show welcome message
                wsManager.showAlert(
                    'Welcome!',
                    `Signed in as ${username}`,
                    'success',
                    3000
                );

            } else {
                this.showLoginStatus('Sign in failed. Please check your credentials.', 'error');
            }
        } catch (error) {
            this.showLoginStatus('Sign in failed. ' + error.message, 'error');
        }
    },

    // Handle registration
    async handleRegister() {
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;

        try {
            const response = await fetch(`${api.baseURL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            const data = await response.json();

            // Store token
            api.authToken = data.access_token;
            api.currentUsername = username;

            // Hide login, show console
            document.getElementById('loginScreen').style.display = 'none';
            document.getElementById('console').style.display = 'block';
            document.getElementById('currentUser').textContent = username;

            // Connect to WebSocket
            wsManager.connect();

            // Load initial dashboard
            await dashboard.loadDashboard();

            // Show welcome message
            wsManager.showAlert(
                'Account Created!',
                `Welcome to AlphaBase, ${username}!`,
                'success',
                3000
            );

        } catch (error) {
            this.showLoginStatus('Registration failed. ' + error.message, 'error');
        }
    },

    // Logout
    logout() {
        // Disconnect WebSocket
        wsManager.disconnect();

        // Reset API
        api.authToken = null;
        api.currentUsername = null;

        // Show login screen
        document.getElementById('loginScreen').style.display = 'flex';
        document.getElementById('console').style.display = 'none';
        document.getElementById('loginForm').reset();
        document.getElementById('registerForm').reset();

        // Show login form (hide register)
        showLoginForm();

        console.log('👋 Logged out');
    },

    // Switch between views
    switchView(viewName) {
        console.log(`📄 Switching to view: ${viewName}`);

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
        event.target.classList.add('active');

        // Update views
        document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));

        // Restore console-content padding (for when leaving Settings)
        document.querySelector('.console-content').style.paddingTop = '24px';

        // Store current view
        this.currentView = viewName;

        // Show selected view and load its data
        if (viewName === 'dashboard') {
            document.getElementById('dashboardView').classList.add('active');
            dashboard.loadDashboard();
        } else if (viewName === 'analytics') {
            document.getElementById('analyticsView').classList.add('active');
            charts.loadAnalytics();
        } else if (viewName === 'data') {
            document.getElementById('dataView').classList.add('active');
        } else if (viewName === 'collections') {
            document.getElementById('collectionsView').classList.add('active');
            dashboard.loadCollectionsView();
        } else if (viewName === 'settings') {
            document.getElementById('settingsView').classList.add('active');
            // Remove padding for Settings view only
            document.querySelector('.console-content').style.paddingTop = '0';
            settings.loadSettings();
        }

    },

    // Show login status message
    showLoginStatus(message, type) {
        const statusDiv = document.getElementById('loginStatus');
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.style.display = 'block';
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
};

// Form switching functions (global scope for onclick)
function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('loginStatus').style.display = 'none';
}

function showLoginForm() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('loginStatus').style.display = 'none';
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});