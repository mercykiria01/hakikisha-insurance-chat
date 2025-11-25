import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

print("📧 Testing email configuration...")

sender_email = os.getenv('EMAIL_USER')
sender_password = os.getenv('EMAIL_PASSWORD')
test_recipient = input("Enter your email to receive test OTP: ")

if not sender_email or not sender_password:
    print("❌ Email credentials not found in .env")
    exit(1)

print(f"Sender: {sender_email}")
print(f"Recipient: {test_recipient}")

try:
    # Create test message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Hakikisha Insurance - Test OTP"
    message["From"] = sender_email
    message["To"] = test_recipient
    
    html = """
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>Test OTP Email</h2>
        <p>Your test OTP code is: <strong>123456</strong></p>
        <p>If you received this, the email system is working correctly!</p>
      </body>
    </html>
    """
    
    part = MIMEText(html, "html")
    message.attach(part)
    
    # Send email
    print("\n📤 Sending test email...")
    with smtplib.SMTP(os.getenv('EMAIL_HOST', 'smtp.gmail.com'), 
                     int(os.getenv('EMAIL_PORT', 587))) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, test_recipient, message.as_string())
    
    print("✅ Test email sent successfully!")
    print(f"📬 Check your inbox at {test_recipient}")
    
except smtplib.SMTPAuthenticationError:
    print("❌ Authentication failed!")
    print("🔧 Make sure you're using a Gmail App Password, not your regular password")
    print("   Generate one at: https://myaccount.google.com/apppasswords")
    
except Exception as e:
    print(f"❌ Email send failed: {e}")