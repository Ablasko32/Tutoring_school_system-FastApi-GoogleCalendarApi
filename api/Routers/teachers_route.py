from typing import List

from fastapi import APIRouter, Query, status

from api.db.db_manager import db_dependancy
from api.db.models import Teachers

from .. import crud
from ..schemas import ClassResponse, TeacherData, TeacherResponse

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=TeacherResponse
)
async def add_new_class(db: db_dependancy, teacher: TeacherData):
    """Add new teacher to database using TeacherData schema,
    returns teacher model"""
    return await crud.add_item(db, teacher, Teachers)


@router.get(
    "/all", status_code=status.HTTP_200_OK, response_model=List[TeacherResponse]
)
async def get_all_teachers(
    db: db_dependancy,
    last_name: str = None,
    email: str = None,
    phone_num: str = None,
    page: int = Query(ge=1),
    limit: int = Query(10, gt=0),
):
    """Returns a list of teachers,filter by last name,email or phone number, pagination via page and limit parameters"""
    return await crud.get_all_teachers(db, page, limit, last_name, email, phone_num)


@router.put("/update", status_code=status.HTTP_201_CREATED)
async def update_teacher(
    db: db_dependancy, student: TeacherData, id: int = Query(gt=0)
):
    """Update teacher model via ID, use TeacherData schema"""
    return await crud.update_item(db, student, id, Teachers)


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(db: db_dependancy, id: int = Query(gt=0)):
    """Delete teacher via ID"""
    return await crud.delete_item(db, id, Teachers)


@router.get(
    "/classes", status_code=status.HTTP_200_OK, response_model=List[ClassResponse]
)
async def get_teacher_classes(db: db_dependancy, teacher_id: int = Query(gt=0)):
    """Returns teacher model with loaded classes using ClassResponse schema"""
    return await crud.get_all_teacher_classes(db, teacher_id)
