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

    code: Mapped[str] = mapped_column(
        String(20),
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        unique=True
    )

    employees: Mapped[List["Employee"]] = relationship(
        back_populates="department"
    )


# ---------------------------------------------------
# Employee Model
# ---------------------------------------------------

class Employee(Base):
    __tablename__ = "employees"

    pf: Mapped[str] = mapped_column(
        String(20),
        primary_key=True
    )

    id_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        # unique=True, 
        nullable=True,
        index=True
    )
    department_code: Mapped[Optional[str]] = mapped_column(
        ForeignKey("departments.code", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    department: Mapped[Optional["Department"]] = relationship(
        back_populates="employees"
    )
    personal_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        # unique=True,
        nullable=True,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Active",
        index=True
    )

    logs: Mapped[List["AttendanceLog"]] = relationship(
        back_populates="employee"
    )

# ---------------------------------------------------
# Attendance Log Model
# ---------------------------------------------------

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    __table_args__ = (
        UniqueConstraint("pf", "date_only", name="uq_pf_date"),
        Index("ix_pf_date", "pf", "date_only"),
        Index("ix_date_only", "date_only"),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    pf: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("employees.pf"),
        nullable=False
    )

    arrival_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    checkout_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime
    )

    date_only: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

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
        nullable=False,
        index=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )