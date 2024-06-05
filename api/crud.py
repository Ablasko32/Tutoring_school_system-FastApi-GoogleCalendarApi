from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, table, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.Calendar_utils.calendar_func import (add_event_to_calendar,
                                              add_reservation_to_calendar,
                                              delete_class_from_calendar,
                                              delete_reservation_from_calendar,
                                              update_event_calendar)
from api.Calendar_utils.calendar_service_manager import service_dependancy
from api.db.models import *

from .logger import *


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


async def add_new_class(db: AsyncSession, class_data, manager: service_dependancy):
    """Add new class to db,cant assign two classes on the same datetime with same name, returns 409 conflict if tried,
    creates event on google calendar"""
    service = manager.get_calendar_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
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


async def delete_class(db: AsyncSession, id: int, manager: service_dependancy):
    """Deletes class by class ID, auto deletes calendar event, rises 404 if class ID not found, deletes linked invoices"""
    service = manager.get_calendar_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
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


async def update_class(db: AsyncSession, payload, id: int, manager: service_dependancy):
    """Update class in database and class event in google calendar using ClassData schema, rises 404 if class ID not found"""
    service = manager.get_calendar_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
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
    db: AsyncSession,
    class_id: int,
    student_id: int,
    amount: float,
    manager: service_dependancy,
):
    """Function to add new reservation to db.Takes class_id and student_id, checks class capacity, wont allow reservation if class is full,
    returns a class with all students, registers student email to atendees to google calendar event, auto creates invoice
    """
    service = manager.get_calendar_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
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
    db: AsyncSession, student_id: int, class_id: int, manager: service_dependancy
):
    """Remove student from linked class, returns 404 if student not in class or if student/class ID not found,auto deletes linked invoice"""
    service = manager.get_calendar_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
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


async def pay_invoice(db: AsyncSession, id: int):
    """Pay student invoice"""
    query = select(Invoices).filter(Invoices.id == id)
    result = await db.execute(query)
    target_invoice = result.scalars().first()
    if not target_invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice ID not found"
        )
    target_invoice.payment_status = True
    await db.commit()
    await db.refresh(target_invoice)
    return target_invoice


# teachers pay route


async def add_work_hours(db: AsyncSession, teacher_data):
    """Add work hours to TeacherHours models, cant enter twice for same date, same teacher same hours"""
    # query to see if hours are added for teacher ,date
    query = (
        select(TeacherHours)
        .filter(TeacherHours.teacher_id == teacher_data.teacher_id)
        .filter(TeacherHours.date == teacher_data.date)
        .filter(TeacherHours.hours == teacher_data.hours)
    )
    result = await db.execute(query)
    target_hours = result.scalars().first()
    if target_hours:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hours already loged for that teacher on that date",
        )

    new_work_day_hours = TeacherHours(**teacher_data.dict())
    db.add(new_work_day_hours)
    try:
        await db.commit()
        await db.refresh(new_work_day_hours)
        return new_work_day_hours
    except SQLAlchemyError as e:
        api_logger.critical(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An database error has occured",
        )


async def get_work_hours(
    db: AsyncSession,
    page: int,
    limit: int,
    teacher_id: int = None,
    start_date: date = None,
    end_date: date = None,
):
    """Returns a list of teacher work hours filter by teacher id , and combination of start and end times, paginated via page and limit query params"""

    skip = (page - 1) * limit

    base_query = select(TeacherHours)
    if teacher_id:
        base_query = base_query.filter(TeacherHours.teacher_id == teacher_id)
    if start_date and end_date:
        base_query = base_query.filter(TeacherHours.date.between(start_date, end_date))
    query = base_query.offset(skip).limit(limit)

    result = await db.execute(query)
    hours_list = result.scalars().all()
    if not hours_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target hours for date range and teacher id not found",
        )
    return hours_list


async def generate_paycheck(
    db: AsyncSession, start_date: date, end_date: date, teacher_id: int
):
    """Generates paycheck for teacher for given date range and saves it to table paychecks, counts school hours(45 mins)"""

    teacher_query = select(Teachers).filter(Teachers.id == teacher_id)
    teacher_result = await db.execute(teacher_query)

    target_teacher = teacher_result.scalars().first()

    query = (
        select(TeacherHours)
        .filter(TeacherHours.teacher_id == teacher_id)
        .filter(TeacherHours.date.between(start_date, end_date))
    )
    result = await db.execute(query)
    hours_list = result.scalars().all()
    if not hours_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target hours for date range and teacher id not found",
        )

    hourly = target_teacher.hourly

    work_hours = 0
    for hour in hours_list:
        work_hours += hour.hours

    school_hours = round(work_hours * 60 / 45, 2)
    payment_amount = round(school_hours * hourly, 2)

    check_exist_paycheck_query = (
        select(Paychecks)
        .filter(Paychecks.teacher_id == teacher_id)
        .filter(Paychecks.start_date == start_date)
        .filter(Paychecks.end_date == end_date)
    )
    result = await db.execute(check_exist_paycheck_query)
    existing_paycheck = result.scalars().first()
    if existing_paycheck:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paycheck for that period already exists",
        )

    new_paycheck = Paychecks(
        teacher_id=teacher_id,
        amount=payment_amount,
        school_hours=school_hours,
        work_hours=work_hours,
        hourly=hourly,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(new_paycheck)
    await db.commit()
    await db.refresh(new_paycheck)
    return new_paycheck


async def get_all_paychecks(
    db: AsyncSession,
    page: int,
    limit: int,
    teacher_id: int = None,
    is_payed: bool = None,
    start_date: date = None,
    end_date: date = None,
):
    """Returns all paychecks for, paginated via page and limit query params, filter by teacher id , payment status, and combination of start and end date"""
    skip = (page - 1) * limit
    base_query = select(Paychecks)
    if teacher_id:
        base_query = base_query.filter(Paychecks.teacher_id == teacher_id)
    if is_payed is not None:
        base_query = base_query.filter(Paychecks.payment_status == is_payed)
    if start_date and end_date:
        base_query = base_query.filter(Paychecks.start_date >= start_date).filter(
            Paychecks.end_date <= end_date
        )
    query = base_query.offset(skip).limit(limit)

    results = await db.execute(query)
    all_paychecks = results.scalars().all()
    if not all_paychecks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paychecks not found"
        )
    return all_paychecks


async def pay_paycheck(db: AsyncSession, paycheck_id: int):
    """Pay paycheck, change payment status of Paycheck model to true"""
    query = select(Paychecks).filter(Paychecks.id == paycheck_id)
    result = await db.execute(query)
    target_paycheck = result.scalars().first()
    if not target_paycheck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Paycheck ID not found"
        )
    target_paycheck.payment_status = True
    target_paycheck.payment_date = datetime.datetime.today().date()
    await db.commit()
    await db.refresh(target_paycheck)
    return target_paycheck
