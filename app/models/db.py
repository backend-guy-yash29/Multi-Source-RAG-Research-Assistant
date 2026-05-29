import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship

# Default trial budget for an anonymous guest, in tokens.
GUEST_TOKEN_LIMIT = 10_000


# One Base for the whole project — every model below inherits from it,
# so they all share a single metadata registry.
class Base(DeclarativeBase):
    pass


def _utcnow():
    """Timezone-aware UTC timestamp, evaluated fresh at each insert."""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(255), unique=True, nullable=True, index=True)
    name            = Column(String(100))
    hashed_password = Column(String(255), nullable=True)

    is_guest        = Column(Boolean, nullable=False, default=True)
    tokens_used     = Column(Integer, nullable=False, default=0)
    token_limit     = Column(Integer, nullable=False, default=GUEST_TOKEN_LIMIT)

    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    sources  = relationship("Source",  back_populates="user", cascade="all, delete")
    sessions = relationship("Session", back_populates="user", cascade="all, delete")

    @property
    def tokens_remaining(self) -> int:
        return max(self.token_limit - self.tokens_used, 0)

    @property
    def quota_exceeded(self) -> bool:
        return self.tokens_used >= self.token_limit


class Source(Base):
    __tablename__ = "sources"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type       = Column(String(20), nullable=False)   # 'url' | 'pdf' | 'notion'
    location   = Column(Text, nullable=False)          # URL, S3 key, or Notion page ID
    status     = Column(String(20), nullable=False, default="pending")  # pending | ready | failed
    title      = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Chunks live exclusively in Qdrant — no chunk table in Postgres.
    # On source deletion, Qdrant points are removed by filtering on source_id.
    user = relationship("User", back_populates="sources")


class Session(Base):
    __tablename__ = "sessions"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    source_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    user     = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete")


class Message(Base):
    __tablename__ = "messages"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    role       = Column(String(20), nullable=False)   # 'user' | 'assistant'
    content    = Column(Text, nullable=False)
    citations  = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    session = relationship("Session", back_populates="messages")