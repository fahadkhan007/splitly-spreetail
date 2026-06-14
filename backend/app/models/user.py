# app/models/user.py
#
# The User table stores all registered users and pending members.
#
# PENDING users are people found in CSV imports who don't have an account yet.
# They can appear in expenses but cannot log in.

import enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"       # Normal registered user
    PENDING = "PENDING"     # Found in CSV import, no account yet
    INACTIVE = "INACTIVE"   # Deactivated (e.g. pending member admin removed)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Email is the unique login identifier (not display_name)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # The name shown in the UI — does not have to be unique
    display_name = Column(String(100), nullable=False)

    # Stored as a bcrypt hash. NULL for PENDING users (they have no password yet)
    password_hash = Column(String(255), nullable=True)

    # Must be True before the user can invite others or add expenses
    is_verified = Column(Boolean, nullable=False, default=False)

    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    # Optional profile picture URL
    avatar_url = Column(String(500), nullable=True)

    # Timestamps — set automatically by the database
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
