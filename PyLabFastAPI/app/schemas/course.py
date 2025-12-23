# PyLabFastAPI/app/schemas/course.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# === 课程相关 ===
class CourseBase(BaseModel):
    title: str
    desc: Optional[str] = None
    cover: Optional[str] = None  # 封面图URL
    price: float = 0


class CourseCreateReq(CourseBase):
    pass


class CourseOut(CourseBase):
    id: int
    teacher_id: int
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从 ORM 模型转换


# === 章节相关 ===
class ChapterCreateReq(BaseModel):
    title: str
    rank: int = 0  # 排序


class ChapterOut(BaseModel):
    id: int
    title: str
    rank: int

    class Config:
        from_attributes = True

from enum import Enum

# === 课时相关 ===
class LessonType(str, Enum):
    VIDEO = "video"
    PROBLEM = "problem"

class LessonCreateReq(BaseModel):
    title: str
    type: LessonType  # 必须是 'video' 或 'problem'
    rank: int = 0
    # 如果是视频课，必须传 video_id
    video_id: Optional[int] = None
    # 如果是题目课，必须传 problem_id (后面开发OJ时用)
    problem_id: Optional[int] = None

class LessonOut(BaseModel):
    id: int
    title: str
    type: str
    video_id: Optional[int] = None
    problem_id: Optional[int] = None

    class Config:
        from_attributes = True