from fastapi import APIRouter,status
from .. import crud

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.get("/login", status_code=status.HTTP_200_OK)
async def build_service():
    """Redirects to google consent screen, builds calendar service"""
    return crud.build_service()

@router.get("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """Logs user out, requires authetification to use google calendar api"""
    return crud.logout()