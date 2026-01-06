# app/models/course.py
from tortoise import fields, models
from enum import Enum


class Course(models.Model):
    """课程元数据表"""
    id = fields.IntField(pk=True)
    # 这里虽然物理外键是 User，但业务逻辑上必须要求 user.role == 1
    teacher = fields.ForeignKeyField('models.User', related_name='courses', description="讲师")

    title = fields.CharField(max_length=100, description="课程标题")
    desc = fields.TextField(null=True, description="课程简介")
    cover = fields.CharField(max_length=255, null=True, description="封面图URL")
    price = fields.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_published = fields.BooleanField(default=False, description="是否发布")
    view_count = fields.IntField(default=0, description="浏览量/热度")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "courses"


class Chapter(models.Model):
    """章节表"""
    id = fields.IntField(pk=True)
    course = fields.ForeignKeyField('models.Course', related_name='chapters')
    title = fields.CharField(max_length=100)
    rank = fields.IntField(default=0, description="排序")

    class Meta:
        table = "chapters"
        ordering = ["rank"]


class Lesson(models.Model):
    """[核心] 课时表"""

    class LessonType(str, Enum):
        VIDEO = "video"
        PROBLEM = "problem"

    id = fields.IntField(pk=True)
    chapter = fields.ForeignKeyField('models.Chapter', related_name='lessons')
    title = fields.CharField(max_length=100)
    type = fields.CharEnumField(LessonType, description="课时类型")
    rank = fields.IntField(default=0, description="排序")

    # 资源挂载
    video = fields.ForeignKeyField('models.VideoResource', related_name='lessons', null=True)
    problem = fields.ForeignKeyField('models.Problem', related_name='lessons', null=True)

    # 闯关链表：上一节课ID
    prev_lesson_id = fields.IntField(null=True, description="前置解锁条件ID")

    class Meta:
        table = "lessons"
        ordering = ["rank"]


class VideoResource(models.Model):
    """视频资源表"""
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=100)
    file_key = fields.CharField(max_length=255)
    play_url = fields.CharField(max_length=255, null=True)
    duration = fields.IntField(default=0)
    status = fields.IntField(default=0)
    uploader = fields.ForeignKeyField('models.User', related_name='uploaded_videos')
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "video_resources"


class UserCourse(models.Model):
    """
    用户-课程关联表 (记录购买/加入记录 + 学习进度)
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='enrolled_courses')
    course = fields.ForeignKeyField('models.Course', related_name='students')

    # 学习进度
    progress = fields.FloatField(default=0.0, description="学习进度(0-100)")

    # 断点续播：记录上次学到了哪一节课
    last_lesson = fields.ForeignKeyField('models.Lesson', related_name='+', null=True, description="上次学到的课时")

    joined_at = fields.DatetimeField(auto_now_add=True, description="加入时间")

    class Meta:
        table = "user_courses"
        # 联合唯一索引：防止重复加入同一门课
        unique_together = (("user", "course"),)