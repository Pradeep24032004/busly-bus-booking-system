# utils/email_utils.py
import smtplib
from email.message import EmailMessage
from typing import Optional
from config import settings
import logging

logger = logging.getLogger("uvicorn.error")

def send_email_sync(to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
    """
    Synchronous email send using smtplib.
    Returns True on success, False on failure.
    """
    host = getattr(settings, "SMTP_HOST", None)
    port = getattr(settings, "SMTP_PORT", None)
    user = getattr(settings, "SMTP_USER", None)
    password = getattr(settings, "SMTP_PASSWORD", None)
    from_addr = getattr(settings, "SMTP_FROM", None)
    use_ssl = getattr(settings, "SMTP_USE_SSL", True)

    if not host or not port or not from_addr:
        logger.warning("SMTP not configured - skipping email send")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)

    if html:
        msg.add_alternative(html, subtype="html")

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=30) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            # STARTTLS flow
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        logger.info("Email sent to %s subject=%s", to_email, subject)
        return True
    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, e)
        return False
