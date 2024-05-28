from fastapi import HTTPException, status
from sqlalchemy import delete, select, table, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .logger import *
from .models import *
from .calendar_func import get_calendar_service,add_event_to_calendar,add_reservation_to_calendar,delete_reservation_from_calendar,delete_class_from_calendar,update_event_calendar

service = get_calendar_service()

async def delete_item(db: AsyncSession, id: int, Table: table):
    """Deletes item by item ID"""
    query = delete(Table).where(Table.id == id)
    result = await db.execute(query)
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deletion ID not found"
        )
    await db.commit()


async def update_item(db: AsyncSession, payload, id: int, Table: table):
    """Filter item by ID, update by unpacking item object,return a 404 if ID not found"""
    querry = select(Table).filter(Table.id == id)
    result = await db.execute(querry)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item ID not found"
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
    try:
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        return new_item
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item already exists: {e.orig}",
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


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


async def get_all_teacher_classes(db: AsyncSession, teacher_id: int):
    """Retruns teacher model with all classes"""
    query = (
        select(Teachers)
        .options(joinedload(Teachers.classes))
        .filter(Teachers.id == teacher_id)
    )
    teacher_result = await db.execute(query)
    teacher = teacher_result.scalars().first()
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher ID not found"
        )
    return teacher.classes


# classes router
async def get_all_classes(db: AsyncSession, page: int, limit: int):
    """Skip is the amount of pages to skip, limit is the amount of entries per page"""
    skip = (page - 1) * limit
    query = select(Classes).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def add_new_class(db: AsyncSession, class_data):
    """Add new class to db,cant assign two classes on the same datetime with same name, returns 409 conflict if tried"""
    target_start = class_data.class_start
    target_end = class_data.class_end
    target_name = class_data.class_name
    target_description = class_data.description
    query = (
        select(Classes)
        .filter(Classes.class_start == target_start)
        .filter(Classes.class_end == target_end)
        .filter(Classes.class_name==target_name)
    )
    result = await db.execute(query)
    rows = result.fetchall()
    if rows:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict with date/time, class already exists",
        )
    #add event to calendar
    calendar_event = add_event_to_calendar(service, target_name, target_start, target_end, target_description)
    if not calendar_event:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create calendar event")
    calendar_id = calendar_event.get("id").strip()
    api_logger.info("Calendar ID, %s", calendar_id)

    #add to database
    new_class = Classes(**class_data.dict(), event_id=calendar_id)
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class


async def delete_class(db: AsyncSession, id: int):
    """Deletes class by class ID"""

    select_query = select(Classes).filter(Classes.id == id)
    result = await db.execute(select_query)
    event = result.scalars().first()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class ID not found"
        )

    #delete event from calendar
    delete_class_from_calendar(service, event.event_id)

    #remove the class from db
    delete_query = delete(Classes).where(Classes.id == id)
    await db.execute(delete_query)
    await db.commit()

async def update_class(db: AsyncSession, payload, id: int,):
    """Update class and class event in calendar """
    querry = select(Classes).filter(Classes.id == id)
    result = await db.execute(querry)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item ID not found"
        )

    update_query = (
        update(Classes).where(Classes.id == id).values(**payload.dict(exclude_unset=True))
    )

    select_querry = (
        select(Classes).where(Classes.id == id)
    )

    select_result = await db.execute(select_querry)
    select_result = select_result.scalars().first()

    target_start = payload.class_start
    target_end = payload.class_end
    target_name = payload.class_name
    target_description = payload.description
    target_event_id = select_result.event_id


    update_event_calendar(service,target_event_id,target_name,target_description,target_start,target_end)



    await db.execute(update_query)
    await db.commit()
    return {"message": "updated"}




# reservations route
async def add_new_reservation(db: AsyncSession, class_id: int, student_id: int):
    """Function to add new reservation to db.Takes class_id and student_id, checks class capacity, wont allow reservation if class is full,
    returns a class with all students"""
    query = (
        select(Classes)
        .options(joinedload(Classes.students))
        .filter(Classes.id == class_id)
    )
    result = await db.execute(query)
    class_object = result.scalars().first()

    if class_object is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class ID not found"
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

    #update calendar event
    student_email = student.email
    event_id = class_object.event_id
    new_reservation = add_reservation_to_calendar(service,event_id,student_email)
    api_logger.info("New reservation")

    class_object.students.append(student)
    await db.commit()
    await db.refresh(class_object)

    return class_object


async def get_class_reservations(db: AsyncSession, class_id: int):
    """Returns joinedload class object with all students"""
    query = (
        select(Classes)
        .options(joinedload(Classes.students))
        .filter(Classes.id == class_id)
    )
    result = await db.execute(query)
    result_object = result.scalars().first()
    if result_object is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class ID not found"
        )
    return result_object


async def remove_student_from_reservations(
    db: AsyncSession, student_id: int, class_id: int
):
    """Remove student from linked class, returns 404 if student noti in class or if student/class ID not found"""
    query = (
        select(Classes)
        .options(joinedload(Classes.students))
        .filter(Classes.id == class_id)
    )
    result = await db.execute(query)
    class_object = result.scalars().first()
    if class_object is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class ID not found"
        )
    student_query = select(Students).filter(Students.id == student_id)
    student_result = await db.execute(student_query)
    student = student_result.scalars().first()

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student ID not found"
        )
    if student not in class_object.students:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not in the class"
        )
    class_object.students.remove(student)

    student_email = student.email
    updated_class = delete_reservation_from_calendar(service, event_id=class_object.event_id, target_student_mail=student_email)


    await db.commit()
    await db.refresh(class_object)
    return class_object


async def get_student_classes(db: AsyncSession, student_id: int):
    """Return all stundet classes"""
    query = (
        select(Students)
        .options(joinedload(Students.classes))
        .filter(Students.id == student_id)
    )
    student_result = await db.execute(query)
    student = student_result.scalars().first()

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student ID not found"
        )

    return student.classes


# invoices route


async def get_all_invoices(db: AsyncSession, page: int, limit: int):
    """Return all invoices,pagination via page and limit params"""
    skip = (page - 1) * limit
    query = select(Invoices).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_invoice_student(db: AsyncSession, id: int):
    """Preform joinedload and return student attribute of invoices"""
    query = (
        select(Invoices).options(joinedload(Invoices.student)).filter(Invoices.id == id)
    )
    result = await db.execute(query)
    invoice_rusult = result.scalars().first()
    if invoice_rusult is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice ID not found"
        )
    return invoice_rusult.student
