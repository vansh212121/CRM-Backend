import re
import uuid
from typing import Optional, List
from datetime import datetime, date, timezone
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)
from app.core.exceptions import ValidationError
from app.models.appointment_model import AppointmentStatus


# ======================================================
# BASE SCHEMA
# ======================================================
class AppointmentBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the user",
    )
    email: EmailStr = Field(..., min_length=2, description="User email address")
    contact: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Contact phone number",
    )
    appointment_date: datetime = Field(
        ..., description="Scheduled appointment date and time"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes from the user",
    )

    # -------- String cleanup --------
    @field_validator("name", "notes")
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = " ".join(v.strip().split())
        if not v:
            raise ValidationError("Field cannot be empty or whitespace")
        return v

    # -------- Contact validation --------
    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[0-9+\-\s]{7,20}$", v):
            raise ValidationError("Invalid contact number format")
        return v


# ======================================================
# CREATE SCHEMAS
# ======================================================
class CreatePublicAppointment(BaseModel):
    """Schema used when a public user creates an appointment request."""

    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    contact: str = Field(..., min_length=7, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("name", "notes")
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = " ".join(v.strip().split())
        if not v:
            raise ValidationError("Field cannot be empty or whitespace")
        return v

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[0-9+\-\s]{7,20}$", v):
            raise ValidationError("Invalid contact number format")
        return v


class CreateAdminAppointment(AppointmentBase):
    """Admin-created appointment with explicit appointment_date."""

    # -------- Appointment date validation --------
    @field_validator("appointment_date")
    @classmethod
    def validate_appointment_date(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        if v < datetime.now(timezone.utc):
            raise ValidationError("Appointment date must be in the future")
        return v


# ======================================================
# STATE TRANSITION SCHEMAS
# ======================================================
class ConfirmAppointment(BaseModel):
    appointment_date: datetime = Field(..., description="Confirmed appointment date")
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("appointment_date")
    @classmethod
    def validate_appointment_date(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        if v < datetime.now(timezone.utc):
            raise ValidationError("Appointment date must be in the future")
        return v


class RescheduleAppointment(BaseModel):
    appointment_date: datetime = Field(..., description="New appointment date")

    @field_validator("appointment_date")
    @classmethod
    def validate_appointment_date(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        if v < datetime.now(timezone.utc):
            raise ValidationError("Appointment date must be in the future")
        return v


class CancelAppointment(BaseModel):
    cancellation_reason: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Reason for appointment cancellation",
    )

    @field_validator("cancellation_reason")
    @classmethod
    def clean_reason(cls, v: str) -> str:
        v = " ".join(v.strip().split())
        if not v:
            raise ValidationError("Cancellation reason cannot be empty")
        return v


class CompleteAppointment(BaseModel):
    notes: Optional[str] = Field(
        None, max_length=1000, description="Final outcome notes"
    )

    # Validation for notes (reuse existing cleaner)
    @field_validator("notes")
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = " ".join(v.strip().split())
        return v


# ======================================================
# RESPONSE MODELS
# ======================================================
class AppointmentResponse(AppointmentBase):
    """Appointment response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Appointment ID")

    appointment_date: Optional[datetime] = Field(
        None, description="Scheduled appointment date"
    )

    cancellation_reason: Optional[str] = Field(
        None, description="Cancellation reason if appointment was cancelled"
    )
    status: AppointmentStatus = Field(..., description="Current appointment status")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ======================================================
# LIST RESPONSE
# ======================================================
class AppointmentListResponse(BaseModel):
    """Response for paginated appointment list."""

    items: List[AppointmentResponse] = Field(..., description="List of appointments")
    total: int = Field(..., ge=0, description="Total number of appointments")
    page: int = Field(..., ge=1, description="Current page number")
    pages: int = Field(..., ge=0, description="Total number of pages")
    size: int = Field(..., ge=1, le=100, description="Number of items per page")

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


# ======================================================
# SEARCH PARAMS
# ======================================================
class AppointmentSearchParams(BaseModel):
    """Parameters for searching appointments."""

    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Search across name, email, contact",
    )
    name: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[AppointmentStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    created_after: Optional[date] = Field(
        None, description="Filter appointments created after this date"
    )
    created_before: Optional[date] = Field(
        None, description="Filter appointments created before this date"
    )
    updated_after: Optional[date] = Field(
        None, description="Filter appointments created after this date"
    )
    updated_before: Optional[date] = Field(
        None, description="Filter appointments created before this date"
    )

    @field_validator("search", "name", "contact")
    @classmethod
    def clean_search_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @model_validator(mode="after")
    def validate_date_range(self) -> "AppointmentSearchParams":
        if self.created_after and self.created_before:
            if self.created_after > self.created_before:
                raise ValidationError("created_after must be before created_before")
        if self.updated_after and self.updated_before:
            if self.updated_after > self.updated_before:
                raise ValidationError("updated_after must be before updated_before")
        return self


# ======================================================
# EXPORTS
# ======================================================
__all__ = [
    "AppointmentBase",
    "CreatePublicAppointment",
    "CreateAdminAppointment",
    "ConfirmAppointment",
    "RescheduleAppointment",
    "CancelAppointment",
    "AppointmentResponse",
    "AppointmentListResponse",
    "AppointmentSearchParams",
]
