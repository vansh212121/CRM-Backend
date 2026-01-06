import logging
import uuid
from typing import Dict
from fastapi import APIRouter, Depends, status, Query

from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.schemas.center_schema import (
    CenterResponse,
    CenterSearchParams,
    CenterListResponse,
    CenterCreate,
    CenterUpdate,
)
from app.models.user_model import User
from app.db.session import get_session
from app.utils.deps import (
    get_current_user,
    rate_limit_api,
    PaginationParams,
    get_pagination_params,
)
from app.services.center_service import center_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Center"],
    prefix=f"{settings.API_V1_STR}/centers",
)


@router.get(
    "/",
    response_model=CenterListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all centers",
    description="Get a paginated and filterable list of centers.",
    dependencies=[
        Depends(rate_limit_api),
    ],
)
async def get_all_centers(
    *,
    db: AsyncSession = Depends(get_session),
    pagination: PaginationParams = Depends(get_pagination_params),
    search_params: CenterSearchParams = Depends(CenterSearchParams),
    order_by: str = Query("created_at", description="Field to order by"),
    order_desc: bool = Query(True, description="Order descending"),
):
    """get paginated response of current_user bills"""

    return await center_service.get_all_centers(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
        filters=search_params.model_dump(exclude_none=True),
        order_by=order_by,
        order_desc=order_desc,
    )


@router.get(
    "/{center_id}",
    status_code=status.HTTP_200_OK,
    response_model=CenterResponse,
    summary="Get a center's profile",
    description="Get profile information for the center",
    dependencies=[Depends(rate_limit_api)],
)
async def get_center_by_id(
    *,
    center_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a center by it's ID"""

    return await center_service.get_center_by_id(
        center_id=center_id, db=db, current_user=current_user
    )


@router.post(
    "/",
    response_model=CenterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a center",
    description="Create a center for authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def create_center(
    *,
    center_data: CenterCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a center, only for authenticated user"""

    task = await center_service.create_center(
        db=db, current_user=current_user, center_dict=center_data
    )

    return task


@router.patch(
    "/{center_id}",
    response_model=CenterResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a center",
    description="Update a center for authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def update_center(
    center_id: uuid.UUID,
    *,
    center_data: CenterUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a center, only for authenticated user"""

    update_center = await center_service.update_center(
        db=db,
        center_id_to_update=center_id,
        center_data=center_data,
        current_user=current_user,
    )

    return update_center


@router.delete(
    "/{center_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete a center",
    description="Delete a center for authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def delete_center(
    center_id: uuid.UUID,
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a center, only for authenticated user"""

    await center_service.delete_center(
        db=db, center_id_to_delete=center_id, current_user=current_user
    )

    return {"message": "Center deleted successfully."}
