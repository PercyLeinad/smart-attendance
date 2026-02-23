from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey
from datetime import datetime
from typing import Optional, List

class Base(DeclarativeBase):
    pass

class Department(Base):
    __tablename__ = "departments"
    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationship to employees
    employees: Mapped[List["Employee"]] = relationship(back_populates="department")

class Employee(Base):
    __tablename__ = "employees"
    pf: Mapped[str] = mapped_column(String(20), primary_key=True)
    id_number: Mapped[Optional[str]] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    department_code: Mapped[Optional[str]] = mapped_column(ForeignKey("departments.code"))
    
    department: Mapped["Department"] = relationship(back_populates="employees")
    logs: Mapped[List["AttendanceLog"]] = relationship(back_populates="employee")

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pf: Mapped[str] = mapped_column(String(50), ForeignKey("employees.pf"), nullable=False)
    arrival_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_only: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    checkout_time: Mapped[Optional[datetime]] = mapped_column(DateTime)

    employee: Mapped["Employee"] = relationship(back_populates="logs")

class Master(Base):
    __tablename__ = "masters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)