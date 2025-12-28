from sqlalchemy import Column, String, DateTime, Text, ARRAY, Boolean
from sqlalchemy.sql import func
from app.database import Base
from .base import TenantMixin


class Paper(TenantMixin, Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True)  # arXiv ID
    title = Column(String, nullable=False)
    authors = Column(ARRAY(String))
    summary = Column(Text)
    published_date = Column(DateTime)
    pdf_url = Column(String)
    status = Column(String, default="new")
    is_bookmarked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
