import os
import base64
import secrets
from app.config import settings

from app.config import settings
import logging

from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from webauthn.helpers import (
    bytes_to_base64url,
    options_to_json_dict,
)

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)

from app.schemas.auth import RegistrationOptionsResponse, VerifiedRegistration

logger = logging.getLogger(__name__)

class PasskeyManager:
    def __init__(self):
        self.rp_id = settings.RP_ID
        self.rp_name = settings.RP_NAME
        self.rp_origin = settings.RP_ORIGIN

    def generate_registration_options(self,
        user_id: bytes,
        username: str,
        display_name: str,
        exclude_credentials: list[bytes]):

            challenge = secrets.token_bytes(settings.WEBAUTHN_CHALLENGE_BYTES)

            exclude_creds = []
            if exclude_credentials:
                exclude_creds = [
                    PublicKeyCredentialDescriptor(id = cred_id)
                    for cred_id in exclude_credentials
                ]

            options = generate_registration_options(
            rp_id = self.rp_id,
            rp_name = self.rp_name,
            user_id = user_id,
            user_name = username,
            user_display_name = display_name,
            challenge = challenge,
            attestation = AttestationConveyancePreference.NONE,
            authenticator_selection = AuthenticatorSelectionCriteria(
                resident_key = ResidentKeyRequirement.REQUIRED,
                user_verification = UserVerificationRequirement.REQUIRED,
                ),
            exclude_credentials = exclude_creds,
            )

            logger.debug("Generated registration options for user %s", username)

            return RegistrationOptionsResponse(
                options = options_to_json_dict(options),
                challenge = challenge,
            )

    def verify_registration_response(self, response: dict[str, any], expected_challenge: bytes):
        try:
            verification = verify_registration_response(
                credential=response,
                expected_challenge=expected_challenge,
                expected_rp_id=self.rp_id,
                expected_origin=self.rp_origin,
                require_user_verification=True,
            )

        except Exception as e:
            logger.error("WebAuthn registration failed: %s", str(e))
            raise ValueError("Registration verification failed") from e

        return VerifiedRegistration(
            credential_id=verification.credential_id,
            credential_public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            aaguid=verification.aaguid,
            attestation_object=verification.attestation_object,
            credential_type=verification.credential_type,
            user_verified=verification.user_verified,
            attestation_format=verification.fmt,
            credential_device_type=verification.credential_device_type,

            # SAFE FALLBACKS ↓↓↓
            credential_backed_up=bool(getattr(verification, "credential_backed_up", False)),
            backup_eligible=bool(getattr(verification, "credential_backup_eligible", False)),
            backup_state=bool(getattr(verification, "credential_backed_up", False)),
        )


passkey_manager = PasskeyManager()