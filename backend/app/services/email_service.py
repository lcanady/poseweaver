from abc import ABC, abstractmethod
import os
import resend
from flask import current_app

class EmailProvider(ABC):
    """Abstract base class for email providers (Adapter Pattern)."""
    
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str) -> dict:
        pass

class ResendProvider(EmailProvider):
    """Resend implementation of EmailProvider."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('RESEND_API_KEY')
        if not self.api_key:
            current_app.logger.warning("RESEND_API_KEY not set. Email sending will fail.")
        resend.api_key = self.api_key

    def send_email(self, to_email: str, subject: str, html_content: str) -> dict:
        if not self.api_key:
            raise ValueError("Resend API key is missing")
            
        params = {
            "from": os.getenv('EMAIL_FROM', 'onboarding@resend.dev'),
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        try:
            email = resend.Emails.send(params)
            return email
        except Exception as e:
            current_app.logger.error(f"Failed to send email via Resend: {str(e)}")
            raise

class EmailService:
    """Service to handle email operations."""
    
    def __init__(self, provider: EmailProvider = None):
        self.provider = provider or ResendProvider()

    def send_password_reset(self, user_email: str, token: str):
        """Send password reset email."""
        # TODO: Replace with actual frontend URL construction
        reset_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
        
        subject = "Reset Your Password - PoseWeaver"
        html_content = f"""
        <h1>Password Reset Request</h1>
        <p>You requested a password reset for your PoseWeaver account.</p>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_link}">Reset Password</a>
        <p>If you didn't request this, please ignore this email.</p>
        """
        
        return self.provider.send_email(user_email, subject, html_content)
