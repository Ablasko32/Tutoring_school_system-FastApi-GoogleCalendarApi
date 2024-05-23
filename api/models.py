from sqlalchemy import (Boolean, Column, Date, Float, ForeignKey, Integer,
                        String, Text, Time,DateTime)
from sqlalchemy.orm import relationship

from .db_manager import Base


class Students(Base):
    """Keeps track of school students"""

    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(250), unique=True, nullable=False)
    phone_num = Column(String(100), nullable=False)
    parent_phone = Column(String(100))
    birth_year = Column(Integer, nullable=False)

    classes = relationship(
        "Classes", secondary="students_classes", back_populates="students", lazy=True
    )
    invoices = relationship("Invoices", back_populates="student")


class Teachers(Base):
    """Keeps track of teachers"""

    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(150),nullable=False)
    last_name = Column(String(150),nullable=False)
    email = Column(String(250), unique=True, nullable=False)
    phone_num = Column(String(100), nullable=False)
    hourly = Column(Float,nullable=False)
    hire_date = Column(Date,nullable=False)

    classes = relationship("Classes", back_populates="teacher")


class Classes(Base):
    """Keeps track of classes"""

    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    class_name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    class_size = Column(Integer, nullable=False)
    class_start = Column(DateTime, nullable=False)
    class_end = Column(DateTime, nullable=False)

    teacher = relationship("Teachers", back_populates="classes", uselist=False)
    students = relationship(
        "Students", secondary="students_classes", back_populates="classes", lazy=True
    )


class StudentsClasses(Base):
    """Many to many relationship between clases and students"""

    __tablename__ = "students_classes"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)


class Invoices(Base):
    """Keeps track of transactions"""

    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    invoice_date = Column(Date,nullable=False)
    description = Column(Text)
    payment_status = Column(Boolean, default=False)
    amount = Column(Float, nullable=False)

    student = relationship("Students", back_populates="invoices", uselist=False)
