import re
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator
from typing import Sequence
import bleach


ALLOWED_VIDEO_DOMAINS = {
    "youtube.com", "www.youtube.com", "youtu.be",
    "bilibili.com", "www.bilibili.com", "player.bilibili.com",
}


def sanitize_html(value: str) -> str:
    """Remove dangerous HTML tags, keep safe formatting."""
    allowed_tags = [
        "h3", "h4", "p", "br", "strong", "em", "b", "i", "u",
        "ul", "ol", "li", "a", "img", "video", "source", "iframe",
        "blockquote", "code", "pre", "span", "div", "table", "tr", "td", "th",
    ]
    allowed_attrs = {
        "a": ["href", "title", "target"],
        "img": ["src", "alt", "width", "height"],
        "video": ["src", "controls", "width", "height"],
        "source": ["src", "type"],
        "iframe": ["src", "width", "height", "frameborder", "allowfullscreen"],
        "td": ["colspan", "rowspan"],
        "th": ["colspan", "rowspan"],
    }
    return bleach.clean(value, tags=allowed_tags, attributes=allowed_attrs, strip=True)


def validate_video_url(v: str) -> str:
    """Validate and sanitize a video URL."""
    v = v.strip()
    if not v:
        return v
    parsed = urlparse(v)
    if not parsed.scheme.startswith("http"):
        raise ValueError("视频链接必须以 http:// 或 https:// 开头")
    hostname = parsed.hostname or ""
    if hostname and not any(domain in hostname for domain in ALLOWED_VIDEO_DOMAINS):
        if not re.match(r'^[\w\-]+(\.[\w\-]+)*\.[a-z]{2,}$', hostname):
            raise ValueError("视频链接域名格式不正确")
    return bleach.clean(v, tags=[], attributes={}, strip=True)


# ── Output Schemas ──

class GuideOut(BaseModel):
    id: int
    title: str
    description: str
    content: str
    icon: str
    image_url: str
    category: str
    tags: str
    badge: str
    video_url: str
    sort_order: int
    created_at: str | None = None

    model_config = {"from_attributes": True}


class CodeOut(BaseModel):
    id: int
    code: str
    title: str
    description: str
    reward: str
    expiry: str
    is_active: int
    sort_order: int
    created_at: str | None = None

    model_config = {"from_attributes": True}


class QuickRefOut(BaseModel):
    id: int
    title: str
    icon: str
    items: str
    sort_order: int
    created_at: str | None = None

    model_config = {"from_attributes": True}


class GuideList(BaseModel):
    items: Sequence[GuideOut]
    total: int


# ── Input Schemas: Guide (PVP / PVE) ──

class GuideCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    content: str = Field(default="", max_length=50000)
    icon: str = Field(default="", max_length=32)
    image_url: str = Field(default="", max_length=512)
    category: str = Field(default="general", max_length=64)
    tags: list[str] = Field(default_factory=list)
    badge: str = Field(default="", max_length=16)
    video_url: str = Field(default="", max_length=512)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        return sanitize_html(v)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        return sanitize_html(v.strip())

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        return sanitize_html(v)

    @field_validator("video_url")
    @classmethod
    def validate_video(cls, v: str) -> str:
        return validate_video_url(v)


class GuideUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    content: str | None = Field(default=None, max_length=50000)
    icon: str | None = Field(default=None, max_length=32)
    image_url: str | None = Field(default=None, max_length=512)
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = None
    badge: str | None = Field(default=None, max_length=16)
    video_url: str | None = Field(default=None, max_length=512)
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        return sanitize_html(v) if v is not None else v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        return sanitize_html(v.strip()) if v is not None else v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        return sanitize_html(v) if v is not None else v

    @field_validator("video_url")
    @classmethod
    def validate_video(cls, v: str | None) -> str | None:
        return validate_video_url(v) if v is not None else v


# ── Input Schemas: Code ──

class CodeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    title: str = Field(default="", max_length=64)
    description: str = Field(default="", max_length=500)
    reward: str = Field(default="", max_length=500)
    expiry: str = Field(default="长期有效", max_length=64)
    is_active: int = Field(default=1, ge=0, le=1)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("title", "description", "reward")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        return sanitize_html(v) if v else v


class CodeUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    title: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    reward: str | None = Field(default=None, max_length=500)
    expiry: str | None = Field(default=None, max_length=64)
    is_active: int | None = Field(default=None, ge=0, le=1)
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("title", "description", "reward")
    @classmethod
    def sanitize_text(cls, v: str | None) -> str | None:
        return sanitize_html(v) if v is not None else v


# ── Input Schemas: QuickRef ──

class QuickRefCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    icon: str = Field(default="", max_length=32)
    items: list[str] = Field(default_factory=list)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        return sanitize_html(v.strip())


class QuickRefUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    icon: str | None = Field(default=None, max_length=32)
    items: list[str] | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str | None) -> str | None:
        return sanitize_html(v.strip()) if v is not None else v


# ── Sort Item ──

class SortItem(BaseModel):
    id: int
    sort_order: int = Field(default=0, ge=0)


class SortPayload(BaseModel):
    items: list[SortItem]


# ── Batch Delete ──

class BatchDeletePayload(BaseModel):
    table: str
    ids: list[int]


# ── Login ──

class LoginPayload(BaseModel):
    username: str
    password: str


class ChangePasswordPayload(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Audit Log ──

class AuditLogOut(BaseModel):
    id: int
    action: str
    table_name: str
    item_id: int | None = None
    detail: str
    created_at: str | None = None

    model_config = {"from_attributes": True}


# ── Paginated Response ──

class PaginatedResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
