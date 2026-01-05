import logging
from typing import Optional, Dict, Any
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timezone
from app.crud.user_crud import user_repository
from app.crud.appointment_crud import appointment_repository
from app.schemas.appointment_schema import (
    CreatePublicAppointment,
    CreateAdminAppointment,
    ConfirmAppointment,
    RescheduleAppointment,
    CancelAppointment,
    AppointmentListResponse,
)
from app.models.user_model import User
from app.models.appointment_model import Appointment, AppointmentStatus
from app.core.exception_utils import raise_for_status
from app.core.exceptions import (
    ResourceNotFound,
    BadRequestException,
    ValidationError,
)

logger = logging.getLogger(__name__)


class AppointmentService:
    """Handles all appointment-related business logic."""

    def __init__(self):
        """
        Initializes the AppointmentService.
        This version has no arguments, making it easy for FastAPI to use,
        while still allowing for dependency injection during tests.
        """
        self.appointment_repository = appointment_repository
        self.user_repository = user_repository
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def get_appointment_by_id(
        self, db: AsyncSession, *, appointment_id: uuid.UUID, current_user: User
    ) -> Optional[Appointment]:
        """Fetch appointment by its ID"""

        appointment = await self.appointment_repository.get(
            db=db, obj_id=appointment_id
        )
        raise_for_status(
            condition=(appointment is None),
            exception=ResourceNotFound,
            detail=f"Appointment with Id {appointment_id} not Found.",
            resource_type="Appointment",
        )

        self._logger.debug(
            f"Appointment {appointment_id} retrieved by user {current_user.id}"
        )
        return appointment

    async def get_all_appointments(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> AppointmentListResponse:

        # Input validation
        if skip < 0:
            raise ValidationError("Skip parameter must be non-negative")
        if limit <= 0 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")

        # Delegate fetching to the repository
        appointments, total = await self.appointment_repository.get_all(
            db=db,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=order_by,
            order_desc=order_desc,
        )

        # Calculate pagination info
        page = (skip // limit) + 1
        total_pages = (total + limit - 1) // limit  # Ceiling division

        # Construct the response schema
        response = AppointmentListResponse(
            items=appointments, total=total, page=page, pages=total_pages, size=limit
        )

        return response

    async def create_pending_request(
        self, db: AsyncSession, *, appointment_dict: CreatePublicAppointment
    ) -> Appointment:
        """Create a pending request"""

        appointment_dict = appointment_dict.model_dump(mode="json")
        appointment_dict["status"] = AppointmentStatus.PENDING
        appointment_dict["created_at"] = datetime.now(timezone.utc)
        appointment_dict["updated_at"] = datetime.now(timezone.utc)

        appointment_to_create = Appointment(**appointment_dict)

        new_appointment = await self.appointment_repository.create(
            db=db, db_obj=appointment_to_create
        )
        self._logger.info(f"New Appointment created: {new_appointment.name}")

        return new_appointment

    async def schedule_appointment(
        self,
        *,
        db: AsyncSession,
        appointment_dict: CreateAdminAppointment,
        current_user: User,
    ) -> Appointment:
        """Schedule an appointment"""

        appointment_dict = appointment_dict.model_dump(mode="json")
        appointment_dict["status"] = AppointmentStatus.UPCOMING
        appointment_dict["created_at"] = datetime.now(timezone.utc)
        appointment_dict["updated_at"] = datetime.now(timezone.utc)

        appointment_to_create = Appointment(**appointment_dict)

        new_appointment = await self.appointment_repository.create(
            db=db, db_obj=appointment_to_create
        )
        self._logger.info(
            f"New Appointment created: {new_appointment.name}, created by: {current_user.id}"
        )

        return new_appointment

    async def reschedule_appointment(
        self,
        db: AsyncSession,
        *,
        appointment_id: uuid.UUID,
        current_user: User,
        appointment_data: RescheduleAppointment,
    ) -> Appointment:
        """Reschedule an appointment"""

        appointment = await self.get_appointment_by_id(
            db=db, current_user=current_user, appointment_id=appointment_id
        )

        update_dict = appointment_data.model_dump(
            exclude_unset=True, exclude_none=True, mode="json"
        )

        # Remove timestamp fields that should not be manually updated
        for ts_field in {"created_at", "updated_at"}:
            update_dict.pop(ts_field, None)

        updated_appointment = await self.appointment_repository.update(
            db=db,
            appointment=appointment,
            fields_to_update=update_dict,
        )

        self._logger.info(
            f"Appointment {appointment} updated by {current_user.id}",
            extra={
                "updated_appointment_id": appointment_id,
                "updater_id": current_user.id,
                "updated_fields": list(update_dict.keys()),
            },
        )
        return updated_appointment

    async def confirm_appointment(
        self,
        db: AsyncSession,
        *,
        appointment_id: uuid.UUID,
        current_user: User,
        appointment_data: ConfirmAppointment,
    ) -> Appointment:

        appointment = await self.get_appointment_by_id(
            db=db, current_user=current_user, appointment_id=appointment_id
        )
        raise_for_status(
            condition=(appointment.status != AppointmentStatus.PENDING),
            exception=BadRequestException,
            detail=f"Cannot confirm appointment {appointment_id}. Current status: {appointment.status}",
        )
        update_dict = appointment_data.model_dump(
            exclude_unset=True, exclude_none=True, mode="json"
        )

        update_dict["status"] = AppointmentStatus.UPCOMING

        # Remove timestamp fields that should not be manually updated
        for ts_field in {"created_at", "updated_at"}:
            update_dict.pop(ts_field, None)

        updated_appointment = await self.appointment_repository.update(
            db=db,
            appointment=appointment,
            fields_to_update=update_dict,
        )

        self._logger.info(
            f"Appointment {appointment} updated by {current_user.id}",
            extra={
                "updated_appointment_id": appointment_id,
                "updater_id": current_user.id,
                "updated_fields": list(update_dict.keys()),
            },
        )
        return updated_appointment

    async def cancel_appointment(
        self,
        db: AsyncSession,
        *,
        appointment_id: uuid.UUID,
        current_user: User,
        appointment_data: CancelAppointment,
    ) -> Appointment:

        appointment = await self.get_appointment_by_id(
            db=db, current_user=current_user, appointment_id=appointment_id
        )
        raise_for_status(
            condition=(appointment.status != AppointmentStatus.UPCOMING),
            exception=BadRequestException,
            detail=f"Cannot cancel appointment {appointment_id}. Current status: {appointment.status}",
        )

        update_dict = appointment_data.model_dump(
            exclude_unset=True, exclude_none=True, mode="json"
        )

        update_dict["status"] = AppointmentStatus.CANCELLED

        # Remove timestamp fields that should not be manually updated
        for ts_field in {"created_at", "updated_at"}:
            update_dict.pop(ts_field, None)

        updated_appointment = await self.appointment_repository.update(
            db=db,
            appointment=appointment,
            fields_to_update=update_dict,
        )

        self._logger.info(
            f"Appointment {appointment} updated by {current_user.id}",
            extra={
                "updated_appointment_id": appointment_id,
                "updater_id": current_user.id,
                "updated_fields": list(update_dict.keys()),
            },
        )
        return updated_appointment

    async def reject_appointment(
        self,
        db: AsyncSession,
        *,
        appointment_id: uuid.UUID,
        current_user: User,
        appointment_data: CancelAppointment,
    ) -> Appointment:

        appointment = await self.get_appointment_by_id(
            db=db, current_user=current_user, appointment_id=appointment_id
        )
        raise_for_status(
            condition=(appointment.status != AppointmentStatus.UPCOMING),
            exception=BadRequestException,
            detail=f"Cannot reject appointment {appointment_id}. Current status: {appointment.status}",
        )

        update_dict = appointment_data.model_dump(
            exclude_unset=True, exclude_none=True, mode="json"
        )

        update_dict["status"] = AppointmentStatus.REJECTED

        # Remove timestamp fields that should not be manually updated
        for ts_field in {"created_at", "updated_at"}:
            update_dict.pop(ts_field, None)

        updated_appointment = await self.appointment_repository.update(
            db=db,
            appointment=appointment,
            fields_to_update=update_dict,
        )

        self._logger.info(
            f"Appointment {appointment} updated by {current_user.id}",
            extra={
                "updated_appointment_id": appointment_id,
                "updater_id": current_user.id,
                "updated_fields": list(update_dict.keys()),
            },
        )
        return updated_appointment

    async def delete_appointment(
        self,
        db: AsyncSession,
        *,
        appointment_id_to_delete: uuid.UUID,
        current_user: User,
    ) -> Dict[str, str]:
        """Delete an appointment"""

        appointment_to_delete = await self.appointment_repository.get(
            db=db, obj_id=appointment_id_to_delete
        )
        raise_for_status(
            condition=(appointment_to_delete is None),
            exception=ResourceNotFound,
            detail=f"Appointment with ID {appointment_id_to_delete} not Found.",
            resource_type="Appointment",
        )

        await self.appointment_repository.delete(db=db, obj_id=appointment_id_to_delete)

        self._logger.warning(
            f"Appointment {appointment_id_to_delete} permanently deleted by {current_user.id}",
            extra={
                "deleted_appointment_id": appointment_id_to_delete,
                "deleter_id": current_user.id,
                "deleted_appointment_name": appointment_to_delete.name,
            },
        )

        return {"message": "Appointment deleted successfully"}


appointment_service = AppointmentService()
