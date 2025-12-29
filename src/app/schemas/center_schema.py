import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)
from app.core.exceptions import ValidationError


class CenterBase(BaseModel):
    """"""