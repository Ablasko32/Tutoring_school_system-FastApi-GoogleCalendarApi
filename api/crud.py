from sqlalchemy.ext.asyncio import AsyncSession

from .models import *
from .schemas import *


async def get_all_students(db: AsyncSession, student: StudentData):
    new_student = Students(**student.dict())
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student
