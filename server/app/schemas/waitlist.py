from pydantic import BaseModel, EmailStr

class WaitlistRequest(BaseModel):
    """
    Represents a waitlist request model.

    This class is used to manage data related to a waitlist request, where users can
    register their email addresses to join a waitlist.

    Attributes:
        email: An email address provided by the user for the waitlist.
    """
    email: EmailStr