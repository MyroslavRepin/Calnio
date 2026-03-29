import os
from fastapi.templating import Jinja2Templates

def import_templates():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.abspath(os.path.join(
        BASE_DIR, "..", "..", "..", "frontend"))

    templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates/routes"))

    return templates
