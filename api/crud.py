import datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, table, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .calendar_func import (add_event_to_calendar, add_reservation_to_calendar,
                            delete_class_from_calendar,
                            delete_reservation_from_calendar,
                            get_calendar_service, update_event_calendar)
from .logger import *
from .models import *
import os

service=None

def build_service():
    """Builds calendar service"""
    global service
    try:
        service = get_calendar_service()
        return {"message":"Logged in"}
    except Exception as e:
        api_logger.critical(e)
        return {"error":e}

def logout():
    """Removes token.json and sets service to none, logging user out and requiring authorization again"""
    global service
    service=None
    abs_path = os.path.abspath("api/Credentials/token.json")
    os.remove(abs_path)
    return {"message":"logged out"}




async def delete_item(db: AsyncSession, id: int, Table: table):
    """Deletes item by item ID, raised 404 if item ID not found"""
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
    """Add new student by passing student data item, returns new student, rises 409 if student exists"""
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


async def get_all_students(
    db: AsyncSession,
    page: int,
    limit: int,
    last_name: str = None,
    email: str = None,
    phone_num: str = None,
):
    """Skip is the amount of pages to skip, limit is the amount of entries per page, filter by last name, email or phone number"""
    skip = (page - 1) * limit
    base_query = select(Students)
    if last_name:
        base_query = base_query.filter(Students.last_name == last_name)
    if email:
        base_query = base_query.filter(Students.email == email)
    if phone_num:
        base_query = base_query.filter(Students.phone_num == phone_num)
    query = base_query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# teachers router
async def get_all_teachers(
    db: AsyncSession,
    page: int,
    limit: int,
    last_name: str = None,
    email: str = None,
    phone_num: str = None,
):
    """Skip is the amount of pages to skip, limit is the amount of entries per page, filter by last name, email or phone number"""
    skip = (page - 1) * limit

    base_query = select(Teachers)
    if last_name:
        base_query = base_query.filter(Teachers.last_name == last_name)
    if email:
        base_query = base_query.filter(Teachers.email == email)
    if phone_num:
        base_query = base_query.filter(Teachers.phone_num == phone_num)

    query = base_query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_all_teacher_classes(db: AsyncSession, teacher_id: int):
    """Retruns teacher model with all classes, rises 404 if teacher ID not found"""
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
async def get_all_classes(
    db: AsyncSession,
    page: int,
    limit: int,
    class_name: str = None,
    target_date=None,
    description: str = None,
):
    """Skip is the amount of pages to skip, limit is the amount of entries per page, filter by class name,target date or description"""
    skip = (page - 1) * limit
    base_query = select(Classes)
    if class_name:
        base_query = base_query.filter(Classes.class_name.ilike(f"%{class_name}%"))
    if target_date:
        base_query = base_query.where(func.date(Classes.class_start) == target_date)
    if description:
        base_query = base_query.filter(Classes.description.ilike(f"%{description}%"))

    query = base_query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def add_new_class(db: AsyncSession, class_data):
    """Add new class to db,cant assign two classes on the same datetime with same name, returns 409 conflict if tried,
    creates event on google calendar"""
    if service is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    target_start = class_data.class_start
    target_end = class_data.class_end
    target_name = class_data.class_name
    target_description = class_data.description
    target_frequency = class_data.frequency
    query = (
        select(Classes)
        .filter(Classes.class_start == target_start)
        .filter(Classes.class_end == target_end)
        .filter(Classes.class_name == target_name)
    )
    result = await db.execute(query)
    rows = result.fetchall()
    if rows:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict with date/time, class already exists",
        )
    # add event to calendar
    calendar_event = add_event_to_calendar(
        service,
        target_name,
        target_start,
        target_end,
        target_description,
        target_frequency,
    )
    if not calendar_event:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create calendar event",
        )
    calendar_id = calendar_event.get("id").strip()
    api_logger.info("Calendar ID, %s", calendar_id)

    # add to database
    new_class = Classes(**class_data.dict(), event_id=calendar_id)
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class


