# app/views/oj.py
import uuid
import sys
import io
import traceback
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.models.oj import Problem, Submission, UserLessonProgress
from app.models.course import Lesson
from app.schemas.oj import SubmitReq, SubmissionOut, ProblemOut,ProblemCreateReq
from app.deps import get_current_user

router = APIRouter(prefix="/oj", tags=["OnlineJudge"])


# 1. 获取题目详情
@router.get("/problems/{problem_id}")
async def get_problem(problem_id: int):
    problem = await Problem.get_or_none(id=problem_id)
    if not problem:
        raise HTTPException(404, "题目不存在")
    return {"code": 200, "data": ProblemOut.model_validate(problem)}


# 2. 核心：提交代码
@router.post("/submit")
async def submit_code(req: SubmitReq, user: User = Depends(get_current_user)):
    # A. 检查题目
    problem = await Problem.get_or_none(id=req.problem_id)
    if not problem:
        raise HTTPException(404, "题目不存在")

    # B. 创建提交记录 (状态: PENDING)
    sub_id = str(uuid.uuid4())
    submission = await Submission.create(
        id=sub_id,
        user=user,
        problem=problem,
        code=req.code,
        language=req.language,
        status="PENDING"
    )

    # C. [简易判题机]
    run_status = "AC"
    error_msg = None

    try:
        # 捕获 stdout 输出
        captured_output = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output

        # === [核心修改] 定义允许使用的“白名单”函数 ===
        safe_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "int": int,
                "str": str,
                "list": list,
                "float": float,
                "abs": abs,
                "round": round,
                # 如果需要更多函数，在这里添加
            }
        }

        # 使用 safe_globals 运行代码
        exec(req.code, safe_globals)

        # 恢复 stdout
        sys.stdout = original_stdout
        user_output = captured_output.getvalue()

        # TODO: 这里应该比对 user_output 和题目预设的 output
        # 目前演示逻辑：只要没报错就算过

    except Exception:
        sys.stdout = sys.__stdout__  # 确保出错也能恢复
        run_status = "RE"  # Runtime Error
        error_msg = traceback.format_exc()

    # D. 更新提交状态
    submission.status = run_status
    submission.error_msg = error_msg
    await submission.save()

    # E. 如果 AC 了，自动解锁下一节课
    if run_status == "AC":
        await unlock_next_lesson(user, problem.id)

    return {
        "code": 200,
        "msg": "判题完成",
        "data": SubmissionOut.model_validate(submission)
    }


# --- 辅助函数：解锁下一关 ---
async def unlock_next_lesson(user: User, problem_id: int):
    # 1. 找到这道题属于哪个 Lesson
    # 注意：models/course.py 里的 Lesson 有个 problem 字段关联了 Problem
    # 我们反向查：哪个 Lesson 关联了这个 Problem
    current_lesson = await Lesson.get_or_none(problem_id=problem_id)

    if not current_lesson:
        return  # 这道题可能不属于任何课程，只是独立练习

    # 2. 标记当前 Lesson 为 COMPLETED
    await UserLessonProgress.update_or_create(
        user=user,
        lesson=current_lesson,
        defaults={"status": "COMPLETED"}
    )

    # 3. 找到下一节课 (根据 rank 排序)
    # 逻辑：同章节 rank 更大的，或者下一章节 rank 最小的
    # 为了简单，我们假设是同章节的下一节
    next_lesson = await Lesson.filter(
        chapter_id=current_lesson.chapter_id,
        rank__gt=current_lesson.rank
    ).order_by('rank').first()

    if next_lesson:
        # 解锁它
        progress, created = await UserLessonProgress.get_or_create(
            user=user,
            lesson=next_lesson
        )
        if progress.status == "LOCKED":
            progress.status = "UNLOCKED"
            await progress.save()
            print(f"🔓 已自动解锁下一节课: {next_lesson.title}")


# === [新增] 3. 创建题目 ===
@router.post("/problems")
async def create_problem(req: ProblemCreateReq, user: User = Depends(get_current_user)):
    # 鉴权：只有老师能出题 (role=1)
    if user.role != 1:
        raise HTTPException(403, "只有讲师可以创建题目")

    # 生成唯一的 slug (简单处理，实际可用 uuid)
    slug = f"p-{uuid.uuid4().hex[:8]}"

    problem = await Problem.create(
        title=req.title,
        slug=slug,
        content=req.content,
        init_code=req.init_code,
        time_limit=req.time_limit,
        memory_limit=req.memory_limit
    )

    return {"code": 200, "msg": "题目创建成功", "data": ProblemOut.model_validate(problem)}


# === [新增] 4. 修改题目 ===
@router.put("/problems/{problem_id}")
async def update_problem(problem_id: int, req: ProblemCreateReq, user: User = Depends(get_current_user)):
    if user.role != 1:
        raise HTTPException(403, "权限不足")

    problem = await Problem.get_or_none(id=problem_id)
    if not problem:
        raise HTTPException(404, "题目不存在")

    problem.title = req.title
    problem.content = req.content
    problem.init_code = req.init_code
    await problem.save()

    return {"code": 200, "msg": "题目更新成功", "data": ProblemOut.model_validate(problem)}