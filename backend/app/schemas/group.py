# app/schemas/group.py
#
# Request and response shapes for group endpoints.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.member import MemberOut


class GroupCreate(BaseModel):
    """Body for POST /groups"""
    name: str
    description: str | None = None
    base_currency: str  # e.g. 'INR', 'USD', 'EUR'

    @field_validator("name")
    def name_not_blank(cls, value):
        if not value.strip():
            raise ValueError("Group name cannot be empty")
        return value.strip()

    @field_validator("base_currency")
    def currency_must_be_3_letters(cls, value):
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code like INR or USD")
        return value.upper()


class GroupUpdate(BaseModel):
    """Body for PATCH /groups/{group_id} — all fields optional"""
    name: str | None = None
    description: str | None = None


class GroupOut(BaseModel):
    """Full group detail — returned for GET /groups/{group_id}"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    base_currency: str
    currency_locked: bool
    status: str
    my_role: str                # The current user's role: 'ADMIN' or 'MEMBER'
    members: list[MemberOut]    # All active members
    created_at: datetime


class GroupListItem(BaseModel):
    """Compact group summary — returned in GET /groups list"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    base_currency: str
    status: str
    my_role: str
    member_count: int
