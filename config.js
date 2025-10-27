// config.js - Frontend Configuration
const CONFIG = {
    // API Base URL - Change this to your server's address
    API_BASE_URL: 'http://localhost:8000',
    
    // WebSocket URL - Change this to match your server
    WS_BASE_URL: 'ws://localhost:8000',
    
    // Reconnection settings
    WS_RECONNECT_ATTEMPTS: 5,
    WS_RECONNECT_DELAY: 3000,
    
    // Auto-refresh intervals (milliseconds)
    DASHBOARD_REFRESH_INTERVAL: 30000,  // 30 seconds
    
    // UI Settings
    ALERTS_DEFAULT_DURATION: 5000  // 5 seconds
};

// Make config available globally
window.AlphaBaseConfig = CONFIG;