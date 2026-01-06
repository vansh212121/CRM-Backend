import logging
from typing import Dict
from fastapi import APIRouter, Depends, status, Query

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.schemas.user_schema import UserResponse, UserUpdate
from app.schemas.auth_schema import UserPasswordChange
from app.models.user_model import User
from app.db.session import get_session
from app.utils.deps import (
    get_current_user,
    rate_limit_api,
    rate_limit_auth,
)
from app.services.user_service import user_service
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["User"],
    prefix=f"{settings.API_V1_STR}/users",
)


# ------ Current User Operations ------
@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get profile information for the authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def get_my_profile(
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update profile information for the authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def update_my_profile(
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_data: UserUpdate,
):
    updated_user = await user_service.update_user(
        db=db,
        user_id_to_update=current_user.id,
        user_data=user_data,
        current_user=current_user,
    )

    return updated_user


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, str],
    summary="Delete current user profile",
    description="Delete profile for the authenticated user",
    dependencies=[Depends(rate_limit_auth)],
)
async def delete_my_account(
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a user account.

    - Users can deactivate their own account
    """
    await user_service.delete_user(
        db=db, user_id_to_delete=current_user.id, current_user=current_user
    )

    return {"message": "User deleted successfully"}


@router.post(
    "/change-password",
    response_model=Dict[str, str],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Change Current User's Password",
    description="Change Current User's Password",
    dependencies=[Depends(rate_limit_auth)],
)
async def change_my_password(
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    password_data: UserPasswordChange,
):
    """Change a logged-in User Password"""
    await auth_service.change_password(
        db=db, password_data=password_data, user=current_user
    )

    return {"message": "Password updated successfully"}
