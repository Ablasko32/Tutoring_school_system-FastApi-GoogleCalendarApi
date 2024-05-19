from typing import List

from fastapi import APIRouter, Query, status

from .. import crud
from ..db_manager import db_dependancy
from ..models import Teachers
from ..schemas import ReservationResponse

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post(
    "/add_new", status_code=status.HTTP_201_CREATED, response_model=ReservationResponse
)
async def add_reservation(db: db_dependancy, class_id: int, student_id: int):
    return await crud.add_new_reservation(db, class_id, student_id)
