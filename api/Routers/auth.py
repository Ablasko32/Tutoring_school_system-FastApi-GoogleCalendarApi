from fastapi import APIRouter, status

from api.Calendar_utils.calendar_service_manager import service_dependancy

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login", status_code=status.HTTP_200_OK)
async def login(manager: service_dependancy):
    """Redirects to google consent screen, builds calendar service"""
    return manager.login()


@router.get("/logout", status_code=status.HTTP_200_OK)
async def logout(manager: service_dependancy):
    """Logout route, deletes token.json"""
    return manager.logout()
