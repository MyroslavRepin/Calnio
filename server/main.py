import asyncio
import os
import sys
import logging
from loguru import logger
from dotenv import load_dotenv

from server.core.config import settings

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from server.app.api.v1.auth import router as api_auth_router
from server.app.api.v1.users import router as api_users_router

# === Intercept standard logging and redirect to Loguru ===
class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and redirect them to Loguru."""
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Remove default Loguru handler and add custom one
# logger.remove()

# Intercept all standard logging and redirect to Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Redirect uvicorn loggers to Loguru
for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler()]
    logging_logger.propagate = False

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception


# Creating Main App
app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Request body: {await request.body()}")
    logger.error(f"Validation errors: {exc.errors()}")
    
    # Transform validation errors to user-friendly format
    errors = []
    for error in exc.errors():
        field = error['loc'][-1] if error['loc'] else 'unknown'
        message = error.get('msg', 'Validation error')
        
        # Extract user-friendly message
        if 'ctx' in error and 'reason' in error['ctx']:
            message = error['ctx']['reason']
        
        errors.append({
            'field': field,
            'message': message,
            'input': error.get('input')
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation failed",
            "errors": errors,
            "raw_errors": exc.errors()  # Keep for debugging
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "https://reflectly.myroslavrepin.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "dist")
)


# Setting static / templates files into FastAPI
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

app.include_router(api_auth_router)
app.include_router(api_users_router)

# Catch-all route for SPA - serve index.html for client-side routing
@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_spa(full_path: str):
    """Serve index.html for SPA routing, fallback for other paths"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # If index.html doesn't exist, return 404
    raise HTTPException(status_code=404, detail="Frontend not built")

if "__main__" == __name__:
    import uvicorn
    uvicorn.run(app, host=settings.server_host, port=settings.server_port, reload=settings.server_reload)