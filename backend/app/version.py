from fastapi import APIRouter

router = APIRouter()
__version__ = '0.4.0'


@router.get("/version")
async def get_version():
    return {"version": __version__}
