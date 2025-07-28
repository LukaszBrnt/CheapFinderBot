import smtplib
from email.message import EmailMessage
import os

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVERS = os.getenv("EMAIL_RECEIVERS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
SMTP_PASSWORD =os.getenv("SMTP_PASSWORD")

def send_email(body):
    msg = EmailMessage()
    msg["Subject"] = "✈️ Tanie loty "
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Bcc"] = EMAIL_RECEIVERS
    msg.set_content(body)
    print(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
       smtp.login(EMAIL_SENDER, SMTP_PASSWORD)
       smtp.send_message(msg)
    print("📧 Wysłano e-mail!")
