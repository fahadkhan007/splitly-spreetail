# app/schemas/member.py
#
# MemberOut is used inside group responses to show who is in a group.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    display_name: str
    email: str
    role: str           # 'ADMIN' or 'MEMBER'
    joined_at: datetime
    left_at: datetime | None   # None = still active in the group
