import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import func, Column, String, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from enum import Enum


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class AppointmentBase(SQLModel):
    name: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    email: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    contact: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    status: AppointmentStatus = Field(
        sa_column=Column(SAEnum(AppointmentStatus), nullable=False, index=True),
        default=AppointmentStatus.PENDING,
    )
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    cancellation_reason: Optional[str] = Field(sa_column=Column(Text, default=None))
    appointment_date: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True)
    )


class Appointment(AppointmentBase, table=True):
    __tablename__ = "appointments"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            server_default=func.gen_random_uuid(),
            primary_key=True,
            index=True,
            nullable=False,
        ),
    )

    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )
    )

    def __repr__(self) -> str:
        return f"<Appointment(id='{self.id}', name='{self.name}')>"
