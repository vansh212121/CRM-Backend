import re
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    EmailStr,
    HttpUrl,
    field_validator,
    model_validator,
)
from app.core.exceptions import ValidationError


class CenterBase(BaseModel):
    district: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="District where the center is located",
    )
    services: Dict[str, Any] = Field(
        ...,
        description="Services offered by the center",
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Center name",
    )
    contact: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Primary contact number",
    )
    address: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Full address of the center",
    )
    location: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Location / area name",
    )
    landmark: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Nearby landmark",
    )
    pincode: str = Field(
        ...,
        min_length=4,
        max_length=10,
        description="Postal / PIN code",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Center email address",
    )
    clinic_url: Optional[HttpUrl] = Field(
        None,
        description="Official clinic website URL",
    )
    google_map_url: Optional[HttpUrl] = Field(
        None,
        description="Google Maps location URL",
    )

    # ---------- STRING CLEANUP ----------
    @field_validator(
        "district",
        "name",
        "address",
        "location",
        "landmark",
        "pincode",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = " ".join(v.strip().split())
        if not v:
            raise ValidationError("Field cannot be empty or whitespace")
        return v

    # ---------- CONTACT VALIDATION ----------
    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[0-9+\-\s]{7,20}$", v):
            raise ValidationError("Invalid contact number format")
        return v

    # ---------- PINCODE VALIDATION ----------
    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        if not re.match(r"^[0-9A-Za-z\-]{4,10}$", v):
            raise ValidationError("Invalid pincode format")
        return v


# ======================================================
# CREATE / UPDATE
# ======================================================
class CenterCreate(CenterBase):
    """Schema for creating a center."""

    pass


class CenterUpdate(BaseModel):
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    services: Optional[Dict[str, Any]] = None
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    contact: Optional[str] = Field(None, min_length=7, max_length=20)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    landmark: Optional[str] = Field(None, min_length=2, max_length=200)
    pincode: Optional[str] = Field(None, min_length=4, max_length=10)
    email: Optional[EmailStr] = None
    clinic_url: Optional[HttpUrl] = None
    google_map_url: Optional[HttpUrl] = None

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure at least one field is provided for update."""
        if not any(v is not None for v in values.values()):
            raise ValidationError("At least one field must be provided for update")
        return values


# ======================================================
# RESPONSE
# ======================================================
class CenterResponse(CenterBase):
    """Center response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Center ID")
    user_id: uuid.UUID = Field(..., description="User ID")

    created_at: datetime = Field(..., description="Registration timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CenterListResponse(BaseModel):
    """Response for paginated center list."""

    items: List[CenterResponse] = Field(..., description="List of centers")
    total: int = Field(..., ge=0, description="Total number of centers")
    page: int = Field(..., ge=1, description="Current page number")
    pages: int = Field(..., ge=0, description="Total number of pages")
    size: int = Field(..., ge=1, le=100, description="Number of items per page")

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


class CenterSearchParams(BaseModel):
    """Parameters for searching centers."""

    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Search across name, district, location",
    )
    district: Optional[str] = None
    name: Optional[str] = None
    contact: Optional[str] = None
    location: Optional[str] = None
    landmark: Optional[str] = None
    pincode: Optional[str] = None
    email: Optional[EmailStr] = None

    created_after: Optional[date] = Field(
        None, description="Filter centers created after this date"
    )
    created_before: Optional[date] = Field(
        None, description="Filter centers created before this date"
    )

    @field_validator("search", "district", "name", "location", "landmark", "pincode")
    @classmethod
    def clean_search_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @model_validator(mode="after")
    def validate_date_range(self) -> "CenterSearchParams":
        if self.created_after and self.created_before:
            if self.created_after > self.created_before:
                raise ValidationError("created_after must be before created_before")
        return self


__all__ = [
    "CenterBase",
    "CenterCreate",
    "CenterUpdate",
    "CenterResponse",
    "CenterListResponse",
    "CenterSearchParams",
]
