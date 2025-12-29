import re
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)
from app.core.exceptions import ValidationError


class UserBase(BaseModel):
    """Base schema for user shared fields."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=25,
        description="User's full name",
        examples=["John Doe"],
    )
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )

    @field_validator("name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        """Validate and clean names."""
        v = " ".join(v.strip().split())
        if not re.match(r"^[A-Za-z\s.'-]+$", v):
            raise ValidationError("Name contains invalid characters")
        return v


class UserCreate(UserBase):
    """Schema for creating new users."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=30,
        description="Strong password",
        examples=["SecurePass123!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password has uppercase, lowercase, digit, and special character."""
        if not re.search(r"[A-Z]", v):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValidationError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValidationError(
                "Password must contain at least one special character"
            )
        return v


class UserUpdate(BaseModel):
    """Schema for updating user details."""

    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=25,
        description="User's full name",
        examples=["John Doe"],
    )
    email: Optional[EmailStr] = Field(
        None,
        description="User's email address",
        examples=["user@example.com"],
    )

    @field_validator("name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        """Validate and clean names."""
        v = " ".join(v.strip().split())
        if not re.match(r"^[A-Za-z\s.'-]+$", v):
            raise ValidationError("Name contains invalid characters")
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure at least one field is provided for update."""
        if isinstance(values, dict) and not any(v is not None for v in values.values()):
            raise ValidationError("At least one field must be provided for update")
        return values


# ======== Response Schemas =========
class UserResponse(UserBase):
    """Basic user response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Registration timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ======== List and Search Schemas =========
class UserListResponse(BaseModel):
    """Response for paginated user list."""

    items: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., ge=0, description="Total number of users")
    page: int = Field(..., ge=1, description="Current page number")
    pages: int = Field(..., ge=0, description="Total number of pages")
    size: int = Field(..., ge=1, le=100, description="Number of items per page")

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class UserSearchParams(BaseModel):
    """Parameters for searching users."""

    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Search in email, name",
    )
    created_after: Optional[date] = Field(
        None, description="Filter users created after this date"
    )
    created_before: Optional[date] = Field(
        None, description="Filter users created before this date"
    )

    @field_validator("search")
    @classmethod
    def clean_search(cls, v: Optional[str]) -> Optional[str]:
        """Clean up search query."""
        return v.strip() if v else v

    @model_validator(mode="after")
    def validate_date_range(self) -> "UserSearchParams":
        """Ensure date range is valid."""
        if self.created_after and self.created_before:
            if self.created_after > self.created_before:
                raise ValidationError("created_after must be before created_before")
        return self
