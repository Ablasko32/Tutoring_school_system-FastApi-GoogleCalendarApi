from typing import List

from fastapi import APIRouter, Query, status

from .. import crud
from ..db_manager import db_dependancy
from ..schemas import StudentData, StudentResponse

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=StudentResponse
)
async def add_new_student(db: db_dependancy, student: StudentData):
    """Add new student to database using StudentData schema,
    returns student model"""
    return await crud.add_student(db, student)


@router.get(
    "/all", status_code=status.HTTP_200_OK, response_model=List[StudentResponse]
)
async def get_all_students(
    db: db_dependancy, page: int = Query(ge=1), limit: int = Query(10, gt=0)
):
    """Returns a list of students, pagination via page and limit parameters"""
    return await crud.get_all_students(db, page, limit)


@router.put("/update", status_code=status.HTTP_201_CREATED)
async def update_student(
    db: db_dependancy, student: StudentData, id: int = Query(gt=0)
):
    """Update student model via ID, use StudentData schema"""
    return await crud.update_student(db, student, id)


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(db: db_dependancy, id: int = Query(gt=0)):
    """Delete student via ID"""
    return await crud.delete_student(db, id)
