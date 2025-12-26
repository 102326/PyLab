import request from '@/utils/request'
// 1. 引入正确的类型 (注意路径是 @/model/auth 和 @/model/common)
import type { LoginReq, LoginRes, MeRes } from '@/model/auth'
import type { ApiResponse } from '@/model/common'

export class AuthApi {
  /**
   * 登录接口
   */
  static async login(data: LoginReq): Promise<LoginRes> {
    // 泛型说明：request.post 返回 AxiosResponse，其 .data 是 ApiResponse<LoginRes>
    const res = await request.post<ApiResponse<LoginRes>>('/auth/login', data)

    // 【核心修复】
    // res.data 是 { code: 200, msg: '...', data: {...} }
    // res.data.data 才是我们要的 { access_token: ... }
    return res.data.data
  }

  /**
   * 获取当前用户完整信息
   */
  static async getMe(): Promise<MeRes> {
    const res = await request.get<ApiResponse<MeRes>>('/auth/me')
    // 同理，拆包
    return res.data.data
  }
  static async register(data: LoginReq): Promise<void> {
    // 这里的返回值通常是 null 或简单消息，不需要解包 data.data
    await request.post('/auth/register', data)
  }
}
