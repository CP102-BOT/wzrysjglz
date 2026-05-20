import json
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


EXPLORATION_CATEGORIES = ["地图探索", "任务攻略", "资源收集", "隐藏要素", "BOSS攻略", "新手入门"]
PVP_CATEGORIES = ["角色技巧", "连招教学", "阵容搭配", "对战策略", "装备推荐", "进阶技巧"]
DIFFICULTY_LEVELS = ["入门", "进阶", "精通"]


class ExplorationGuide(Base):
    __tablename__ = "exploration_guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50), default="地图探索", index=True)
    tags: Mapped[str] = mapped_column(Text, default="[]")
    difficulty: Mapped[str] = mapped_column(String(20), default="入门")
    cover_image: Mapped[str] = mapped_column(String(500), default="")
    video_url: Mapped[str] = mapped_column(String(500), default="")
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_hot: Mapped[int] = mapped_column(Integer, default=0)
    is_new: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "tags": json.loads(self.tags) if self.tags else [],
            "difficulty": self.difficulty,
            "cover_image": self.cover_image,
            "video_url": self.video_url,
            "view_count": self.view_count,
            "is_hot": bool(self.is_hot),
            "is_new": bool(self.is_new),
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }


class PvpTip(Base):
    __tablename__ = "pvp_tips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(50), default="角色技巧", index=True)
    tags: Mapped[str] = mapped_column(Text, default="[]")
    difficulty: Mapped[str] = mapped_column(String(20), default="入门")
    cover_image: Mapped[str] = mapped_column(String(500), default="")
    video_url: Mapped[str] = mapped_column(String(500), default="")
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_hot: Mapped[int] = mapped_column(Integer, default=0)
    is_new: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "content": self.content,
            "category": self.category,
            "tags": json.loads(self.tags) if self.tags else [],
            "difficulty": self.difficulty,
            "cover_image": self.cover_image,
            "video_url": self.video_url,
            "view_count": self.view_count,
            "is_hot": bool(self.is_hot),
            "is_new": bool(self.is_new),
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
