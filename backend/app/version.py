from fastapi import APIRouter

router = APIRouter()
__version__ = '1.2.1'


@router.get("/version")
async def get_version():
    return {"version": __version__}
