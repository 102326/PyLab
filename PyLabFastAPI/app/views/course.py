# PyLabFastAPI/app/views/course.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from app.models.user import User
from app.models.course import Course, Chapter, Lesson, VideoResource
from app.schemas.course import (
    CourseCreateReq, CourseOut,
    ChapterCreateReq, ChapterOut,
    LessonCreateReq, LessonOut
)
from app.deps import get_current_user
from app.services.vector_db import VectorDBService

router = APIRouter(prefix="/courses", tags=["Course"])


# === 1. 创建课程 ===
@router.post("")
async def create_course(
        req: CourseCreateReq,
        bg_tasks: BackgroundTasks,
        user: User = Depends(get_current_user)
):
    # 讲师创建一个新课程
    course = await Course.create(
        teacher=user,
        **req.model_dump()
    )

    # 异步生成向量
    bg_tasks.add_task(
        VectorDBService.update_course_embedding,
        course.id,
        course.title,
        course.desc
    )

    # [核心修复] 使用 model_validate 替代 from_tortoise_orm，且不需要 await
    data = CourseOut.model_validate(course)

    return {
        "code": 200,
        "msg": "课程创建成功",
        "data": data
    }


# === 2. 获取我的课程列表 (讲师端) ===
@router.get("/my")
async def get_my_courses(user: User = Depends(get_current_user)):
    courses = await Course.filter(teacher=user).all()

    # [核心修复] 列表推导式中使用 model_validate
    data = [CourseOut.model_validate(c) for c in courses]

    return {
        "code": 200,
        "msg": "获取成功",
        "data": data
    }


# === 3. 给课程添加章节 ===
@router.post("/{course_id}/chapters")
async def create_chapter(
        course_id: int,
        req: ChapterCreateReq,
        user: User = Depends(get_current_user)
):
    course = await Course.get_or_none(id=course_id, teacher=user)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在或无权操作")

    chapter = await Chapter.create(
        course=course,
        title=req.title,
        rank=req.rank
    )

    # [核心修复]
    return {
        "code": 200,
        "msg": "章节创建成功",
        "data": ChapterOut.model_validate(chapter)
    }


# === 4. 获取某课程的所有章节 ===
@router.get("/{course_id}/chapters")
async def get_course_chapters(course_id: int):
    chapters = await Chapter.filter(course_id=course_id).order_by("rank").all()
    # [核心修复]
    data = [ChapterOut.model_validate(c) for c in chapters]
    return {
        "code": 200,
        "msg": "获取成功",
        "data": data
    }


# === 5. 创建课时 (核心：绑定视频) ===
@router.post("/{course_id}/chapters/{chapter_id}/lessons")
async def create_lesson(
        course_id: int,
        chapter_id: int,
        req: LessonCreateReq,
        user: User = Depends(get_current_user)
):
    # 1. 校验章节
    chapter = await Chapter.filter(id=chapter_id, course__id=course_id, course__teacher=user).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在或无权操作")

    # 2. 准备数据
    lesson_data = {
        "chapter": chapter,
        "title": req.title,
        "type": req.type,
        "rank": req.rank
    }

    # 3. 校验视频ID
    if req.type == "video":
        if not req.video_id:
            raise HTTPException(status_code=400, detail="视频课必须提供 video_id")

        video = await VideoResource.get_or_none(id=req.video_id)
        if not video:
            raise HTTPException(status_code=404, detail="视频资源不存在")

        lesson_data["video"] = video

    # 4. 写入数据库
    lesson = await Lesson.create(**lesson_data)

    # [核心修复]
    return {
        "code": 200,
        "msg": "课时创建成功",
        "data": LessonOut.model_validate(lesson)
    }


# === 6. AI 语义搜索 ===
@router.get("/search/semantic")
async def search_courses_semantic(q: str):
    if not q:
        return {"code": 200, "data": []}

    results = await VectorDBService.search_similar_courses(q)
    return {
        "code": 200,
        "msg": "搜索完成",
        "data": {
            "query": q,
            "matches": results
        }
    }

# === 7. 课程搜索 ===
@router.get("", summary="获取公开课程列表")
async def get_courses(
    page: int = 1,
    size: int = 12,
    keyword: str = None  # 支持简单的标题搜索
):
    # 1. 基础查询：只看已发布的
    # 注意：之前的 Course 模型里 is_published 默认为 False，
    # 如果你刚才发布的课程没在数据库里手动改为 True，可能查不出来。
    # 为了测试方便，我们暂时先查所有，或者你记得去数据库把 is_published 改为 true
    # query = Course.filter(is_published=True)
    query = Course.all() # 暂时查所有，方便调试

    # 2. 关键词过滤
    if keyword:
        query = query.filter(title__icontains=keyword)

    # 3. 总数 (用于前端分页)
    total = await query.count()

    # 4. 分页查询 + 连表查询讲师信息
    # select_related('teacher') 避免 N+1 查询问题
    courses = await query.offset((page - 1) * size).limit(size).select_related('teacher').order_by('-created_at')

    # 5. 序列化
    # 我们需要一个新的 Schema 来包含 teacher 的昵称，这里简单处理手动拼装
    data = []
    for c in courses:
        c_dto = CourseOut.model_validate(c).model_dump()
        # 补上讲师昵称
        c_dto['teacher_name'] = c.teacher.nickname or c.teacher.username
        data.append(c_dto)

    return {
        "code": 200,
        "msg": "获取成功",
        "data": {
            "items": data,
            "total": total,
            "page": page,
            "size": size
        }
    }