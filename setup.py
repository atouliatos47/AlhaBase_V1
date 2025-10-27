# setup.py - AlphaBase Setup Wizard
import json
from pathlib import Path

def setup_wizard():
    print("=" * 60)
    print("🚀 AlphaBase Configuration Wizard")
    print("=" * 60)
    print()
    
    config = {}
    
    # Server Configuration
    print("📡 SERVER CONFIGURATION")
    print("-" * 60)
    host = input("Enter server host (default: 0.0.0.0): ").strip() or "0.0.0.0"
    port = input("Enter server port (default: 8000): ").strip() or "8000"
    
    config["server"] = {
        "host": host,
        "port": int(port)
    }
    
    # Database Configuration
    print("\n💾 DATABASE CONFIGURATION")
    print("-" * 60)
    db_path = input("Enter database path (default: sqlite:///./alphabase.db): ").strip() or "sqlite:///./alphabase.db"
    
    config["database"] = {
        "url": db_path
    }
    
    # Security Configuration
    print("\n🔒 SECURITY CONFIGURATION")
    print("-" * 60)
    import secrets
    secret_key = secrets.token_urlsafe(32)
    print(f"Generated secret key: {secret_key}")
    
    config["security"] = {
        "secret_key": secret_key,
        "algorithm": "HS256",
        "access_token_expire_minutes": 30
    }
    
    # MQTT Configuration
    print("\n📡 MQTT CONFIGURATION")
    print("-" * 60)
    mqtt_enabled = input("Enable MQTT? (y/n, default: n): ").strip().lower() == 'y'
    
    if mqtt_enabled:
        mqtt_host = input("Enter MQTT broker host (default: localhost): ").strip() or "localhost"
        mqtt_port = input("Enter MQTT broker port (default: 1883): ").strip() or "1883"
        
        config["mqtt"] = {
            "enabled": True,
            "broker_host": mqtt_host,
            "broker_port": int(mqtt_port),
            "topics": [
                "alphabase/sensors/#",
                "alphabase/status/#",
                "alphabase/commands/#"
            ]
        }
    else:
        config["mqtt"] = {
            "enabled": False,
            "broker_host": "localhost",
            "broker_port": 1883,
            "topics": [
                "alphabase/sensors/#",
                "alphabase/status/#",
                "alphabase/commands/#"
            ]
        }
    
    # Storage Configuration
    print("\n📁 STORAGE CONFIGURATION")
    print("-" * 60)
    storage_dir = input("Enter storage directory (default: alphabase_storage): ").strip() or "alphabase_storage"
    
    config["storage"] = {
        "directory": storage_dir
    }
    
    # Save configuration to AppData
    import os
    appdata = Path(os.getenv('APPDATA')) / 'AlphaBase'
    appdata.mkdir(exist_ok=True)
    config_file = appdata / "alphabase_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    
    print("\n" + "=" * 60)
    print("✅ Configuration saved to alphabase_config.json")
    print("=" * 60)
    
    # Create frontend config
    print("\n📝 Creating frontend configuration...")
    
    frontend_config = f"""// config.js - Frontend Configuration (AUTO-GENERATED)
const CONFIG = {{
    // API Base URL
    API_BASE_URL: 'http://{host if host != '0.0.0.0' else 'localhost'}:{port}',
    
    // WebSocket URL
    WS_BASE_URL: 'ws://{host if host != '0.0.0.0' else 'localhost'}:{port}',
    
    // Reconnection settings
    WS_RECONNECT_ATTEMPTS: 5,
    WS_RECONNECT_DELAY: 3000,
    
    // Auto-refresh intervals (milliseconds)
    DASHBOARD_REFRESH_INTERVAL: 30000,
    
    // UI Settings
    ALERTS_DEFAULT_DURATION: 5000
}};

// Make config available globally
window.AlphaBaseConfig = CONFIG;
"""
    

    
    # Create frontend config
    print("\n📝 Frontend configuration needs manual update...")
    print(f"Edit: C:\\Program Files (x86)\\AlphaBase\\console\\js\\config.js")
    print(f"Set API_BASE_URL to: 'http://{host if host != '0.0.0.0' else 'localhost'}:{port}'")

if __name__ == "__main__":
    setup_wizard()