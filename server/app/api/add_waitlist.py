import os

from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from server.db.deps import async_get_db
from server.db.models.waitlist import Waitlist
from server.app.schemas.waitlist import WaitlistRequest
from server.app.core.logging_config import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from services.email.utils.email_sender import send_waitlist_email

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

@router.get('/waitlist', response_class=HTMLResponse)
async def waitlist(request: Request, db = Depends(async_get_db)):
    discount_amount = 10

    result = await db.execute(select(func.count()).select_from(Waitlist))
    current = result.scalar()

    remaining = max(0, 10 - current)
    return templates.TemplateResponse(
        "routes/waitlist.html",
        {
            "request": request,
            "remaining": remaining,
            "current": current,
            "discount_amount": discount_amount,
        }
    )
@router.post('/api/waitlist')
async def add_waitlist_email(
    request: WaitlistRequest,
    db: AsyncSession = Depends(async_get_db),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    try:
        waitlist = Waitlist(
            email=str(request.email),
        )
        db.add(waitlist)
        await db.commit()
        await db.refresh(waitlist)

        # Get the current position in waitlist
        result = await db.execute(select(func.count()).select_from(Waitlist))
        position = result.scalar()

        logger.debug(f"Added email {request.email} to waitlist at position {position}.")

        # Send confirmation email
        try:
            logger.info(f"Sending waitlist confirmation email to {request.email}")
            try:
                background_tasks.add_task(
                    send_waitlist_email,
                    destination=str(request.email),
                    name=str(request.email).split("@")[0].capitalize(),
                    position=position,
                    discount_amount=10
                )
                logger.info(f"Sent waitlist confirmation email to {request.email}")
            except Exception as bg_error:
                logger.error(f"Background task error for email {request.email}: {bg_error}")


            # await send_waitlist_email(
            #     destination=str(request.email),
            #     name=str(request.email).split("@")[0].capitalize(),
            #     position=position,
            #     discount_amount=10,
            # )
        except Exception as email_error:
            # Log the error but don't fail the request
            logger.error(f"Failed to send email to {request.email}: {email_error}")

        return JSONResponse({"message": "Successfully added to waitlist"}, status_code=200)

    except IntegrityError:
        logger.warning(f"Email {request.email} already in waitlist.")
        return JSONResponse({"message": "Email already registered"}, status_code=200)
    except ValueError as e:
        logger.warning(f"Error adding email {request.email} to waitlist: {e}")
        return JSONResponse({"message": str(e)}, status_code=400)
