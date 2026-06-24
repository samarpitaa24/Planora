import os
import smtplib
import traceback
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv


def _email_debug(message):
    print(f"[PLANORA][forgot-password][email] {message}", flush=True)


def _print_reset_link_fallback(to_email, reset_link, reason):
    print("\n" + "=" * 72, flush=True)
    print(" [PLANORA PASSWORD RESET LINK - TERMINAL FALLBACK]", flush=True)
    print(f" Reason: {reason}", flush=True)
    print(f" To: {to_email}", flush=True)
    print(f" Reset Link: {reset_link}", flush=True)
    print("=" * 72 + "\n", flush=True)


def send_reset_email(to_email, reset_link):
    """
    Sends a password reset email to the user.
    If SMTP credentials are not configured in the environment,
    it falls back to printing the link to the console for easy local testing.
    """
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)

    print("=== send_reset_email() EXECUTED ===", flush=True)
    print("To Email:", to_email, flush=True)
    _email_debug(f"send_reset_email() called for {to_email}")

    mail_server = os.getenv("MAIL_SERVER") or os.getenv("SMTP_SERVER") or "smtp.gmail.com"
    try:
        mail_port = int(os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT") or 587)
    except (ValueError, TypeError):
        mail_port = 587
        
    mail_username = os.getenv("MAIL_USERNAME") or os.getenv("SMTP_USERNAME") or os.getenv("EMAIL_USER")
    mail_password = os.getenv("MAIL_PASSWORD") or os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_PASSWORD")
    mail_sender = os.getenv("MAIL_DEFAULT_SENDER") or os.getenv("SMTP_SENDER") or mail_username

    print("MAIL_SERVER:", mail_server, flush=True)
    print("MAIL_PORT:", mail_port, flush=True)
    print("MAIL_USERNAME:", mail_username, flush=True)
    print("MAIL_DEFAULT_SENDER:", mail_sender, flush=True)
    print("MAIL_PASSWORD loaded:", bool(mail_password), flush=True)

    _email_debug(
        "SMTP config: "
        f"server={mail_server}, port={mail_port}, "
        f"username_set={bool(mail_username)}, password_set={bool(mail_password)}, "
        f"sender={mail_sender or 'not set'}"
    )
    
    if not mail_username or not mail_password:
        _print_reset_link_fallback(to_email, reset_link, "SMTP username or password is missing")
        return {
            "ok": True,
            "method": "terminal_fallback",
            "message": "SMTP credentials missing; reset link printed in terminal.",
        }

    # Create MIMEMultipart email message
    msg = MIMEMultipart()
    msg['From'] = mail_sender
    msg['To'] = to_email
    msg['Subject'] = "Reset Your Planora Password"
    
    body = f"""Hello,

You requested a password reset for your Planora account.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request this reset, please ignore this email.

Best regards,
The Planora Team
"""
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        _email_debug("Attempting SMTP delivery")
        print("Connecting to SMTP server...", flush=True)
        if mail_port == 465:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=20)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=20)
            server.starttls()
            
        server.login(mail_username, mail_password)
        print("SMTP Login Successful", flush=True)
        server.sendmail(mail_sender, to_email, msg.as_string())
        server.quit()
        print("Email Sent Successfully", flush=True)
        _email_debug(f"SMTP email sent successfully to {to_email}")
        return {
            "ok": True,
            "method": "smtp",
            "message": "Password reset email sent successfully.",
        }
    except Exception as e:
        _email_debug(f"SMTP delivery failed: {e}")
        print("SMTP ERROR:", str(e), flush=True)
        print(traceback.format_exc(), flush=True)
        _print_reset_link_fallback(to_email, reset_link, f"SMTP delivery failed: {e}")
        return {
            "ok": True,
            "method": "smtp_error_fallback",
            "message": "SMTP failed; reset link printed in terminal.",
        }
