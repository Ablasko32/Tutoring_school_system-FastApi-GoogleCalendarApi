from fastapi import APIRouter, status

from .. import crud
from ..db_manager import db_dependancy
from ..schemas import StudentData, StudentResponse

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=StudentResponse
)
async def get_all(db: db_dependancy, student: StudentData):
    return await crud.get_all_students(db, student)


# @router.get("/all", status_code=status.HTTP_200_OK)
# async def get_one()
