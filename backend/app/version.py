from fastapi import FastAPI
from app.version import __version__

app = FastAPI()
__version__ = '0.1.0'


@app.get("/version")
async def get_version():
    return {"version": __version__}
