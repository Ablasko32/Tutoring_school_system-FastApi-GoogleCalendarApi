from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import *
from .schemas import *


# student router
async def add_student(db: AsyncSession, student: StudentData):
    """Add new student by passing student data item, returns new student"""
    new_student = Students(**student.dict())
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student


async def get_all_students(db: AsyncSession, page: int, limit: int):
    """Skip is the amount of pages to skip, limit is the amount of entries per page"""
    skip = (page - 1) * limit
    query = select(Students).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_student(db: AsyncSession, student: StudentData, id: int):
    """Filter students by ID, update by unpacking student object,return a 404 if ID not found"""
    querry = select(Students).filter(Students.id == id)
    result = await db.execute(querry)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student ID not found"
        )

    update_query = (
        update(Students)
        .where(Students.id == id)
        .values(**student.dict(exclude_unset=True))
    )
    await db.execute(update_query)
    await db.commit()
    return {"message": "updated"}


async def delete_student(db: AsyncSession, id: int):
    """Deletes student by student ID"""
    query = delete(Students).where(Students.id == id)
    await db.execute(query)
    await db.commit()
