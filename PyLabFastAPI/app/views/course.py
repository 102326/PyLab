# PyLabFastAPI/app/views/course.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from typing import Optional
from typing import List
from app.models.user import User
from app.models.course import Course, Chapter, Lesson, VideoResource, UserCourse
from tortoise.expressions import F
from app.schemas.course import (
    CourseCreateReq, CourseOut, UserCourseOut,
    ChapterCreateReq, ChapterOut,
    LessonCreateReq, LessonOut,CourseUpdateReq,ChapterUpdateReq,LessonUpdateReq
)
from app.services.es_sync import CourseESService
from app.services.vector_db import VectorDBService
from collections import defaultdict
from app.deps import get_current_user
from app.utils.jwt import MyJWT
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

    # === 🚑 [核心修复] ===
    # 刚创建的 chapter 对象，其 lessons 属性是 Relation 实例
    # 必须手动 fetch 一下，让它变成一个真正的空列表 []
    # 否则 Pydantic 转换 Schema 时会报错
    await chapter.fetch_related("lessons")

    return {
        "code": 200,
        "msg": "章节创建成功",
        "data": ChapterOut.model_validate(chapter)
    }


# === 4. 获取某课程的所有章节(含课时) ===
@router.get("/{course_id}/chapters")
async def get_course_chapters(course_id: int):
    # [核心修复]
    # 1. 增加 lessons__video (连表查询视频信息)
    # 2. 增加 lessons__problem (连表查询题目信息)
    chapters = await Chapter.filter(course_id=course_id) \
        .prefetch_related('lessons', 'lessons__video', 'lessons__problem') \
        .order_by("rank") \
        .all()

    data = []
    for c in chapters:
        # 手动排序 lesson (因为 Tortoise 的 prefetch 排序有时不稳定)
        sorted_lessons = sorted(c.lessons, key=lambda x: x.rank)

        # 构造 Pydantic 模型 (需确保 schemas/course.py 里的 LessonOut 有 video/problem 字段)
        # 这里用简易字典构造法，确保字段存在
        c_data = {
            "id": c.id,
            "title": c.title,
            "rank": c.rank,
            "lessons": []
        }

        for l in sorted_lessons:
            l_data = {
                "id": l.id,
                "title": l.title,
                "type": l.type,
                "rank": l.rank,
                "video": l.video,  # 关键：只要上面 prefetch 了，这里就有值
                "problem": l.problem  # 关键：OJ 题目也有了
            }
            c_data["lessons"].append(l_data)

        data.append(c_data)

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


