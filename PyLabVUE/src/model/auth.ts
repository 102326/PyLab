// src/model/auth.ts

// src/model/auth.ts
export interface LoginReq {
  login_type: 'password' | 'dingtalk'
  phone?: string
  password?: string
  auth_code?: string
  role?: number // <--- 新增：注册时必选
}

/**
 * 用户信息
 * 对应后端 User 模型
 */
export interface UserInfo {
  id: number
  username: string
  nickname: string
  avatar: string | null
  role: number // 0=学生, 1=老师, 9=管理员
}

/**
 * 登录成功响应
 * 对应后端 Token 响应
 */
export interface LoginRes {
  access_token: string
  token_type: string
  user_info: UserInfo
}

/**
 * 教师档案
 * 对应后端 app/models/user.py -> TeacherProfile
 */
export interface TeacherProfile {
  real_name: string
  id_card: string
  verify_status: 0 | 1 | 2 | 3 // 0=未提交, 1=审核中, 2=已通过, 3=驳回
  reject_reason?: string
  id_card_img_f?: string
  id_card_img_b?: string
}

/**
 * 完整的用户信息 (包含角色)
 * 对应后端 /auth/me 接口返回的 user_info
 */
export interface UserInfoFull extends UserInfo {
  role: 0 | 1 | 9 // 0=学生, 1=老师, 9=管理员
}

/**
 * /auth/me 接口的响应数据
 */
export interface MeRes {
  user_info: UserInfoFull
  teacher_profile: TeacherProfile | null
}
