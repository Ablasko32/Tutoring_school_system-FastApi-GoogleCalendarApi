from datetime import date
from typing import List

from fastapi import APIRouter, Query, status

from api.db.db_manager import db_dependancy
from api.db.models import Paychecks, TeacherHours

from .. import crud
from ..schemas import PaycheckResponse, TeacherHoursData, TeacherHoursResponse

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
    start_date: date = None,
    end_date: date = None,
    teacher_id: int = None,
    page: int = Query(gt=0),
    limit: int = Query(gt=0, default=20),
):
    """Returns a list of teacher work hours filter by teacher id , and combination of start and end times, paginated via page and limit query params"""

    return await crud.get_work_hours(db, page, limit, teacher_id, start_date, end_date)


@router.delete("/delete_hours", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_hours(db: db_dependancy, id: int = Query(gt=0)):
    """Deletes work hour entry based on ID"""
    return await crud.delete_item(db, id, TeacherHours)


@router.post(
    "/generate_paycheck",
    status_code=status.HTTP_201_CREATED,
    response_model=PaycheckResponse,
)
async def generate_paycheck(
    db: db_dependancy, start_date: date, end_date: date, teacher_id: int = Query(gt=0)
):
    """Generates paycheck for target date period"""

    return await crud.generate_paycheck(db, start_date, end_date, teacher_id)


@router.get(
    "/all_paychecks/",
    status_code=status.HTTP_200_OK,
    response_model=List[PaycheckResponse],
)
async def get_all_paychecks_for_teacher(
    db: db_dependancy,
    is_payed: bool = None,
    start_date: date = None,
    end_date: date = None,
    teacher_id: int = None,
    page: int = Query(gt=0),
    limit: int = Query(gt=0, default=20),
):
    """Returns list of all paychecks, optionaly filtered by teacher id, payment status, and combination of start and end date, paginated via page and limit query params"""

    return await crud.get_all_paychecks(
        db, page, limit, teacher_id, is_payed, start_date, end_date
    )


@router.delete("/delete_paycheck", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paycheck(db: db_dependancy, paycheck_id: int = Query(gt=0)):
    """Deletes paycheck based on paycheck ID"""
    return await crud.delete_item(db, paycheck_id, Paychecks)


@router.put(
    "/pay", status_code=status.HTTP_201_CREATED, response_model=PaycheckResponse
)
async def pay_paycheck(db: db_dependancy, paycheck_id: int = Query(gt=0)):
    """Pay paycheck, change payment status to true"""
    return await crud.pay_paycheck(db, paycheck_id)
