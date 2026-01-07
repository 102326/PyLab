// src/api/oj.ts
import request from '@/utils/request'
import type { ApiResponse } from '@/model/common'

// 题目详情接口定义
export interface Problem {
  id: number
  title: string
  content: string // Markdown
  init_code: string
  time_limit: number
  memory_limit: number
}

// 提交请求
export interface SubmitReq {
  problem_id: number
  code: string
  language?: string
}

// 提交结果
export interface Submission {
  id: string
  status: 'PENDING' | 'AC' | 'WA' | 'TLE' | 'RE'
  error_msg?: string
  time_cost?: number
  memory_cost?: number
  created_at: string
}

export class OJApi {
  /**
   * 获取题目详情
   */
  static async getProblem(problemId: number) {
    const res = await request.get<ApiResponse<Problem>>(`/oj/problems/${problemId}`)
    return res.data.data
  }

  /**
   * 提交代码
   */
  static async submitCode(data: SubmitReq) {
    const res = await request.post<ApiResponse<Submission>>('/oj/submit', data)
    return res.data.data
  }

  /**
   * [新增] 创建题目
   */
  static async createProblem(data: any) {
    const res = await request.post<ApiResponse<Problem>>('/oj/problems', data)
    return res.data.data
  }

  /**
   * [新增] 更新题目
   */
  static async updateProblem(id: number, data: any) {
    const res = await request.put<ApiResponse<Problem>>(`/oj/problems/${id}`, data)
    return res.data.data
  }
}
