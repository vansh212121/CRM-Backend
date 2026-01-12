import logging
import uuid
from typing import Optional, List, Dict, Any, TypeVar, Generic, Tuple
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func, and_, or_, delete

from app.core.exception_utils import handle_exceptions
from app.core.exceptions import InternalServerError

from app.models.appointment_model import Appointment, AppointmentStatus


logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository providing consistent interface for database operations."""

    def __init__(self, model: type[T]):
        self.model = model

    @abstractmethod
    async def get(self, db: AsyncSession, *, obj_id: Any) -> Optional[T]:
        """Get entity by its primary key."""
        pass

    @abstractmethod
    async def create(self, db: AsyncSession, *, obj_in: Any) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def update(self, db: AsyncSession, *, db_obj: T, obj_in: Any) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, db: AsyncSession, *, obj_id: Any) -> None:
        """Delete an entity by its primary key."""


class AppointmentRepository(BaseRepository[Appointment]):
    """Repository for all database operations related to the Appointment model."""

    def __init__(self):
        super().__init__(Appointment)
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @handle_exceptions(
        default_exception=InternalServerError,
        message="An unexpected database error occurred.",
    )
    async def get(
        self, db: AsyncSession, *, obj_id: uuid.UUID
    ) -> Optional[Appointment]:
        """get a Appointment by it's ID"""

        statement = select(self.model).where(self.model.id == obj_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    @handle_exceptions(
        default_exception=InternalServerError,
        message="An unexpected database error occurred.",
    )
    async def get_by_email(
        self, db: AsyncSession, *, email: str
    ) -> Optional[Appointment]:
        """fetch by email"""
        statement = select(self.model).where(
            self.model.email == email, self.model.status == AppointmentStatus.PENDING
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    @handle_exceptions(
        default_exception=InternalServerError,
        message="An unexpected database error occurred.",
    )
    async def get_all(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Appointment], int]:
        """Get multiple Appointment with filtering and pagination."""

        query = select(self.model)

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Apply ordering
        query = self._apply_ordering(query, order_by, order_desc)

        # Apply pagination
        paginated_query = query.offset(skip).limit(limit)
        result = await db.execute(paginated_query)
        appointments = result.scalars().all()

        return appointments, total

    @handle_exceptions(
        default_exception=InternalServerError,
        message="An unexpected database error occurred.",
    )
    async def create(self, db: AsyncSession, *, db_obj: Appointment) -> Appointment:
        """create an appointment (admin only)"""

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        self._logger.info(f"Appointment created: {db_obj.id}")
        return db_obj

    @handle_exceptions(
        default_exception=InternalServerError,
        message="An unexpected database error occurred.",
    )
    async def update(
        self,
        db: AsyncSession,
        *,
        appointment: Appointment,
        fields_to_update: Dict[str, any],
    ) -> Appointment:
        """Update an appointemt (for confirm, reject and reschedule)"""

        for field, value in fields_to_update.items():
            if field in {"created_at", "updated_at"} and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    value = datetime.now(timezone.utc)

            setattr(appointment, field, value)

        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)

        self._logger.info(
            f"Appointment fields updated for {appointment.id}: {list(fields_to_update.keys())}"
        )
        return appointment

    @handle_exceptions(
        default_exception=InternalServerError,
        message="An unexpected database error occurred.",
    )
    async def delete(self, db: AsyncSession, *, obj_id: uuid.UUID) -> None:
        """Delete an appointment (Test Only)"""
        statement = delete(self.model).where(self.model.id == obj_id)
        await db.execute(statement)
        await db.commit()
        self._logger.info(f"Appointment hard deleted: {obj_id}")
        return

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        conditions = []

        # --- 1. Status Filter (CRITICAL) ---
        if "status" in filters and filters["status"]:
            conditions.append(Appointment.status == filters["status"])

        # --- 2. Date Range Filters (CRITICAL) ---
        if "start_date" in filters and filters["start_date"]:
            conditions.append(Appointment.appointment_date >= filters["start_date"])

        if "end_date" in filters and filters["end_date"]:
            next_day = filters["end_date"] + timedelta(days=1)
            conditions.append(Appointment.appointment_date < next_day)

        # --- 3. Created At Range Filters (NEW) ---
        if "created_after" in filters and filters["created_after"]:
            conditions.append(Appointment.created_at >= filters["created_after"])

        if "created_before" in filters and filters["created_before"]:
            # Same logic: Include the full 'before' day
            next_day = filters["created_before"] + timedelta(days=1)
            conditions.append(Appointment.created_at < next_day)

        # --- 4. Updated At Range Filters (NEW) ---
        if "updated_after" in filters and filters["updated_after"]:
            conditions.append(Appointment.updated_at >= filters["updated_after"])

        if "updated_before" in filters and filters["updated_before"]:
            # Same logic: Include the full 'before' day
            next_day = filters["updated_before"] + timedelta(days=1)
            conditions.append(Appointment.updated_at < next_day)

        # --- 5. Strict Match Filters ---
        if "name" in filters and filters["name"]:
            conditions.append(Appointment.name == filters["name"])

        if "contact" in filters and filters["contact"]:
            conditions.append(Appointment.contact == filters["contact"])

        if "email" in filters and filters["email"]:
            conditions.append(Appointment.email == filters["email"])

        # --- 6. Fuzzy Search ---
        if "search" in filters and filters["search"]:
            search_term = f"%{filters['search']}%"
            conditions.append(
                or_(
                    Appointment.name.ilike(search_term),
                    Appointment.contact.ilike(search_term),
                    Appointment.email.ilike(search_term),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _apply_ordering(self, query, order_by: str, order_desc: bool):
        """Apply ordering to query."""
        order_column = getattr(self.model, order_by, self.model.created_at)
        if order_desc:
            return query.order_by(order_column.desc())
        else:
            return query.order_by(order_column.asc())


appointment_repository = AppointmentRepository()
