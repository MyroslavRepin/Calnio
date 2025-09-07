from fastapi import APIRouter

router = APIRouter()

__version__ = '1.5.5'


@router.get("/version")
async def get_version():
    return {"version": __version__}
