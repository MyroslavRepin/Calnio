"""
Test script for waitlist email sending
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from services.email.utils.email_sender import send_waitlist_email

# Load environment variables
load_dotenv()


async def test_email():
    """Test sending a waitlist confirmation email"""
    test_email = input("Enter test email address: ").strip()

    if not test_email:
        print("❌ No email provided")
        return

    print(f"📧 Sending test email to: {test_email}")

    try:
        await send_waitlist_email(
            destination=test_email,
            name=test_email.split("@")[0].capitalize(),
            position=42,
            discount_amount=10,
        )
        print("✅ Email sent successfully!")
        print(f"📬 Check your inbox at {test_email}")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_email())

