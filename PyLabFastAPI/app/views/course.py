# PyLabFastAPI/app/views/course.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.course import Course, Chapter, Lesson, VideoResource
from app.schemas.course import LessonCreateReq, LessonOut
from app.deps import get_current_user
from app.models.user import User
from app.models.course import Course, Chapter
from app.schemas.course import CourseCreateReq, CourseOut, ChapterCreateReq, ChapterOut
from fastapi import BackgroundTasks
from app.services.vector_db import VectorDBService

router = APIRouter(prefix="/courses", tags=["Course"])


# === 1. 创建课程 ===
@router.post("", response_model=CourseOut)
async def create_course(
        req: CourseCreateReq,
        bg_tasks: BackgroundTasks,  # <--- [新增参数]
        user: User = Depends(get_current_user)
):
    # 讲师创建一个新课程
    course = await Course.create(
        teacher=user,
        **req.model_dump()
    )

    # === [狠活儿] 异步生成向量 ===
    # 放入后台任务，不卡顿主线程
    bg_tasks.add_task(
        VectorDBService.update_course_embedding,
        course.id,
        course.title,
        course.desc
    )

    return course


# === 2. 获取我的课程列表 (讲师端) ===
@router.get("/my", response_model=List[CourseOut])
async def get_my_courses(user: User = Depends(get_current_user)):
    return await Course.filter(teacher=user).all()


# === 3. 给课程添加章节 ===
@router.post("/{course_id}/chapters", response_model=ChapterOut)
async def create_chapter(
        course_id: int,
        req: ChapterCreateReq,
        user: User = Depends(get_current_user)
):
    # 先检查课程是否存在，且是否是当前用户创建的
    course = await Course.get_or_none(id=course_id, teacher=user)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在或无权操作")

    chapter = await Chapter.create(
        course=course,
        title=req.title,
        rank=req.rank
    )
    return chapter


# === 4. 获取某课程的所有章节 ===
@router.get("/{course_id}/chapters", response_model=List[ChapterOut])
async def get_course_chapters(course_id: int):
    # 这里不需要鉴权，因为学生也要看目录
    return await Chapter.filter(course_id=course_id).order_by("rank").all()


# === 5. 创建课时 (核心：绑定视频) ===
@router.post("/{course_id}/chapters/{chapter_id}/lessons", response_model=LessonOut)
async def create_lesson(
        course_id: int,
        chapter_id: int,
        req: LessonCreateReq,
        user: User = Depends(get_current_user)
):
    # 1. 校验章节是否存在 (且属于当前讲师的课程)
    # 这里用 filter 链式查询确保安全
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

    # 3. 如果是视频课，必须校验视频ID
    if req.type == "video":
        if not req.video_id:
            raise HTTPException(status_code=400, detail="视频课必须提供 video_id")

        # 检查视频是否存在
        video = await VideoResource.get_or_none(id=req.video_id)
        if not video:
            raise HTTPException(status_code=404, detail="视频资源不存在")

        lesson_data["video"] = video  # 绑定关系

    # 4. (预留) 如果是题目课
    # if req.type == "problem": ...

    # 5. 写入数据库
    lesson = await Lesson.create(**lesson_data)

    return lesson


# === [新增接口] 6. AI 语义搜索 ===
@router.get("/search/semantic")
async def search_courses_semantic(q: str):
    """
    AI 搜索接口：输入自然语言，返回最匹配的课程
    """
    if not q:
        return []

    results = await VectorDBService.search_similar_courses(q)
    return {
        "query": q,
        "matches": results,
        "ai_comment": "为您找到最相关的课程"
    }