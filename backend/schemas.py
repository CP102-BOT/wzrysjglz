from pydantic import BaseModel
from typing import Sequence


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

    model_config = {"from_attributes": True}


class CodeOut(BaseModel):
    id: int
    code: str
    description: str
    reward: str
    expiry: str
    is_active: int

    model_config = {"from_attributes": True}


class QuickRefOut(BaseModel):
    id: int
    title: str
    icon: str
    items: str
    sort_order: int

    model_config = {"from_attributes": True}


class GuideList(BaseModel):
    items: Sequence[GuideOut]
    total: int
