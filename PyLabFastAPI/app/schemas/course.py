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
    view_count: int = 0

    # [新增] 当前用户是否已加入 (仅在登录且请求详情时有效)
    is_joined: bool = False

    class Config:
        from_attributes = True


# === 章节相关 ===
class ChapterCreateReq(BaseModel):
    title: str
    rank: int = 0  # 排序

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
    rank: int
    video_id: Optional[int] = None

    # [新增] 必须把题目ID返回给前端
    problem_id: Optional[int] = None

    class Config:
        from_attributes = True


class ChapterOut(BaseModel):
    id: int
    title: str
    rank: int

    # [新增] 嵌套返回该章节下的所有课时
    lessons: List[LessonOut] = []

    class Config:
        from_attributes = True


class UserCourseOut(BaseModel):
    id: int
    course_id: int
    user_id: int
    progress: float
    joined_at: datetime

    class Config:
        from_attributes = True

class CourseUpdateReq(BaseModel):
    title: str = None
    desc: str = None
    cover: str = None
    price: float = None
    is_published: bool = None

class ChapterUpdateReq(BaseModel):
    title: str
    rank: int

class LessonUpdateReq(BaseModel):
    title: str
    type: str
    rank: int
    video_id: int = None