from sqlalchemy import Column, Integer, String, Text, DateTime, func
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


class QuickRef(Base):
    __tablename__ = "quickref"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    icon = Column(String(32), default="📌")
    items = Column(Text, default="[]")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
