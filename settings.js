// settings.js - Settings Management

const settings = {
    recipients: [],
    
    // Load settings when view is opened
    async loadSettings() {
        try {
            // Load current email config from server
            const response = await fetch(`${api.baseURL}/settings/email`, {
                headers: {
                    'Authorization': `Bearer ${api.authToken}`
                }
            });
            
            if (response.ok) {
                const config = await response.json();
                this.populateEmailSettings(config);
            }
            
            // Load recipients list
            await this.loadRecipients();
            
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    },
    
    // Populate email settings form
    populateEmailSettings(config) {
        document.getElementById('emailEnabled').checked = config.enabled || false;
        document.getElementById('smtpServer').value = config.smtp_server || 'smtp.gmail.com';
        document.getElementById('smtpPort').value = config.smtp_port || 587;
        document.getElementById('senderEmail').value = config.sender_email || '';
        // Don't populate password for security
        
        if (config.enabled) {
            document.getElementById('emailSettings').style.display = 'block';
        }
    },
    
    // Toggle email settings visibility
    toggleEmailSettings() {
        const enabled = document.getElementById('emailEnabled').checked;
        document.getElementById('emailSettings').style.display = enabled ? 'block' : 'none';
    },
    
    // Save email configuration
    async saveEmailConfig() {
        const config = {
            enabled: document.getElementById('emailEnabled').checked,
            smtp_server: document.getElementById('smtpServer').value,
            smtp_port: parseInt(document.getElementById('smtpPort').value),
            sender_email: document.getElementById('senderEmail').value,
            sender_password: document.getElementById('senderPassword').value
        };
        
        try {
            const response = await fetch(`${api.baseURL}/settings/email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${api.authToken}`
                },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                this.showStatus('✅ Email configuration saved successfully!', 'success');
                // Clear password field
                document.getElementById('senderPassword').value = '';
            } else {
                this.showStatus('❌ Failed to save configuration', 'error');
            }
        } catch (error) {
            this.showStatus('❌ Error: ' + error.message, 'error');
        }
    },
    
    // Test email
    async testEmail() {
        const email = document.getElementById('senderEmail').value;
        
        if (!email) {
            this.showStatus('❌ Please enter a sender email first', 'error');
            return;
        }
        
        this.showStatus('📧 Sending test email...', 'info');
        
        try {
            const response = await fetch(`${api.baseURL}/notifications/send-alert`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${api.authToken}`
                },
                body: JSON.stringify({
                    to_email: email,
                    alert_title: 'Test Alert',
                    alert_message: 'This is a test email from AlphaBase Settings',
                    data: {}
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showStatus('✅ Test email sent! Check your inbox.', 'success');
            } else {
                this.showStatus('❌ Failed to send test email', 'error');
            }
        } catch (error) {
            this.showStatus('❌ Error: ' + error.message, 'error');
        }
    },
    
    // Load recipients list
    async loadRecipients() {
        try {
            const response = await fetch(`${api.baseURL}/settings/recipients`, {
                headers: {
                    'Authorization': `Bearer ${api.authToken}`
                }
            });
            
            if (response.ok) {
                this.recipients = await response.json();
                this.renderRecipients();
            }
        } catch (error) {
            console.error('Error loading recipients:', error);
            // If endpoint doesn't exist yet, just show empty list
            this.recipients = [];
            this.renderRecipients();
        }
    },
    
    // Add recipient
    async addRecipient() {
        const email = document.getElementById('recipientEmail').value.trim();
        
        if (!email) {
            this.showStatus('❌ Please enter an email address', 'error');
            return;
        }
        
        if (!this.isValidEmail(email)) {
            this.showStatus('❌ Please enter a valid email address', 'error');
            return;
        }
        
        if (this.recipients.includes(email)) {
            this.showStatus('❌ This email is already in the list', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${api.baseURL}/settings/recipients`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${api.authToken}`
                },
                body: JSON.stringify({ email: email })
            });
            
            if (response.ok) {
                this.recipients.push(email);
                this.renderRecipients();
                document.getElementById('recipientEmail').value = '';
                this.showStatus('✅ Recipient added successfully!', 'success');
            } else {
                this.showStatus('❌ Failed to add recipient', 'error');
            }
        } catch (error) {
            // If endpoint doesn't exist, just add locally
            this.recipients.push(email);
            this.renderRecipients();
            document.getElementById('recipientEmail').value = '';
            this.showStatus('✅ Recipient added (saved locally)', 'success');
        }
    },
    
    // Remove recipient
    async removeRecipient(email) {
        try {
            const response = await fetch(`${api.baseURL}/settings/recipients/${encodeURIComponent(email)}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${api.authToken}`
                }
            });
            
            if (response.ok || response.status === 404) {
                this.recipients = this.recipients.filter(e => e !== email);
                this.renderRecipients();
                this.showStatus('✅ Recipient removed', 'success');
            }
        } catch (error) {
            // If endpoint doesn't exist, just remove locally
            this.recipients = this.recipients.filter(e => e !== email);
            this.renderRecipients();
            this.showStatus('✅ Recipient removed', 'success');
        }
    },
    
    // Render recipients list
    renderRecipients() {
        const container = document.getElementById('recipientsList');
        
        if (this.recipients.length === 0) {
            container.innerHTML = '<p style="color: #5f6368; font-size: 14px;">No recipients added yet.</p>';
            return;
        }
        
        let html = '<div style="display: flex; flex-direction: column; gap: 8px;">';
        
        this.recipients.forEach(email => {
            html += `
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: #f8f9fa; border-radius: 4px; border: 1px solid #e8eaed;">
                    <span style="font-size: 14px;">${email}</span>
                    <button class="btn btn-outline" style="padding: 4px 12px; font-size: 13px;" onclick="settings.removeRecipient('${email}')">Remove</button>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    },
    
    // Validate email
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },
    
    // Show status message
    showStatus(message, type) {
        const statusDiv = document.getElementById('settingsStatus');
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.style.display = 'block';
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
};