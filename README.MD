# AlphaBase v4.0

Universal backend-as-a-service for web applications with real-time updates, authentication, and IoT support.

## Features

- 🔐 User Authentication (Register/Login)
- 💾 Persistent Data Storage (SQLite/PostgreSQL)
- 🔄 Real-time Updates (WebSocket)
- 📡 MQTT Integration (IoT devices)
- 🔒 Security Rules System
- 📁 File Storage
- 🔍 Advanced Query System
- 📊 Data Analytics

## Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Setup Wizard
```bash
python setup.py
```

This will guide you through:
- Server configuration (host and port)
- Database setup
- Security settings
- MQTT configuration (optional)
- Storage location

### 3. Start AlphaBase
```bash
python main.py
```

The server will start on the configured host and port (default: http://localhost:8000)

### 4. Access Web Console

Open your browser and navigate to:
```
http://localhost:8000/index.html
```

Or use the configured server address from setup.

## Configuration

### Backend Configuration

Edit `alphabase_config.json` to customize:
```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8000
    },
    "database": {
        "url": "sqlite:///./alphabase.db"
    },
    "mqtt": {
        "enabled": false,
        "broker_host": "localhost",
        "broker_port": 1883
    }
}
```

### Frontend Configuration

Edit `js/config.js` to set your server URL:
```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    WS_BASE_URL: 'ws://localhost:8000'
};
```

## Usage

### 1. Register a User

First time users need to register:
- Username
- Email
- Password

### 2. Create Data

Use the Data Manager to create collections and documents:
```javascript
// Example: Create a sensor reading
Collection: sensors
Key: sensor_001
Data: {"temperature": 25, "humidity": 60}
```

### 3. Real-time Updates

All data changes are broadcast in real-time to connected clients via WebSocket.

### 4. MQTT Integration (Optional)

If MQTT is enabled, IoT devices can publish data:
```python
# ESP32 example
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("your-server-ip", 1883)
client.publish("alphabase/sensors/temp", '{"temperature": 25}')
```

## Using AlphaBase Client Library

Include the client library in your HTML:
```html
<script src="alphabase.js"></script>
```

Then use it in your JavaScript:
```javascript
const ab = new AlphaBase('http://your-server:8000');

// Login
await ab.login('username', 'password');

// Store data
await ab.set('products', 'item1', {
    name: 'Widget',
    price: 29.99
});

// Get data
const result = await ab.get('products', 'item1');

// Real-time updates
ab.connectRealtime((message) => {
    console.log('Data updated:', message);
});
```

## Network Access

### Local Network Only (Default)
- Access from same computer: `http://localhost:8000`
- Access from other devices on same WiFi: `http://YOUR-IP:8000`

### Internet Access (Advanced)
To make AlphaBase accessible from the internet:
1. Use port forwarding on your router
2. Use a service like ngrok
3. Deploy to a cloud server (AWS, DigitalOcean, etc.)

## Security Notes

- Change the secret key in production (setup wizard generates one)
- Use HTTPS for production deployments
- Configure security rules in `security_rules.py`
- Keep your `alphabase_config.json` secure

## Troubleshooting

### Can't connect to server
- Check if server is running: `python main.py`
- Verify firewall allows port 8000
- Check server IP address in `js/config.js`

### MQTT not working
- Verify MQTT broker is running: `mosquitto -v`
- Check MQTT settings in `alphabase_config.json`
- Ensure `"enabled": true` in MQTT config

### WebSocket disconnects
- Check network stability
- Verify WebSocket URL in `js/config.js`
- Check browser console for errors

## License

Open source - Use for personal or commercial projects

## Support

For issues and questions, check the configuration files and error logs.