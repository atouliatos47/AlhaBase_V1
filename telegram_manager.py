"""
Telegram Notification Manager for AlphaBase
Handles sending messages via Telegram Bot API
"""

import requests
import json
from typing import Optional, Dict, Any
from config import config


class TelegramManager:
    def __init__(self):
        """Initialize Telegram Manager with configuration"""
        telegram_config = config.get("telegram") if config.config else {}
        if telegram_config is None:
            telegram_config = {}

        self.enabled = telegram_config.get("enabled", False)
        self.bot_token = telegram_config.get("bot_token", "")
        self.chat_id = telegram_config.get("chat_id", "")

        if self.enabled and self.bot_token and self.chat_id:
            print("✅ Telegram Manager initialized")
            print(f"   Bot Token: {self.bot_token[:20]}...")
            print(f"   Chat ID: {self.chat_id}")
        else:
            print("⚠️  Telegram not configured")

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a simple text message via Telegram

        Args:
            message: Text message to send
            parse_mode: Message formatting (HTML, Markdown, or None)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("⚠️  Telegram is disabled")
            return False

        if not self.bot_token or not self.chat_id:
            print("❌ Telegram not configured properly")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                print(f"✅ Telegram message sent successfully")
                return True
            else:
                print(f"❌ Telegram failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Telegram error: {str(e)}")
            return False

    def send_alert(
        self, title: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a formatted alert message via Telegram

        Args:
            title: Alert title
            message: Alert message
            data: Optional dictionary with additional data

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        # Format the message with HTML
        formatted_message = f"<b>🚨 {title}</b>\n\n"
        formatted_message += f"{message}\n"

        # Add data if provided
        if data:
            formatted_message += "\n<b>Details:</b>\n"
            for key, value in data.items():
                formatted_message += f"• {key}: {value}\n"

        return self.send_message(formatted_message, parse_mode="HTML")

    def send_press_stop_alert(
        self, press_number: int, reason: str, runtime_seconds: int
    ) -> bool:
        """
        Send a press stop alert with reason and runtime

        Args:
            press_number: Press number (1, 2, 3)
            reason: Stop reason (Maintenance, Quality Issue, etc.)
            runtime_seconds: How long the press was running in seconds

        Returns:
            bool: True if sent successfully, False otherwise
        """
        minutes = runtime_seconds // 60
        seconds = runtime_seconds % 60

        title = f"Press {press_number} Stopped - {reason}"
        message = f"Press {press_number} has been stopped by operator."

        data = {
            "Reason": reason,
            "Runtime": f"{minutes} min {seconds} sec",
            "Press": f"Press {press_number}",
        }

        return self.send_alert(title, message, data)

    def test_connection(self) -> bool:
        """
        Test Telegram connection by sending a test message

        Returns:
            bool: True if test successful, False otherwise
        """
        if not self.enabled:
            print("❌ Telegram is disabled")
            return False

        return self.send_message("✅ AlphaBase Telegram test message")


# Global instance
telegram_manager = TelegramManager()
