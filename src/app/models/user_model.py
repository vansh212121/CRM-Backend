import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import func, Column, String, DateTime
from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
)
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .center_model import Center


class UserBase(SQLModel):
    name: str = Field(
        sa_column=Column(
            String(40),
            nullable=False,
            index=True,
        )
    )
    email: str = Field(
        sa_column=Column(String(200), unique=True, nullable=False, index=True)
    )


class User(UserBase, table=True):
    __tablename__ = "users"

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

    hashed_password: str = Field(nullable=False, exclude=True)

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
    tokens_valid_from_utc: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships
    centers: List["Center"] = Relationship(back_populates="user")

    # --- Computed properties (data-focused) ---
    def __repr__(self) -> str:
        return f"<User(id='{self.id}', email='{self.email}')>"