async def delete_class(db: AsyncSession, id: int):
    """Deletes class by class ID, auto deletes calendar event, rises 404 if class ID not found, deletes linked invoices"""

    if service is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    select_query = select(Classes).filter(Classes.id == id)
    result = await db.execute(select_query)
    event = result.scalars().first()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class ID not found"
        )

    # delete event from calendar
    delete_class_from_calendar(service, event.event_id)

    # remove the class from db
    delete_query = delete(Classes).where(Classes.id == id)
    await db.execute(delete_query)

    # invoice deletion
    invoice_querry = delete(Invoices).filter(Invoices.class_id == event.id)
    result = await db.execute(invoice_querry)

    # studentclass deletion
    reservation_deletion_querry = delete(StudentsClasses).filter(
        StudentsClasses.class_id == event.id
    )
    result = await db.execute(reservation_deletion_querry)

    await db.commit()


async def update_class(
    db: AsyncSession,
    payload,
    id: int,
):
    """Update class in database and class event in google calendar using ClassData schema, rises 404 if class ID not found"""
    if service is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    querry = select(Classes).filter(Classes.id == id)
    result = await db.execute(querry)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class ID not found"
        )

    update_query = (
        update(Classes)
        .where(Classes.id == id)
        .values(**payload.dict(exclude_unset=True))
    )

    select_querry = select(Classes).where(Classes.id == id)

    select_result = await db.execute(select_querry)
    select_result = select_result.scalars().first()

    target_start = payload.class_start
    target_end = payload.class_end
    target_name = payload.class_name
    target_description = payload.description
    target_event_id = select_result.event_id
    target_frequency = select_result.frequency

    update_event_calendar(
        service,
        target_event_id,
        target_name,
        target_description,
        target_start,
        target_end,
        target_frequency,
    )

    await db.execute(update_query)
    await db.commit()
    return {"message": "updated"}


# reservations route
async def add_new_reservation(
    db: AsyncSession, class_id: int, student_id: int, amount: float
):
    """Function to add new reservation to db.Takes class_id and student_id, checks class capacity, wont allow reservation if class is full,
    returns a class with all students, registers student email to atendees to google calendar event, auto creates invoice
    """
    if service is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
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

    # update calendar event
    student_email = student.email
    event_id = class_object.event_id
    new_reservation = add_reservation_to_calendar(service, event_id, student_email)
    api_logger.info("New reservation")

    class_object.students.append(student)
    await db.commit()
    await db.refresh(class_object)

    # new invoice creation

    description = (
        f"Reservation for: {class_object.class_name}, at {class_object.class_start},"
        f" Class description: {class_object.description}"
    )

    new_invoice = Invoices(
        student_id=student.id,
        invoice_date=datetime.datetime.now(),
        description=description,
        amount=amount,
        class_id=class_object.id,
    )

    db.add(new_invoice)
    await db.commit()

    return class_object


async def get_class_reservations(db: AsyncSession, class_id: int):
    """Returns joinedload class object with all students atteding class"""
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
    """Remove student from linked class, returns 404 if student not in class or if student/class ID not found,auto deletes linked invoice"""
    if service is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
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
    updated_class = delete_reservation_from_calendar(
        service, event_id=class_object.event_id, target_student_mail=student_email
    )

    # invoice deletion
    invoice_querry = delete(Invoices).filter(Invoices.student_id == student.id)
    result = await db.execute(invoice_querry)

    # studentclass deletion
    reservation_deletion_querry = (
        delete(StudentsClasses)
        .filter(StudentsClasses.student_id == student.id)
        .filter(StudentsClasses.class_id == class_object.id)
    )
    result = await db.execute(reservation_deletion_querry)

    await db.commit()
    await db.refresh(class_object)

    return class_object


async def get_student_classes(db: AsyncSession, student_id: int):
    """Return all student classes"""
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


async def get_all_invoices(
    db: AsyncSession,
    page: int,
    limit: int,
    payment_status: bool = None,
    invoice_date=None,
):
    """Return all invoices,pagination via page and limit params, filter by payment status or invoice date"""
    skip = (page - 1) * limit

    base_query = select(Invoices)
    if payment_status:
        base_query = base_query.filter(Invoices.payment_status == payment_status)
    if invoice_date:
        base_query = base_query.filter(Invoices.invoice_date == invoice_date)

    query = base_query.offset(skip).limit(limit)
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
