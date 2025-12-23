# app/models/user.py
from tortoise import fields, models
from enum import IntEnum


# === 1. 定义角色枚举 (数据库存数字，代码用枚举) ===
class UserRole(IntEnum):
    STUDENT = 0  # 学生 (默认)
    TEACHER = 1  # 老师
    ADMIN = 9  # 管理员


class User(models.Model):
    """[核心] 用户表 - 仅存储通用登录信息"""
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, null=True, description="系统唯一ID")
    password = fields.CharField(max_length=128, null=True, description="加密密码")
    nickname = fields.CharField(max_length=50, null=True, description="显示昵称")
    avatar = fields.CharField(max_length=255, null=True, description="头像URL")
    phone = fields.CharField(max_length=20, null=True, index=True, description="手机号")

    # 核心字段：角色区分
    role = fields.IntEnumField(UserRole, default=UserRole.STUDENT, description="角色: 0=学生, 1=老师, 9=管理员")

    is_active = fields.BooleanField(default=True, description="是否激活")
    created_at = fields.DatetimeField(auto_now_add=True)

    # 反向关联 (Tortoise 智能提示用)
    social_accounts: fields.ReverseRelation["SocialAccount"]
    teacher_profile: fields.ReverseRelation["TeacherProfile"]
    courses: fields.ReverseRelation["Course"]

    class Meta:
        table = "users"


class TeacherProfile(models.Model):
    """[扩展] 教师档案表 - 存储敏感/审核信息"""
    id = fields.IntField(pk=True)
    # OneToOne: 一个用户只能有一个教师档案
    user = fields.OneToOneField('models.User', related_name='teacher_profile', on_delete=fields.CASCADE)

    # 实名认证信息
    real_name = fields.CharField(max_length=20, null=True, description="真实姓名")
    id_card = fields.CharField(max_length=18, null=True, description="身份证号")
    id_card_img_f = fields.CharField(max_length=255, null=True, description="身份证正面URL")
    id_card_img_b = fields.CharField(max_length=255, null=True, description="身份证反面URL")

    # 审核状态: 0=未提交, 1=审核中, 2=已通过, 3=驳回
    verify_status = fields.IntField(default=0, description="认证状态")
    reject_reason = fields.CharField(max_length=100, null=True, description="驳回原因")

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "teacher_profiles"


class SocialAccount(models.Model):
    """[扩展] 第三方账号绑定表"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='social_accounts')
    platform = fields.CharField(max_length=20, index=True)
    openid = fields.CharField(max_length=100, index=True)
    union_info = fields.JSONField(default={}, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "social_accounts"
        unique_together = (("platform", "openid"),)