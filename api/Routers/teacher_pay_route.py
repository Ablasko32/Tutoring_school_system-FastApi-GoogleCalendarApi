from datetime import date
from typing import List

from fastapi import APIRouter, Query, status

from .. import crud
from ..db_manager import db_dependancy
from ..models import TeacherHours
from ..schemas import TeacherHoursData, TeacherHoursResponse

router = APIRouter(prefix="/paycheck", tags=["Teacher paycheck"])


@router.post(
    "/add_work_hours",
    status_code=status.HTTP_201_CREATED,
    response_model=TeacherHoursResponse,
)
async def add_work_hours(db: db_dependancy, teacher_data: TeacherHoursData):
    """Add work hours for teacher id with date"""

    return await crud.add_work_hours(db, teacher_data)


@router.get(
    "/get_work_hours",
    status_code=status.HTTP_200_OK,
    response_model=List[TeacherHoursResponse],
)
async def get_work_hours(
    db: db_dependancy,
    start_date: date,
    end_date: date,
    teacher_id: int = Query(gt=0),
    page: int = Query(gt=0),
    limit: int = Query(gt=0),
):
    """Returns list of work hours for teacher id in specified date range"""

    return await crud.get_work_hours(db, teacher_id, start_date, end_date, page, limit)


@router.delete("/delete_hours", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_hours(db: db_dependancy, id: int = Query(gt=0)):
    """Deletes work hour entry based on ID"""
    return await crud.delete_item(db, id, TeacherHours)
