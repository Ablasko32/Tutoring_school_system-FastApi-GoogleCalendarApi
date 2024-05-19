from fastapi import HTTPException, status
from sqlalchemy import delete, select, table, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import *
from .schemas import *


async def delete_item(db: AsyncSession, id: int, Table: table):
    """Deletes student by student ID"""
    query = delete(Table).where(Table.id == id)
    result = await db.execute(query)
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deletion ID not found"
        )
    await db.commit()


async def update_item(db: AsyncSession, payload, id: int, Table: table):
    """Filter students by ID, update by unpacking student object,return a 404 if ID not found"""
    querry = select(Table).filter(Table.id == id)
    result = await db.execute(querry)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student ID not found"
        )

    update_query = (
        update(Table).where(Table.id == id).values(**payload.dict(exclude_unset=True))
    )
    await db.execute(update_query)
    await db.commit()
    return {"message": "updated"}


async def add_item(db: AsyncSession, payload, Table: table):
    """Add new student by passing student data item, returns new student"""
    new_item = Table(**payload.dict())
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


# student router


async def get_all_students(db: AsyncSession, page: int, limit: int):
    """Skip is the amount of pages to skip, limit is the amount of entries per page"""
    skip = (page - 1) * limit
    query = select(Students).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# teachers router
async def get_all_teachers(db: AsyncSession, page: int, limit: int):
    """Skip is the amount of pages to skip, limit is the amount of entries per page"""
    skip = (page - 1) * limit
    query = select(Teachers).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# classes router
async def get_all_classes(db: AsyncSession, page: int, limit: int):
    """Skip is the amount of pages to skip, limit is the amount of entries per page"""
    skip = (page - 1) * limit
    query = select(Classes).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def add_new_class(db: AsyncSession, class_data):
    target_date = class_data.class_date
    target_time = class_data.class_hours
    query = (
        select(Classes)
        .filter(Classes.class_date == target_date)
        .filter(Classes.class_hours == target_time)
    )
    result = await db.execute(query)
    rows = result.fetchall()
    if rows:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict with date/time, class already exists",
        )
    new_class = Classes(**class_data.dict())
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class


# reservations route
async def add_new_reservation(db: AsyncSession, class_id: int, student_id: int):
    query = (
        select(Classes)
        .options(joinedload(Classes.students))
        .filter(Classes.id == class_id)
    )
    result = await db.execute(query)
    class_object = result.scalars().first()

    if class_object is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    if len(class_object.students) >= class_object.class_size:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Class is full"
        )

    student_query = select(Students).filter(Students.id == student_id)
    student_result = await db.execute(student_query)
    student = student_result.scalars().first()

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student ID not found"
        )

    class_object.students.append(student)
    await db.commit()
    await db.refresh(class_object)

    return class_object