# ===  7. 课程详情 ===
@router.get("/{course_id}", summary="获取课程详情")
async def get_course_detail(course_id: int, request: Request):
    # 1. 查询课程
    course = await Course.get_or_none(id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 2. 浏览量 +1
    course.view_count = F("view_count") + 1
    await course.save()

    # 3. 强制重新查询
    course = await Course.get(id=course_id).select_related("teacher")

    # 4. [修改逻辑] 适配 MyJWT 判断当前用户是否已加入
    is_joined = False
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            # === 这里改用 MyJWT.decode_token ===
            # 因为 MyJWT.decode_token 失败会抛出 HTTPException，所以我们需要 try-except 捕获它
            payload = MyJWT.decode_token(token)

            # 你的 MyJWT 生成 Token 时把 user_id 放在了 'sub' 字段
            user_id = payload.get("sub")

            if user_id:
                # 还要检查 Token 是否被拉黑 (可选，虽然详情页不做严格鉴权也行，但严谨点好)
                jti = payload.get("jti")
                if not await MyJWT.is_token_revoked(jti):
                    # 查库看是否已选课
                    exists = await UserCourse.exists(user_id=int(user_id), course_id=course.id)
                    if exists:
                        is_joined = True
        except Exception:
            # 无论是 Token 过期、格式错误还是 Redis 连接失败，都视为未登录，不报错
            pass

    # 5. 推荐逻辑
    related_courses = []
    try:
        related_courses = await VectorDBService.search_similar_by_id(course.id, limit=4)
    except:
        pass

    # 6. 组装数据
    data = CourseOut.model_validate(course).model_dump()
    data["teacher_name"] = course.teacher.nickname or course.teacher.username
    data["is_joined"] = is_joined

    return {
        "code": 200,
        "msg": "获取成功",
        "data": {
            "info": data,
            "related": related_courses
        }
    }


# === 8. 课程列表 (混合检索 RRF 版) ===
@router.get("", summary="获取公开课程列表(混合检索)")
async def get_courses(
        page: int = 1,
        size: int = 12,
        keyword: str = None,
        sort: str = "new"
):
    # --- 分支 A: 混合检索 (有关键词时触发) ---
    if keyword:
        # 1. 定义 RRF 常数 k (平滑参数，一般取 60)
        RRF_K = 60
        # 结果容器：{course_id: score}
        fused_scores = defaultdict(float)

        # 2. 并行召回 (ES + Vector)
        # 2.1 获取 关键词检索 结果 (ES 负责精确匹配)
        # 注意: es_sync.py 的 search 方法最好也支持 limit，目前默认返回所有，暂时取前 50
        es_hits = await CourseESService.search(keyword)
        es_hits = es_hits[:50]

        # 2.2 获取 向量检索 结果 (AI 负责语义匹配)
        vector_hits = await VectorDBService.search_similar_courses(keyword, limit=50)

        # 3. 计算 RRF 分数
        # 公式: Score = 1 / (k + rank)

        # 处理 ES 排名 (rank 从 0 开始)
        for rank, item in enumerate(es_hits):
            doc_id = item['id']
            fused_scores[doc_id] += 1 / (RRF_K + rank + 1)

        # 处理 Vector 排名
        for rank, item in enumerate(vector_hits):
            doc_id = item['id']
            fused_scores[doc_id] += 1 / (RRF_K + rank + 1)

        # 4. 根据融合分数倒序排序
        # sorted 返回 [(id, score), (id, score)...]
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        # 5. 内存分页
        start = (page - 1) * size
        end = start + size

        # 拿到本页的目标 ID 列表
        target_ids = [cid for cid, score in sorted_results[start:end]]
        total = len(sorted_results)

        if not target_ids:
            return {
                "code": 200,
                "msg": "获取成功",
                "data": {"items": [], "total": 0, "page": page, "size": size}
            }

        # 6. 回表查询完整详情 (必须保持 RRF 算出来的顺序)
        # 先一次性查出来
        db_courses = await Course.filter(id__in=target_ids).select_related('teacher').all()
        # 以此建立字典映射
        course_map = {c.id: c for c in db_courses}
        # 按 target_ids 的顺序重组列表 (关键步骤，否则顺序会乱)
        paged_courses = [course_map[cid] for cid in target_ids if cid in course_map]

    # --- 分支 B: 普通浏览 (无关键词，走数据库) ---
    else:
        query = Course.filter(is_published=True)
        if sort == "hot":
            query = query.order_by("-view_count", "-created_at")
        else:
            query = query.order_by("-created_at")

        total = await query.count()
        paged_courses = await query.offset((page - 1) * size).limit(size).select_related('teacher')

    # --- 通用序列化 ---
    data = []
    for c in paged_courses:
        c_dto = CourseOut.model_validate(c).model_dump()
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


# === 9. 加入课程  ===
@router.post("/{course_id}/join")
async def join_course(course_id: int, user: User = Depends(get_current_user)):
    # get_current_user 已经在 app/deps.py 里处理好了鉴权，
    # 只要你的 deps.py 也是用的 MyJWT 就没问题。

    course = await Course.get_or_none(id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 1. 检查是否已经加入过
    enrollment = await UserCourse.filter(user=user, course=course).first()
    if enrollment:
        return {
            "code": 200,
            "msg": "您已在学习此课程",
            "data": UserCourseOut.model_validate(enrollment)
        }

    # 2. 检查支付 (TODO)
    if course.price > 0:
        pass

    # 3. 创建学籍
    enrollment = await UserCourse.create(user=user, course=course)

    return {
        "code": 200,
        "msg": "加入成功！开始学习吧",
        "data": UserCourseOut.model_validate(enrollment)
    }


# === [新增] 8. 更新课程 (修复 405 错误) ===
@router.patch("/{course_id}", summary="更新课程信息/发布状态")
async def update_course(course_id: int, req: CourseUpdateReq, user: User = Depends(get_current_user)):
    course = await Course.get_or_none(id=course_id, teacher=user)
    if not course:
        raise HTTPException(404, "课程不存在或无权操作")

    # 动态更新字段
    update_data = req.model_dump(exclude_unset=True)
    if not update_data:
        return {"code": 400, "msg": "没有提交任何修改", "data": None}

    await course.update_from_dict(update_data)
    await course.save()

    # 如果修改了发布状态，触发 ES 同步
    if "is_published" in update_data:
        # 这里的 rabbit_client 需要确认你是否有这个 import，如果没有可以暂时注释掉或者手动调用
        # from app.core.mq import rabbit_client
        # await rabbit_client.publish_message({"id": course.id, "action": "update"})

        # 暂时用简单的 ES 同步代替 (如果你的 es_sync.py 有 sync 方法)
        # 或者直接忽略，等后台 worker 扫表
        pass

    return {
        "code": 200,
        "msg": "更新成功",
        "data": None
    }


# === [新增] 9. 更新章节 ===
# 注意路由：因为 router prefix="/courses"，所以这里最终路径是 /courses/chapters/{chapter_id}
@router.put("/chapters/{chapter_id}")
async def update_chapter(chapter_id: int, req: ChapterUpdateReq, user: User = Depends(get_current_user)):
    # 级联查询：先查章节，再查所属课程
    chapter = await Chapter.get_or_none(id=chapter_id).prefetch_related('course')
    if not chapter:
        raise HTTPException(404, "章节不存在")

    # 鉴权：检查课程老师是不是当前用户
    if chapter.course.teacher_id != user.id:
        raise HTTPException(403, "无权操作此课程")

    chapter.title = req.title
    chapter.rank = req.rank
    await chapter.save()

    return {
        "code": 200,
        "msg": "章节更新成功",
        "data": None
    }


# === [新增] 10. 删除章节 ===
@router.delete("/chapters/{chapter_id}")
async def delete_chapter(chapter_id: int, user: User = Depends(get_current_user)):
    chapter = await Chapter.get_or_none(id=chapter_id).prefetch_related('course')
    if not chapter:
        raise HTTPException(404, "章节不存在")

    if chapter.course.teacher_id != user.id:
        raise HTTPException(403, "无权操作")

    await chapter.delete()

    return {
        "code": 200,
        "msg": "章节已删除",
        "data": None
    }


# === [新增] 11. 更新课时 ===
@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: int, req: LessonUpdateReq, user: User = Depends(get_current_user)):
    # 稍微复杂点的鉴权：Lesson -> Chapter -> Course
    lesson = await Lesson.get_or_none(id=lesson_id).prefetch_related('chapter__course')
    if not lesson:
        raise HTTPException(404, "课时不存在")

    # lesson.chapter.course 可能是 None (如果数据完整性有问题)，这里假设是完整的
    if lesson.chapter.course.teacher_id != user.id:
        raise HTTPException(403, "无权操作")

    lesson.title = req.title
    lesson.type = req.type
    lesson.rank = req.rank
    if req.video_id:
        lesson.video_id = req.video_id

    await lesson.save()

    return {
        "code": 200,
        "msg": "课时更新成功",
        "data": None
    }


# === [新增] 12. 删除课时 ===
@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: int, user: User = Depends(get_current_user)):
    lesson = await Lesson.get_or_none(id=lesson_id).prefetch_related('chapter__course')
    if not lesson:
        raise HTTPException(404, "课时不存在")

    if lesson.chapter.course.teacher_id != user.id:
        raise HTTPException(403, "无权操作")

    await lesson.delete()

    return {
        "code": 200,
        "msg": "课时已删除",
        "data": None
    }


# === [新增] 13. 删除整个课程 ===
@router.delete("/{course_id}")
async def delete_course(course_id: int, user: User = Depends(get_current_user)):
    course = await Course.get_or_none(id=course_id, teacher=user)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在或无权操作")

    # 级联删除：章节、课时、关联的 UserCourse 都会被删除 (取决于数据库级联设置)
    # Tortoise ORM 默认通常需要手动处理，或者数据库层面有 ON DELETE CASCADE
    # 这里简单直接删，如果报错说明有外键约束没解开
    await course.delete()

    # 记得同步删除 ES 索引
    from app.services.es_sync import CourseESService
    await CourseESService.delete(course_id)

    return {"code": 200, "msg": "课程已删除", "data": None}