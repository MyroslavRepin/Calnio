import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from server.app.core.logging_config import logger

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

data = {
    "SMPT_HOST": SMTP_HOST,
    "SMTP_PORT": SMTP_PORT,
    "SMTP_USER": SMTP_USER,
    "SMTP_PASSWORD": SMTP_PASSWORD
}

logger.debug(f"SMTP config: {data}")

env = Environment(loader=FileSystemLoader("templates"))

def send_email(to_email: str, subject: str, text: str):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(text, "plain"))
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email}")
            return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def send_html_email(to_email: str, subject: str, template_name: str, context: dict):

    template = env.get_template(template_name)
    html_content = template.render(context)

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email}")
            return True

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
