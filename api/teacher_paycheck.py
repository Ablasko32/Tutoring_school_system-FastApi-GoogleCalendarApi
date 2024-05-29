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
    total_payheck = []
    for class_ in teacher.classes:
        class_start = class_.class_start
        class_end = class_.class_end

        if (
            start_time <= class_start <= end_time
            and start_time <= class_end <= end_time
        ):
            lenght = class_end - class_start
            lenght = lenght.total_seconds() / 3600

            weeks = class_.frequency["weeks"]
            days_per_week = len(class_.frequency["by_day"].split(","))
            # print(lenght,weeks,days_per_week)

            # times weeks
            weekly = lenght * days_per_week
            total_sum = weekly * weeks
            # print("Total hours ",total_sum)
            # print("Total mins",total_sum*60)
            # print("Total 45 min hours",total_sum*60/45)
            total_school_hours = total_sum * 60 / 45
            paycheck = total_school_hours * hourly
            total_payheck.append(paycheck)
            # print(paycheck)
    # print(total_payheck)
    sum_pay = 0
    for i in total_payheck:
        sum_pay += i
    # print(sum_pay)

    description = (
        f"Paycheck for {teacher.first_name} {teacher.last_name} period between {start_time} and {end_time}.Total hours: "
        f"{total_school_hours}.Total payment amount: {sum_pay}."
        f"Hourly rate: {hourly}"
    )

    new_paycheck = Paychecks(
        teacher_id=teacher.id,
        end_date=end_time,
        start_date=start_time,
        amount=sum_pay,
        description=description,
        total_hours=total_sum,
        total_school_hours=total_school_hours,
        hourly=hourly,
    )
    db.add(new_paycheck)
    await db.commit()
    return {"message": new_paycheck.description}

    # start_time = datetime.fromisoformat(start_time_str)
    # end_time = datetime.fromisoformat(end_time_str)
    # lenght = end_time - start_time
    # lenght = lenght.total_seconds()/3600
    #
    #
    # #times weeks
    # weekly = lenght * days_per_week
    # total_sum = weekly * weeks
    # print("Total hours ",total_sum)
    # print("Total mins",total_sum*60)
    # print("Total 45 min hours",total_sum*60/45)
    # total_school_hours = total_sum*60/45
    # paycheck = total_school_hours * hourly
    # print("Total period paycheck",paycheck)


# db = get_db()


# calculate_paycheck(db,15,3,1,"2024-05-01T09:00:00","2024-05-01T10:00:00")
