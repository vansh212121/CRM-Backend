# app/services/center_service.py
"""
Center service module.

This module provides the business logic layer for center operations,
handling authorization, validation, and orchestrating repository calls.
"""
import logging
from typing import Optional, Dict, Any
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timezone
from app.crud.user_crud import user_repository
from app.crud.center_crud import center_repository
from app.schemas.center_schema import (
    CenterCreate,
    CenterListResponse,
    CenterUpdate,
)
from app.models.user_model import User
from app.models.center_model import Center

from app.core.exception_utils import raise_for_status
from app.core.exceptions import (
    ResourceNotFound,
    ResourceAlreadyExists,
    ValidationError,
)

logger = logging.getLogger(__name__)


class CenterService:
    """Handles all center-related business logic."""

    def __init__(self):
        """
        Initializes the CenterService.
        This version has no arguments, making it easy for FastAPI to use,
        while still allowing for dependency injection during tests.
        """
        self.center_repository = center_repository
        self.user_repository = user_repository
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def get_center_by_id(
        self, db: AsyncSession, *, center_id: uuid.UUID, current_user: User
    ) -> Optional[Center]:
        """Get center by it's ID"""

        center_model = await self.center_repository.get(db=db, obj_id=center_id)
        raise_for_status(
            condition=(center_model is None),
            exception=ResourceNotFound,
            detail=f"Center with id {center_id} not found.",
            resource_type="Center",
        )

        self._logger.debug(f"Center {center_id} retrieved by user {current_user.id}")
        return center_model

    async def get_all_centers(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> CenterListResponse:

        # Input validation
        if skip < 0:
            raise ValidationError("Skip parameter must be non-negative")
        if limit <= 0 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")

        # Delegate fetching to the repository
        tasks, total = await self.center_repository.get_all(
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
        response = CenterListResponse(
            items=tasks, total=total, page=page, pages=total_pages, size=limit
        )

        return response

    async def create_center(
        self, db: AsyncSession, *, center_dict: CenterCreate, current_user: User
    ) -> Center:
        """Handles the business logic of creating a new center."""

        existing_center = await self.center_repository.get_by_name(
            db=db, name=center_dict.name
        )
        raise_for_status(
            condition=(existing_center is not None),
            exception=ResourceAlreadyExists,
            detail=f"Center with name {center_dict.name} already exists",
            resource_type="Center",
        )

        center_dict = center_dict.model_dump(mode="json")
        center_dict["user_id"] = current_user.id
        center_dict["created_at"] = datetime.now(timezone.utc)
        center_dict["updated_at"] = datetime.now(timezone.utc)

        center_to_create = Center(**center_dict)

        # 3. Delegate creation to the repository
        new_center = await self.center_repository.create(db=db, db_obj=center_to_create)
        self._logger.info(f"New Center created: {new_center.name}")

        return new_center

    async def update_center(
        self,
        db: AsyncSession,
        *,
        center_id_to_update: uuid.UUID,
        center_data: CenterUpdate,
        current_user: User,
    ):
        """Updates a center after performing necessary authorization checks."""

        center_to_update = await self.center_repository.get(
            db=db, obj_id=center_id_to_update
        )
        raise_for_status(
            condition=(center_to_update is None),
            exception=ResourceNotFound,
            detail=f"Center with id {center_id_to_update} not Found",
            resource_type="Center",
        )

        update_dict = center_data.model_dump(
            exclude_unset=True, exclude_none=True, mode="json"
        )

        # Remove timestamp fields that should not be manually updated
        for ts_field in {"created_at", "updated_at"}:
            update_dict.pop(ts_field, None)

        updated_center = await self.center_repository.update(
            db=db,
            center=center_to_update,
            fields_to_update=update_dict,
        )

        self._logger.info(
            f"Center {center_id_to_update} updated by {current_user.id}",
            extra={
                "updated_center_id": center_id_to_update,
                "updater_id": current_user.id,
                "updated_fields": list(update_dict.keys()),
            },
        )
        return updated_center

    async def delete_center(
        self, db: AsyncSession, *, center_id_to_delete: uuid.UUID, current_user: User
    ) -> Dict[str, str]:
        """Permanently deletes a task."""

        center_to_delete = await self.center_repository.get(
            db=db, obj_id=center_id_to_delete
        )
        raise_for_status(
            condition=(center_to_delete is None),
            exception=ResourceNotFound,
            detail=f"Center with id {center_id_to_delete} not found.",
            resource_type="Center",
        )

        await self.center_repository.delete(db=db, obj_id=center_id_to_delete)

        self._logger.warning(
            f"Center {center_id_to_delete} permanently deleted by {current_user.id}",
            extra={
                "deleted_center_id": center_id_to_delete,
                "deleter_id": current_user.id,
                "deleted_center_name": center_to_delete.name,
            },
        )


center_service = CenterService()
