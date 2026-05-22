import uuid
from sqlalchemy import ForeignKey, LargeBinary, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # WebAuthn credential ID (from authenticator)
    credential_id: Mapped[bytes] = mapped_column(
        LargeBinary,
        unique=True,
        index=True,
        nullable=False,
    )

    # Public key for signature verification
    public_key: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    # Clone detection counter (VERY IMPORTANT)
    sign_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Link to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    last_used_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user = relationship("User", backref="credentials")