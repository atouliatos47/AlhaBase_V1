"""
test_telegram.py - Test your Telegram bot configuration
Run this to verify your Telegram setup is working correctly
"""

import requests
import json

# Load configuration
try:
    with open('alphabase_config.json', 'r') as f:
        config = json.load(f)
        telegram_config = config.get('telegram', {})
except FileNotFoundError:
    print("❌ Configuration file not found!")
    print("Make sure alphabase_config.json exists in the current directory.")
    exit(1)

def test_telegram():
    """Test Telegram configuration"""
    
    # Check if Telegram is enabled
    if not telegram_config.get('enabled', False):
        print("⚠️  Telegram is disabled in configuration")
        print("Set 'enabled': true in alphabase_config.json to enable")
        return False
    
    bot_token = telegram_config.get('bot_token', '')
    chat_id = telegram_config.get('chat_id', '')
    
    if not bot_token:
        print("❌ Bot token is missing!")
        print("\nTo get a bot token:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the token and add it to alphabase_config.json")
        return False
    
    if not chat_id:
        print("❌ Chat ID is missing!")
        print("\nTo get your chat ID:")
        print("1. Open Telegram and search for @userinfobot")
        print("2. Start the bot and it will show your ID")
        print("3. Copy the ID and add it to alphabase_config.json")
        return False
    
    print("📡 Testing Telegram configuration...")
    print(f"Bot Token: {bot_token[:20]}...")
    print(f"Chat ID: {chat_id}")
    
    # Test sending a message
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        message = """✅ *AlphaBase Telegram Test*

Your Telegram integration is working correctly!

*Configuration:*
• Bot Token: Configured ✓
• Chat ID: {chat_id} ✓
• Status: Active ✓

You can now receive notifications from AlphaBase.
        """.format(chat_id=chat_id)
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
            print("Check your Telegram for the test message.")
            return True
        else:
            error_data = response.json()
            print(f"❌ Failed to send message!")
            print(f"Error: {error_data.get('description', 'Unknown error')}")
            
            # Common error solutions
            if "chat not found" in str(error_data).lower():
                print("\n💡 Solution: Make sure you've started a conversation with your bot")
                print("1. Open Telegram and search for your bot")
                print("2. Click 'Start' to begin conversation")
                print("3. Then run this test again")
            elif "unauthorized" in str(error_data).lower():
                print("\n💡 Solution: Your bot token appears to be invalid")
                print("1. Check if the token is correct in alphabase_config.json")
                print("2. If needed, create a new bot with @BotFather")
            
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def send_test_alert():
    """Send a test alert via Telegram"""
    from datetime import datetime
    
    bot_token = telegram_config.get('bot_token', '')
    chat_id = telegram_config.get('chat_id', '')
    
    if not bot_token or not chat_id:
        print("❌ Telegram not configured properly")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        message = f"""🚨 *AlphaBase Alert Test*

*Alert:* System Test
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Source:* AlphaBase v4.0

*Details:*
• Type: Test Alert
• Priority: Low
• Action: No action required

This is a test of the AlphaBase alert system.
        """
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Test alert sent successfully!")
            return True
        else:
            print(f"❌ Failed to send alert: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AlphaBase Telegram Configuration Test")
    print("=" * 60)
    print()
    
    # Run basic test
    if test_telegram():
        print()
        print("Would you like to send a test alert? (y/n): ", end="")
        if input().lower() == 'y':
            send_test_alert()
    
    print()
    print("=" * 60)
    print("Test complete!")