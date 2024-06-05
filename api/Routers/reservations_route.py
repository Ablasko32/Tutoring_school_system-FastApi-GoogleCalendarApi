from typing import List

from fastapi import APIRouter, Query, status

from api.Calendar_utils.calendar_service_manager import service_dependancy
from api.db.db_manager import db_dependancy

from .. import crud
from ..schemas import ClassResponse, ReservationResponse

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post(
    "/add_new", status_code=status.HTTP_201_CREATED, response_model=ReservationResponse
)
async def add_reservation(
    db: db_dependancy,
    manager: service_dependancy,
    class_id: int = Query(gt=0),
    student_id: int = Query(gt=0),
    amount: float = Query(gt=0),
):
    """Add new class reservation, link student with classes, returns class with all students via
    ReservationResponse"""
    return await crud.add_new_reservation(db, class_id, student_id, amount, manager)


@router.get(
    "/all_students", status_code=status.HTTP_200_OK, response_model=ReservationResponse
)
async def get_class_reservations(db: db_dependancy, class_id: int = Query(gt=0)):
    return await crud.get_class_reservations(db, class_id)


@router.put(
    "/remove_student",
    status_code=status.HTTP_200_OK,
    response_model=ReservationResponse,
)
async def remove_student_from_reservations(
    db: db_dependancy,
    manager: service_dependancy,
    class_id: int = Query(gt=0),
    student_id: int = Query(gt=0),
):
    return await crud.remove_student_from_reservations(
        db, student_id, class_id, manager
    )


@router.get(
    "/student", status_code=status.HTTP_200_OK, response_model=List[ClassResponse]
)
async def get_student_reservations(db: db_dependancy, student_id: int = Query(gt=0)):
    return await crud.get_student_classes(db, student_id)
