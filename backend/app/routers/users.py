# app/routers/users.py
#
# Routes for the currently logged-in user's own profile.
#
# Routes:
#   GET /users/me  — returns the logged-in user's profile

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the currently logged-in user.
    Requires a valid access token in the Authorization header.
    """
    return UserOut.model_validate(current_user)
