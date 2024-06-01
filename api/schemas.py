import dataclasses
from datetime import date, datetime, time
from typing import List

from pydantic import BaseModel


class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_num: str
    parent_phone: str
    birth_year: int


class TeacherBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_num: str
    hourly: float
    hire_date: date


class ClassesBase(BaseModel):
    class_name: str
    teacher_id: int
    class_size: int
    class_start: datetime
    class_end: datetime
    description: str
    frequency: dict


class StudentResponse(StudentBase):
    id: int
    pass


class StudentData(StudentBase):

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Jackson",
                "email": "john@email.com",
                "phone_num": "9786531",
                "parent_phone": "9873611",
                "birth_year": 2007,
            }
        }


class TeacherResponse(TeacherBase):
    id: int


class TeacherData(TeacherBase):

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Jackson",
                "email": "john@email.com",
                "phone_num": "9786531",
                "hourly": 16.21,
                "hire_date": "2024-05-01",
            }
        }


class ClassResponse(ClassesBase):
    id: int
    event_id: str


class ClassData(ClassesBase):
    class Config:
        json_schema_extra = {
            "example": {
                "class_name": "Math",
                "teacher_id": 1,
                "class_size": 5,
                "class_start": "2024-05-01T09:00:00",
                "class_end": "2024-05-01T10:00:00",
                "description": "High school maths",
                "frequency": {"freq": "weekly", "by_day": "MO,WE,FR", "weeks": 2},
            }
        }


class ReservationResponse(ClassResponse):
    students: List[StudentResponse]


class InvoicesBase(BaseModel):
    student_id: int
    invoice_date: date
    description: str
    payment_status: bool
    amount: float
    class_id: int


class InvoiceData(InvoicesBase):
    class Config:
        json_schema_extra = {
            "example": {
                "student_id": 1,
                "invoice_date": "2024-05-01",
                "description": "New invoice",
                "payment_status": False,
                "amount": 17.50,
                "class_id": 1,
            }
        }


class InvoiceResponse(InvoicesBase):
    id: int


class TeacherHoursBase(BaseModel):
    teacher_id: int
    hours: float
    date: date


class TeacherHoursData(TeacherHoursBase):
    class Config:
        json_schema_extra = {
            "example": {"teacher_id": 1, "hours": 5, "date": "2024-05-01"}
        }


class TeacherHoursResponse(TeacherHoursBase):
    id: int


class PaycheckBase(BaseModel):
    teacher_id: int
    amount: float
    work_hours: float
    school_hours: float
    hourly: float
    start_date: date
    end_date: date
    creation_date: date
    payment_status: bool


class PaycheckResponse(PaycheckBase):
    id: int
    payment_date:date
