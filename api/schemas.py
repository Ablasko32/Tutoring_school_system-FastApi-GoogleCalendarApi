from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class FrequencyBase(BaseModel):
    by_day: str
    freq: str
    weeks: int


class StudentBase(BaseModel):
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    email: str = EmailStr()
    phone_num: str = Field(min_length=5)
    parent_phone: Optional[str] = None
    birth_year: int

    class Config:
        json_encoders = {EmailStr: lambda v: str(v)}


class TeacherBase(BaseModel):
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    email: str = EmailStr()
    phone_num: str = Field(min_length=5, description="Phone number of employee")
    hourly: float = Field(description="Hourly pay rate for employee")
    hire_date: date = Field(description="Date of hire for employee, defaults to now")

    class Config:
        json_encoders = {EmailStr: lambda v: str(v)}


class ClassesBase(BaseModel):
    class_name: str = Field(min_length=2)
    teacher_id: int = Field(description="ID of teacher leading the class")
    class_size: int = Field(description="Max class capacity")
    class_start: datetime = Field(description="Start of class datetime")
    class_end: datetime = Field(
        description="End of class datetime, usually same date, moved for hours"
    )
    description: Optional[str] = None
    frequency: Optional[FrequencyBase] = None


class StudentResponse(StudentBase):
    id: int


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
    student_id: int = Field(description="ID of student")
    invoice_date: date = Field(description="Date of invoice creation")
    description: Optional[str] = None
    payment_status: bool = Field(description="Payment status, not payed-False")
    amount: float = Field(description="Amount for invoice payment")
    class_id: Optional[int] = None


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
    amount: float = Field(description="Amount for monthly payment")
    work_hours: float = Field(description="Full work hours for paycheck")
    school_hours: float = Field(description="School 45 mins hours for paycheck")
    hourly: float = Field(description="Hourly rate of teacher")
    start_date: date = Field(description="Start date of pay period")
    end_date: date = Field(description="End date of pay period")
    creation_date: date = Field(description="Date of paycheck creation")
    payment_status: bool = Field(description="Status of payment, not payed-False")


class PaycheckResponse(PaycheckBase):
    id: int
    payment_date: Optional[date] = None
