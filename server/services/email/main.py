from server.services.email.worker.auth import send_welcome_email

send_welcome_email.delay(to_email="myroslavrepin@gmail.com", username="myroslavrepin")
