from datetime import date, time
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
    class_date: date
    class_hours: time


class StudentResponse(StudentBase):
    pass


class StudentData(StudentBase):
    pass

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
    pass


class TeacherData(TeacherBase):
    pass

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
    pass


class ClassData(ClassesBase):
    class Config:
        json_schema_extra = {
            "example": {
                "class_name": "Math",
                "teacher_id": 1,
                "class_size": 5,
                "class_date": "2024-05-01",
                "class_hours": "17:30",
            }
        }


class ReservationResponse(ClassesBase):
    students: List[StudentBase]
