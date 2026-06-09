from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, func, Index
from database import Base


class PvPGuide(Base):
    __tablename__ = "pvp_guides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    content = Column(Text, default="")
    icon = Column(String(32), default="⚔️")
    image_url = Column(String(512), default="")
    category = Column(String(64), default="general")
    tags = Column(Text, default="[]")
    badge = Column(String(16), default="")
    video_url = Column(String(512), default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_pvp_category", "category"),
        Index("ix_pvp_sort_order", "sort_order"),
        Index("ix_pvp_badge", "badge"),
    )


class PvEGuide(Base):
    __tablename__ = "pve_guides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    content = Column(Text, default="")
    icon = Column(String(32), default="🗺️")
    image_url = Column(String(512), default="")
    category = Column(String(64), default="map")
    tags = Column(Text, default="[]")
    badge = Column(String(16), default="")
    video_url = Column(String(512), default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_pve_category", "category"),
        Index("ix_pve_sort_order", "sort_order"),
    )


class CodeItem(Base):
    __tablename__ = "codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), nullable=False)
    title = Column(String(64), default="")
    description = Column(Text, default="")
    reward = Column(Text, default="")
    expiry = Column(String(64), default="长期有效")
    is_active = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_codes_is_active", "is_active"),
        Index("ix_codes_sort_order", "sort_order"),
    )


class QuickRef(Base):
    __tablename__ = "quickref"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    icon = Column(String(32), default="📌")
    items = Column(Text, default="[]")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_quickref_sort_order", "sort_order"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(64), nullable=False)
    table_name = Column(String(64), default="")
    item_id = Column(Integer, nullable=True)
    detail = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_audit_created_at", "created_at"),
    )
