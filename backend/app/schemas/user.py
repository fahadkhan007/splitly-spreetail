# app/schemas/user.py
#
# UserOut is the shape of user data we send back to the frontend.
# It deliberately excludes password_hash and other sensitive fields.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    # Allow this schema to be created directly from a SQLAlchemy User object
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    is_verified: bool
    status: str         # 'ACTIVE', 'PENDING', or 'INACTIVE'
    avatar_url: str | None
    created_at: datetime
