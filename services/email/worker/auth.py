# worker/email/tasks.py
from services.email.celery_app import celery_app
from services.email.utils.emails import send_html_email
from server.app.core.logging_config import logger

@celery_app.task
def send_welcome_email(to_email: str, username: str):
    """
    Sends a welcome email to a new user. This task is executed asynchronously using Celery.

    The function utilizes an HTML email template to send a personalized welcome message
    to the specified recipient email. The email includes a subject line and user-specific
    data, such as the username.

    Args:
        to_email (str): The recipient's email address.
        username (str): The username of the new user.

    Returns:
        None
    """
    if to_email and username:
        send_html_email(
            to_email=to_email,
            subject=f"Big things await you, {username}! Welcome to Calnio",
            template_name="account_created.html",
            context={"username": username}
        )
    else:
        logger.error("Failed to send welcome email: missing email or username")

@celery_app.task
def send_reset_password_email(to_email: str, reset_link: str):
    if to_email and reset_link:
        send_html_email(
            to_email=to_email,
            subject="Сброс пароля",
            template_name="reset_password.html",
            context={"reset_link": reset_link}
        )
    else:
        logger.error("Failed to send reset password email: missing email or reset link")