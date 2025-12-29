# app/models/center_model.py
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import func, Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

if TYPE_CHECKING:
    from .user_model import User


class CenterBase(SQLModel):
    district: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    services: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    name: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    contact: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    address: str = Field(sa_column=Column(Text))
    location: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    landmark: Optional[str] = Field(
        default=None, sa_column=Column(String(100), nullable=True, index=True)
    )
    pincode: str = Field(sa_column=Column(String(10), nullable=False, index=True))
    email: Optional[str] = Field(default=None)
    clinic_url: Optional[str] = Field(default=None)
    google_map_url: Optional[str] = Field(default=None)


class Center(CenterBase, table=True):
    __tablename__ = "centers"

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

    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)

    user: "User" = Relationship(back_populates="centers")

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
        return f"<Center(id='{self.id}', name='{self.name}')>"
