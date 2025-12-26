// src/model/CommonDTO.ts

/**
 * 后端通用响应结构
 * T 代表 data 字段具体的类型
 */
export interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}
