"""
scripts/seed_demo.py
─────────────────────────────────────────────────────────────────────
Creates 7 demo users + a "Testing Group" for the CSV import demo.

Run from the backend/ directory:
    uv run python scripts/seed_demo.py

What it creates
───────────────
Users (all password = "12345", is_verified = True):
  1. Fahad    fahadkhanf715@gmail.com   → GROUP ADMIN
  2. Aisha    aisha@splitly.demo
  3. Rohan    rohan@splitly.demo
  4. Priya    priya@splitly.demo
  5. Meera    meera@splitly.demo        → left_at = 31 Mar 2026
  6. Dev      dev@splitly.demo
  7. Sam      sam@splitly.demo          → joined_at = 8 Apr 2026

Group:  "Testing Group"  (base_currency = INR)

The script is idempotent — safe to run multiple times.
"""

import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ── make sure app/ is importable ─────────────────────────────────
sys.path.insert(0, ".")

from app.config import settings
from app.core.security import hash_password
from app.database import Base
from app.models import *  # register all models with Base
from app.models.group import Group, GroupStatus
from app.models.group_member import GroupMember, MemberRole
from app.models.user import User


# ── DEMO USERS ────────────────────────────────────────────────────
DEMO_USERS = [
    # (display_name, email, joined_at, left_at, role)
    (
        "Fahad",
        "fahadkhanf715@gmail.com",
        datetime(2026, 2, 1, tzinfo=timezone.utc),
        None,
        MemberRole.ADMIN,
    ),
    (
        "Aisha",
        "aisha@splitly.demo",
        datetime(2026, 2, 1, tzinfo=timezone.utc),
        None,
        MemberRole.MEMBER,
    ),
    (
        "Rohan",
        "rohan@splitly.demo",
        datetime(2026, 2, 1, tzinfo=timezone.utc),
        None,
        MemberRole.MEMBER,
    ),
    (
        "Priya",
        "priya@splitly.demo",
        datetime(2026, 2, 1, tzinfo=timezone.utc),
        None,
        MemberRole.MEMBER,
    ),
    (
        "Meera",
        "meera@splitly.demo",
        datetime(2026, 2, 1, tzinfo=timezone.utc),
        datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc),  # moved out end of March
        MemberRole.MEMBER,
    ),
    (
        "Dev",
        "dev@splitly.demo",
        datetime(2026, 2, 1, tzinfo=timezone.utc),
        None,
        MemberRole.MEMBER,
    ),
    (
        "Sam",
        "sam@splitly.demo",
        datetime(2026, 4, 8, tzinfo=timezone.utc),  # moved in mid-April
        None,
        MemberRole.MEMBER,
    ),
]

PASSWORD = "12345"
GROUP_NAME = "Testing Group"


async def seed():
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        password_hash = hash_password(PASSWORD)

        # ── 1. CREATE / FETCH USERS ───────────────────────────────
        user_objects: dict[str, User] = {}  # display_name → User

        for display_name, email, joined_at, left_at, role in DEMO_USERS:
            existing = (await db.execute(
                select(User).where(User.email == email)
            )).scalar_one_or_none()

            if existing:
                print(f"  [SKIP] User '{display_name}' ({email}) already exists")
                user_objects[display_name] = existing
            else:
                user = User(
                    email=email,
                    display_name=display_name,
                    password_hash=password_hash,
                    is_verified=True,           # skip email verification for demo
                )
                db.add(user)
                await db.flush()
                print(f"  [CREATE] User '{display_name}' ({email})")
                user_objects[display_name] = user

        # ── 2. CREATE / FETCH GROUP ───────────────────────────────
        fahad = user_objects["Fahad"]

        existing_group = (await db.execute(
            select(Group).where(Group.name == GROUP_NAME)
        )).scalar_one_or_none()

        if existing_group:
            print(f"  [SKIP] Group '{GROUP_NAME}' already exists")
            group = existing_group
        else:
            group = Group(
                name=GROUP_NAME,
                description="Demo group for the shared expenses assignment",
                base_currency="INR",
                currency_locked=False,
                status=GroupStatus.ACTIVE,
                created_by_user_id=fahad.id,
            )
            db.add(group)
            await db.flush()
            print(f"  [CREATE] Group '{GROUP_NAME}'")

        # ── 3. ADD MEMBERS ────────────────────────────────────────
        for display_name, email, joined_at, left_at, role in DEMO_USERS:
            user = user_objects[display_name]

            existing_membership = (await db.execute(
                select(GroupMember).where(
                    GroupMember.group_id == group.id,
                    GroupMember.user_id == user.id,
                )
            )).scalar_one_or_none()

            if existing_membership:
                print(f"  [SKIP] '{display_name}' already a member")
                # Still update left_at if needed
                if left_at and existing_membership.left_at is None:
                    existing_membership.left_at = left_at
                    print(f"  [UPDATE] Set left_at for '{display_name}'")
            else:
                membership = GroupMember(
                    group_id=group.id,
                    user_id=user.id,
                    role=role,
                    joined_at=joined_at,
                    left_at=left_at,
                )
                db.add(membership)
                status = f"(left {left_at.date()})" if left_at else "(active)"
                print(f"  [CREATE] Added '{display_name}' as {role.value} {status}")

        await db.commit()

    await engine.dispose()
    print()
    print("Done! All data seeded successfully.")
    print(f"Group:    '{GROUP_NAME}' (base currency: INR)")
    print(f"Login:    fahadkhanf715@gmail.com / {PASSWORD}")
    print(f"Members:  Aisha, Rohan, Priya, Dev, Sam (active) + Meera (left 31 Mar 2026)")
    print()
    print("Next: upload 'Expenses Export.csv' via POST /groups/{group_id}/import")


if __name__ == "__main__":
    asyncio.run(seed())
