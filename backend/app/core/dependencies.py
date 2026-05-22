import logging
import secrets
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

from app.core.redis_manager import redis_manager
from app.models.user import User
from app.services.auth_service import auth_service


logger = logging.getLogger(__name__)

async def issue_session(response: Response, user: User) -> str:
    """
    Create a session token, persist it in Redis, and attach the cookie
    """
    token = secrets.token_urlsafe(settings.SESSION_TOKEN_BYTES)
    await redis_manager.create_session(
        token = token,
        user_id = str(user.id),
        ttl = settings.SESSION_TTL_SECONDS,
    )
    response.set_cookie(
        key = settings.SESSION_COOKIE_NAME,
        value = token,
        max_age = settings.SESSION_TTL_SECONDS,
        httponly = True,
        secure = True, # Change to work with .env
        samesite = "lax",
        path = "/",
    )
    return token