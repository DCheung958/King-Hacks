try:
    from sqlalchemy import Table, Column, String, DateTime, Text, ForeignKey, Index
    from sqlalchemy.dialects.postgresql import UUID
    from datetime import datetime
    from database import metadata
    
    if metadata is None:
        raise ImportError("Database not configured")
    
    users = Table(
        "users",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("email", String(255), unique=True, nullable=False, index=True),
        Column("name", String(255), nullable=True),
        Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
    )
    
    voice_samples = Table(
        "voice_samples",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        Column("filename", String(255), nullable=False),
        Column("uploaded_at", DateTime, default=datetime.utcnow, nullable=False),
        Index("idx_voice_samples_user_id", "user_id"),
        Index("idx_voice_samples_uploaded_at", "uploaded_at"),
    )
    
    conversations = Table(
        "conversations",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_created_at", "created_at"),
    )
    
    messages = Table(
        "messages",
        metadata,
        Column("id", UUID(as_uuid=True), primary_key=True),
        Column("conversation_id", UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        Column("role", String(20), nullable=False),  # "user" or "assistant"
        Column("text", Text, nullable=False),
        Column("emotion", String(50), nullable=True),
        Column("timestamp", DateTime, default=datetime.utcnow, nullable=False),
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_timestamp", "timestamp"),
        Index("idx_messages_role", "role"),
    )
except (ImportError, TypeError, AttributeError):
    # Database packages not available - define as None
    users = None
    voice_samples = None
    conversations = None
    messages = None
