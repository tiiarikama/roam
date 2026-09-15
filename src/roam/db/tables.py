from sqlalchemy import MetaData, Table, Column, String, Text, Boolean, DateTime, ForeignKey, Index, CheckConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

# app tables, managed by Alembic
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

users = Table(
    "users",
    metadata,
    Column("id", UUID, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("email", String(320), nullable=False, unique=True),
    Column("display_name", String(80), nullable=False),
    Column("password_hash", Text, nullable=False),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

# refresh tokens are tracked server-side so logout can revoke them
refresh_tokens = Table(
    "refresh_tokens",
    metadata,
    Column("id", UUID, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("token_hash", String(64), nullable=False, unique=True),  # sha256 hex of the token
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Index("idx_refresh_tokens_user_id", "user_id"),
)

conversations = Table(
    "conversations",
    metadata,
    Column("id", UUID, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(120), nullable=False, server_default="New chat"),
    Column("last_park_codes", ARRAY(String(10)), nullable=False, server_default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Index("idx_conversations_user_updated", "user_id", "updated_at"),
)

messages = Table(
    "messages",
    metadata,
    Column("id", UUID, primary_key=True, server_default=text("gen_random_uuid()")),
    Column("conversation_id", UUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(16), nullable=False),
    Column("content", Text, nullable=False, server_default=""),
    Column("intent", String(32)),
    Column("park_codes", ARRAY(String(10)), nullable=False, server_default="{}"),
    Column("sources", JSONB, nullable=False, server_default="[]"),
    Column("weather", JSONB),
    Column("is_partial", Boolean, nullable=False, server_default=text("false")),  # true when the client disconnected mid-stream
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Index("idx_messages_conversation_created", "conversation_id", "created_at"),
    CheckConstraint("role IN ('user', 'assistant')", name="role"),
)
