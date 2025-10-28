# email_manager.py - Email Notification System
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional

class EmailManager:
    def __init__(self):
        from config import config
        self.smtp_server = config.get("email", "smtp_server")
        self.smtp_port = config.get("email", "smtp_port")
        self.sender_email = config.get("email", "sender_email")
        self.sender_password = config.get("email", "sender_password")
        self.enabled = config.get("email", "enabled")
    
    def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> bool:
        """Send an email notification"""
        
        if not self.enabled:
            print("⏭️  Email notifications disabled in config")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email
            
            # Add body
            if html:
                part = MIMEText(body, "html")
            else:
                part = MIMEText(body, "plain")
            
            message.attach(part)
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False
    
    def send_alert(self, to_email: str, alert_title: str, alert_message: str, data: dict = None) -> bool:
        """Send a formatted alert email"""
        
        subject = f"🚨 AlphaBase Alert: {alert_title}"
        
        # Create formatted body
        body = f"""
AlphaBase Alert Notification
========================================

Alert: {alert_title}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message:
{alert_message}
"""
        
        if data:
            body += "\n\nData:\n"
            for key, value in data.items():
                body += f"  {key}: {value}\n"
        
        body += "\n========================================\nSent by AlphaBase v4.0"
        
        return self.send_email(to_email, subject, body)
    
    def send_multiple(self, to_emails: List[str], subject: str, body: str) -> dict:
        """Send email to multiple recipients"""
        results = {}
        for email in to_emails:
            results[email] = self.send_email(email, subject, body)
        return results

# Create global instance
email_manager = EmailManager()