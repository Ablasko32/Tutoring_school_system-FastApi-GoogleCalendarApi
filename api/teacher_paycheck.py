from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import *





async def calculate_paycheck(
    db: AsyncSession, teacher_id: int, start_time_str=None, end_time_str=None
):
    """Calculates paycheck for teacher ID in given date range, saves to db to paychecks table"""
    start_time = datetime.datetime.fromisoformat(start_time_str)
    end_time = datetime.datetime.fromisoformat(end_time_str) + timedelta(days=1)

    query = (
        select(Teachers)
        .where(Teachers.id == teacher_id)
        .options(joinedload(Teachers.classes))
    )
    result = await db.execute(query)
    teacher = result.scalars().first()

    hourly = teacher.hourly
    print(start_time)
    print(end_time)

    paycheck = 0
    total_hours = 0
    total_school_hours = 0
    for class_ in teacher.classes:
        start_time_class = class_.class_start
        end_time_class = class_.class_end


        print(start_time_class,end_time_class)

        duration = (end_time_class - start_time_class).total_seconds()/3600

        instances = class_.classes_number

        class_working_hours = duration * instances
        total_hours += class_working_hours

        class_school_working_hours = round(class_working_hours *60/45, 2)
        total_school_hours += class_school_working_hours


        class_payout = class_school_working_hours * hourly
        paycheck += class_payout


    description = (
        f"Paycheck for {teacher.first_name} {teacher.last_name} period between {start_time.date()} and {end_time.date()}.Total hours: {total_hours}."
        f"Total school hours: "
        f"{total_school_hours}.Total payment amount: {paycheck}."
        f"Hourly rate: {hourly}"
    )

    new_paycheck = Paychecks(
        teacher_id=teacher.id,
        end_date=end_time,
        start_date=start_time,
        amount=paycheck,
        description=description,
        total_hours=total_hours,
        total_school_hours=total_school_hours,
        hourly=hourly,
    )
    db.add(new_paycheck)
    await db.commit()
    return {"message": new_paycheck.description}
