from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
from .base import TenantMixin
import uuid


class Post(TenantMixin, Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(String, ForeignKey("papers.id"))
    slug = Column(String, unique=True, index=True, nullable=True)
    title = Column(String)
    content_markdown = Column(Text)
    language = Column(String, default="en")
    status = Column(String, default="draft")
    published_at = Column(DateTime)
    substack_embed_code = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
