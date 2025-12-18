from fastapi import APIRouter

router = APIRouter()

__version__ = '1.17.0'


@router.get("/version")
async def get_version():
    return {"version": __version__}
