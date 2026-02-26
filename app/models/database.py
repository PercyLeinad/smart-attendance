from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Date,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from datetime import datetime, timezone, date
from typing import Optional, List


# ---------------------------------------------------
# Base Class
# ---------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------
# Department Model
# ---------------------------------------------------

class Department(Base):
    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    employees: Mapped[List["Employee"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan"
    )


# ---------------------------------------------------
# Employee Model
# ---------------------------------------------------

class Employee(Base):
    __tablename__ = "employees"

    pf: Mapped[str] = mapped_column(String(20), primary_key=True)
    
    id_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    department_code: Mapped[Optional[str]] = mapped_column(
        ForeignKey("departments.code", ondelete="CASCADE"),
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    department: Mapped["Department"] = relationship(
        back_populates="employees"
    )

    logs: Mapped[List["AttendanceLog"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan"
    )


# ---------------------------------------------------
# Attendance Log Model
# ---------------------------------------------------

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    __table_args__ = (
        UniqueConstraint("pf", "date_only", name="uq_pf_date"),
        Index("ix_attendance_pf_date", "pf", "date_only"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    pf: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("employees.pf", ondelete="CASCADE"),
        nullable=False
    )

    arrival_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    date_only: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    checkout_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime
    )

    # Relationship
    employee: Mapped["Employee"] = relationship(
        back_populates="logs"
    )


# --------------------------------------------------
# Admin / Master Model
# ---------------------------------------------------

class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )