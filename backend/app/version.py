from fastapi import APIRouter

router = APIRouter()
__version__ = '0.4.2'


@router.get("/version")
async def get_version():
    return {"version": __version__}
