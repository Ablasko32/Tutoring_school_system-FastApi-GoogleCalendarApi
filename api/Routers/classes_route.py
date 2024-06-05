from typing import List

from fastapi import APIRouter, Query, status

from api.Calendar_utils.calendar_service_manager import service_dependancy
from api.db.db_manager import db_dependancy

from .. import crud
from ..schemas import ClassData, ClassResponse

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=ClassResponse
)
async def add_new_class(
    db: db_dependancy, manager: service_dependancy, class_data: ClassData
):
    """Add new class to database using ClassData schema,
    returns class model"""
    return await crud.add_new_class(db, class_data, manager)


@router.get("/all", status_code=status.HTTP_200_OK, response_model=List[ClassResponse])
async def get_all_classes(
    db: db_dependancy,
    class_name: str = None,
    target_date=None,
    description: str = None,
    page: int = Query(ge=1),
    limit: int = Query(10, gt=0),
):
    """Returns a list of classes,filter by class name,target_date or description, pagination via page and limit parameters"""
    return await crud.get_all_classes(
        db, page, limit, class_name, target_date, description
    )


@router.put("/update", status_code=status.HTTP_201_CREATED)
async def update_class(
    db: db_dependancy,
    manager: service_dependancy,
    class_data: ClassData,
    id: int = Query(gt=0),
):
    """Update class model via ID, use ClassData schema"""
    return await crud.update_class(db, class_data, id, manager)


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    db: db_dependancy, manager: service_dependancy, id: int = Query(gt=0)
):
    """Delete class via ID"""
    return await crud.delete_class(db, id, manager)
