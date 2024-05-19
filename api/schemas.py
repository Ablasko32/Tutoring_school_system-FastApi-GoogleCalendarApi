from pydantic import BaseModel


class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_num: str
    parent_phone: str
    age: int


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
                "age": 14,
            }
        }
