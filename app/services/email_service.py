"""
Email Service for OTP verification
Handles OTP generation and sending via Gmail SMTP
"""

import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from datetime import datetime, timedelta
import hashlib


def generate_otp(length=6):
    """Generate a random numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


def hash_otp(otp):
    """Hash OTP for secure storage"""
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp_hash(otp, hashed_otp):
    """Verify OTP against stored hash"""
    return hash_otp(otp) == hashed_otp


def get_otp_expiry():
    """Get OTP expiry timestamp (3 minutes from now)"""
    expiry_minutes = current_app.config.get("OTP_EXPIRY_MINUTES", 3)
    return datetime.utcnow() + timedelta(minutes=expiry_minutes)


def create_otp_email_html(otp, user_name=None):
    """Create beautiful HTML email template matching app design"""
    display_name = user_name if user_name else "there"
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - KG AI</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #FAF9F5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 480px; width: 100%; border-collapse: collapse;">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="padding-bottom: 32px;">
                            <div style="font-family: Georgia, 'Times New Roman', serif; font-size: 28px; font-weight: 600; color: #1A1A1A;">
                                <span style="color: #D97757;">📦</span> KG AI
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Main Card -->
                    <tr>
                        <td>
                            <table role="presentation" style="width: 100%; background-color: #FFFFFF; border-radius: 16px; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08); border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 40px 36px;">
                                        <!-- Greeting -->
                                        <h1 style="margin: 0 0 8px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 500; color: #1A1A1A;">
                                            Hey {display_name}! 👋
                                        </h1>
                                        <p style="margin: 0 0 32px 0; font-size: 16px; color: #5A5A5A; line-height: 1.6;">
                                            Enter this code to verify your email and get started with Knowledge Graph AI.
                                        </p>
                                        
                                        <!-- OTP Code Box -->
                                        <div style="background: linear-gradient(135deg, #FDF8F5 0%, #FAF9F5 100%); border: 2px solid #F0E6E0; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
                                            <div style="font-family: 'Courier New', monospace; font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #D97757;">
                                                {otp}
                                            </div>
                                        </div>
                                        
                                        <!-- Timer Notice -->
                                        <div style="display: flex; align-items: center; background-color: #FFF8F5; border-radius: 8px; padding: 12px 16px; margin-bottom: 24px;">
                                            <span style="font-size: 14px; color: #B85A2E;">
                                                ⏱️ This code expires in <strong>3 minutes</strong>
                                            </span>
                                        </div>
                                        
                                        <!-- Security Notice -->
                                        <p style="margin: 0; font-size: 13px; color: #8B8680; line-height: 1.5;">
                                            🔒 <strong>Security tip:</strong> Never share this code with anyone. Our team will never ask for it.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td align="center" style="padding-top: 32px;">
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #8B8680;">
                                Didn't request this code? You can safely ignore this email.
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #A8A49E;">
                                © 2024 Knowledge Graph AI. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


def create_otp_email_text(otp, user_name=None):
    """Create plain text email fallback"""
    display_name = user_name if user_name else "there"
    
    text = f"""
Hey {display_name}!

Your verification code for Knowledge Graph AI is:

    {otp}

This code expires in 3 minutes.

Security tip: Never share this code with anyone. Our team will never ask for it.

Didn't request this code? You can safely ignore this email.

© 2024 Knowledge Graph AI
"""
    return text


def send_otp_email(to_email, otp, user_name=None):
    """Send OTP verification email via Gmail SMTP"""
    try:
        smtp_server = current_app.config.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = current_app.config.get("SMTP_PORT", 587)
        smtp_email = current_app.config.get("SMTP_EMAIL")
        smtp_password = current_app.config.get("SMTP_APP_PASSWORD")
        
        if not smtp_email or not smtp_password:
            print("Error: SMTP credentials not configured")
            return False
        
        # Remove spaces from app password (Google format has spaces)
        smtp_password = smtp_password.replace(" ", "")
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "🔐 Your KG AI Verification Code"
        message["From"] = f"KG AI <{smtp_email}>"
        message["To"] = to_email
        
        # Create plain text and HTML versions
        text_content = create_otp_email_text(otp, user_name)
        html_content = create_otp_email_html(otp, user_name)
        
        # Attach both versions (email client will choose the best one)
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, message.as_string())
        
        print(f"OTP email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        import traceback
        traceback.print_exc()
        return False

