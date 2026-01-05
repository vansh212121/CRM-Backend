import logging
import uuid
from typing import Dict
from fastapi import APIRouter, Depends, status, Query

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.schemas.appointment_schema import (
    CreatePublicAppointment,
    CreateAdminAppointment,
    ConfirmAppointment,
    RescheduleAppointment,
    CancelAppointment,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentSearchParams,
)
from app.models.user_model import User

from app.db.session import get_session
from app.utils.deps import (
    get_current_user,
    rate_limit_api,
    PaginationParams,
    get_pagination_params,
)
from app.services.appointment_service import appointment_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Appointment"],
    prefix=f"{settings.API_V1_STR}/appointments",
)


@router.get(
    "/",
    response_model=AppointmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all appointments",
    description="Get a paginated and filterable list of appointments.",
    dependencies=[
        Depends(rate_limit_api),
    ],
)
async def get_all_appointments(
    *,
    db: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    search_params: AppointmentSearchParams = Depends(AppointmentSearchParams),
    order_by: str = Query("created_at", description="Field to order by"),
    order_desc: bool = Query(True, description="Order descending"),
):
    """get paginated response of appointments"""

    return await appointment_service.get_all_appointments(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
        filters=search_params.model_dump(exclude_none=True),
        order_by=order_by,
        order_desc=order_desc,
    )


@router.get(
    "/{appointment_id}",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    summary="Get appointment details",
    description="Get profile information for the center",
    dependencies=[Depends(rate_limit_api)],
)
async def get_appointment_by_id(
    *,
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a center by it's ID"""

    return await appointment_service.get_appointment_by_id(
        appointment_id=appointment_id, db=db, current_user=current_user
    )


@router.post(
    "/pending",
    status_code=status.HTTP_201_CREATED,
    summary="Make a pending request",
    description="Make a pending request(Public only)",
    response_model=AppointmentResponse,
    dependencies=[Depends(rate_limit_api)],
)
async def create_pending_request(
    *,
    appointment_data: CreatePublicAppointment,
    db: AsyncSession = Depends(get_session),
):
    return await appointment_service.create_pending_request(
        db=db, appointment_dict=appointment_data
    )


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Make a pending request",
    description="Make a pending request(Public only)",
    response_model=AppointmentResponse,
    dependencies=[Depends(rate_limit_api)],
)
async def schedule_appointment(
    *,
    appointment_data: CreateAdminAppointment,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.schedule_appointment(
        db=db, current_user=current_user, appointment_dict=appointment_data
    )


@router.patch(
    "/{appointment_id}/reschedule",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    summary="reschedule appointment",
    description="reschedule appointment ",
    dependencies=[Depends(rate_limit_api)],
)
async def reschedule_appointment(
    *,
    appointment_id: uuid.UUID,
    appointment_data: RescheduleAppointment,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.reschedule_appointment(
        db=db,
        current_user=current_user,
        appointment_data=appointment_data,
        appointment_id=appointment_id,
    )


@router.patch(
    "/{appointment_id}/confirm",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    summary="change status",
    description="Change status to Confirm",
    dependencies=[Depends(rate_limit_api)],
)
async def confirm_appointment(
    *,
    appointment_id: uuid.UUID,
    appointment_data: ConfirmAppointment,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.confirm_appointment(
        db=db,
        current_user=current_user,
        appointment_data=appointment_data,
        appointment_id=appointment_id,
    )


@router.patch(
    "/{appointment_id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    summary="change status",
    description="Change status to Cancel",
    dependencies=[Depends(rate_limit_api)],
)
async def cancel_appointment(
    *,
    appointment_id: uuid.UUID,
    appointment_data: CancelAppointment,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.cancel_appointment(
        db=db,
        current_user=current_user,
        appointment_data=appointment_data,
        appointment_id=appointment_id,
    )


@router.patch(
    "/{appointment_id}/reject",
    status_code=status.HTTP_200_OK,
    response_model=AppointmentResponse,
    summary="change status",
    description="Change status to Reject",
    dependencies=[Depends(rate_limit_api)],
)
async def reject_appointment(
    *,
    appointment_id: uuid.UUID,
    appointment_data: CancelAppointment,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await appointment_service.reject_appointment(
        db=db,
        current_user=current_user,
        appointment_data=appointment_data,
        appointment_id=appointment_id,
    )


@router.delete(
    "/{appointment_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete a Appointment",
    description="Delete a Appointment for authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def delete_appointment(
    appointment_id: uuid.UUID,
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):

    await appointment_service.delete_appointment(
        db=db, appointment_id_to_delete=appointment_id, current_user=current_user
    )

    return {"message": "Appointment deleted successfully."}
