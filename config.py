# config.py - AlphaBase Configuration Management
import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        # Store config in user's AppData folder
        import os
        appdata_path = Path(os.getenv('APPDATA')) / 'AlphaBase'
        appdata_path.mkdir(exist_ok=True)
        self.config_file = appdata_path / "alphabase_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default configuration WITH TELEGRAM
            default_config = {
                "server": {
                    "host": "0.0.0.0",
                    "port": 8000 
                },
                "database": {
                    "url": "sqlite:///./alphabase.db"
                },
                "security": {
                    "secret_key": "alphabase-secret-key-change-in-production",
                    "algorithm": "HS256",
                    "access_token_expire_minutes": 30
                },
                "mqtt": {
                    "enabled": True,  # Changed to True since you're using MQTT
                    "broker_host": "localhost",
                    "broker_port": 1883,
                    "topics": [
                        "alphabase/sensors/#",
                        "alphabase/status/#",
                        "alphabase/commands/#"
                    ]
                },
                "telegram": {  # ADD THIS SECTION
                    "enabled": True,
                    "bot_token": "8223163172:AAGPtPNPdZ94f7KiwYw7QJzoW52uWAtCm5w",
                    "chat_id": "8314923318"
                },
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "atouliatos43@gmail.com",
                    "sender_password": "nsnrqeobhwquvvkf"
                },
                "storage": {
                    "directory": "alphabase_storage"
                }
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config_data=None):
        """Save configuration to file"""
        if config_data:
            self.config = config_data
        
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get(self, *keys):
        """Get nested configuration value"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            if value is None:
                return None
        return value

# Create global config instance
config = Config()