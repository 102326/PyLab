# app/models/oj.py
from tortoise import fields, models


class Problem(models.Model):
    """题目表 (独立于课程存在，构建题库)"""
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=100)
    slug = fields.CharField(max_length=100, unique=True, description="URL别名")
    content = fields.TextField(description="Markdown描述")
    init_code = fields.TextField(default="", description="代码模板")
    time_limit = fields.IntField(default=1000, description="时间限制(ms)")
    memory_limit = fields.IntField(default=128, description="内存限制(MB)")
    test_case_path = fields.CharField(max_length=255, null=True, description="MinIO用例路径")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "problems"


class Submission(models.Model):
    """代码提交记录表"""
    id = fields.CharField(pk=True, max_length=36, description="UUID")
    user = fields.ForeignKeyField('models.User', related_name='submissions')
    problem = fields.ForeignKeyField('models.Problem', related_name='submissions')

    code = fields.TextField()
    language = fields.CharField(max_length=20, default="python")
    status = fields.CharField(max_length=20, default="PENDING")  # AC, WA, TLE...

    memory_cost = fields.IntField(null=True)
    time_cost = fields.IntField(null=True)
    error_msg = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "submissions"


class UserLessonProgress(models.Model):
    """[核心] 用户学习进度表 - 记录每一节课的状态"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='lesson_progress')

    # 字符串引用 'models.Lesson' 可以解决循环导入问题 (因为 Lesson 在 models/course.py)
    lesson = fields.ForeignKeyField('models.Lesson', related_name='user_progress')

    # 状态: LOCKED(锁定), UNLOCKED(进行中), COMPLETED(已完成)
    status = fields.CharField(max_length=20, default="LOCKED")

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_lesson_progress"
        # 联合唯一索引：一个用户对同一节课只有一条进度记录
        unique_together = (("user", "lesson"),)