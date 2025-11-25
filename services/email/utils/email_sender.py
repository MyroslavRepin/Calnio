
import os
from server.app.core.logging_config import logger

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Get the email template directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_DIR = BASE_DIR / "frontend" / "templates" / "email"

# Initialize Jinja2 environment
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


async def send_email(
    destination: str,
    subject: str,
    html_content: str,
    from_email: str = None,
):
    """
    Send an email using aiosmtplib.

    Args:
        destination: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        from_email: Sender email (defaults to EMAIL_USER from env)
    """
    # Get email config from environment
    smtp_host = os.getenv("EMAIL_HOST", "smtp.zohocloud.ca")
    smtp_port = int(os.getenv("EMAIL_PORT", "465"))
    smtp_user = os.getenv("EMAIL_USER", "dev@calnio.com")
    smtp_password = os.getenv("EMAIL_PASSWORD")

    # Log configuration (without password)
    logger.debug(f"Email Config: HOST={smtp_host}, PORT={smtp_port}, USER={smtp_user}, PASSWORD={'SET' if smtp_password else 'NOT SET'}")

    if not smtp_password:
        raise ValueError("EMAIL_PASSWORD not set in environment variables")

    from_email = from_email or smtp_user

    # Create message
    message = MIMEMultipart("alternative")
    message["From"] = from_email
    message["To"] = destination
    message["Subject"] = subject

    # Attach HTML content
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    # Send email
    try:
        logger.info(f"Sending email to {destination}")
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            use_tls=True,
        )
        logger.info(f"Email sent successfully to {destination}")
    except Exception as e:
        logger.error(f"SMTP Error: {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")


# --- Waitlist ---
async def send_waitlist_email(
    destination: str,
    name: str,
    position: int = None,
    discount_amount: int = 10,
):
    """
    Send a brutalist-styled waitlist confirmation email.

    Args:
        destination: Recipient email address
        name: Name of the person (or extracted from email)
        position: Position in the waitlist
        discount_amount: Discount percentage to offer
    """
    # If no name provided, use email prefix
    if not name or name.strip() == "":
        name = destination.split("@")[0].capitalize()

    # Load and render template
    template = jinja_env.get_template("waitlist_confirmation.html")
    html_content = template.render(
        name=name,
        email=destination,
        position=position or "TBD",
        discount_amount=discount_amount,
    )

    # Send email
    await send_email(
        destination=destination,
        subject="You're on the Calnio Waitlist ✓",
        html_content=html_content,
    )
