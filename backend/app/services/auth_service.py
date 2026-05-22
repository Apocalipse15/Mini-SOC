from http.client import HTTPException
import json
import json
import os
import secrets
from app.core.redis_manager import redis_manager
from app.core.passkey.passkey_manager import passkey_manager
from app.config import settings
from app.core.encoding import b64url_encode
import base64
from app.config import WEBAUTHN_USER_HANDLE_BYTES
from sqlmodel import select
from app.models.user import User
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.schemas.auth import RegistrationCompleteRequest

logger = logging.getLogger(__name__)

async def get_user_by_username(
    self,
    session: AsyncSession,
    username: str,
) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()

class AuthService:
    async def register_begin(self, session, username: str, display_name: str):
        result = await session.execute(
            select(User).where(User.username == username)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User already exists")

        from app.config import WEBAUTHN_USER_HANDLE_BYTES
        user_handle = secrets.token_bytes(WEBAUTHN_USER_HANDLE_BYTES)

        options_response = passkey_manager.generate_registration_options(
            user_id = user_handle,
            username = username,
            display_name = display_name,
            exclude_credentials = [],
        )

        await redis_manager.set_registration_context(
            username = username,
            challenge = options_response.challenge,
            user_handle = user_handle,
            display_name = display_name,
        )

        logger.info("Started registration for user: %s", username)
        return options_response.options

    async def complete_registration(self, session: AsyncSession, body: RegistrationCompleteRequest):
        result = await session.execute(
            select(User).where(User.username == body.username)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User already exists")

        context = await redis_manager.get_and_delete_registration_context(body.username)

        if not context:
            raise ValueError("Registration context not found or expired")

        expected_challenge = base64.b64decode(context["challenge"])

        verified = passkey_manager.verify_registration_response(
            response=body.credential,
            expected_challenge=expected_challenge,
        )

        user = User(
            username=body.username,
            display_name=context["display_name"],
            webauthn_user_handle=base64.b64decode(context["user_handle"]),
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.info("Completed registration for user: %s", body.username)
        return user

    





auth_service = AuthService()