// src/api/oj.ts
import request from '@/utils/request'
import type { ApiResponse } from '@/model/common'

export interface Problem {
  id: number
  title: string
  content: string
  init_code: string
  time_limit: number
  memory_limit: number
}

export interface SubmitReq {
  problem_id: number
  code: string
  language?: string
}

export interface Submission {
  id: string
  status: 'PENDING' | 'AC' | 'WA' | 'TLE' | 'RE'
  error_msg?: string
  time_cost?: number
  memory_cost?: number
  created_at: string
}

export class OJApi {
  static async getProblem(problemId: number) {
    const res = await request.get<ApiResponse<Problem>>(`/oj/problems/${problemId}`)
    return res.data.data
  }

  static async submitCode(data: SubmitReq) {
    const res = await request.post<ApiResponse<Submission>>('/oj/submit', data)
    return res.data.data
  }

  // [修复] 补全创建题目
  static async createProblem(data: any) {
    const res = await request.post<ApiResponse<Problem>>('/oj/problems', data)
    return res.data.data
  }

  // [修复] 补全更新题目
  static async updateProblem(id: number, data: any) {
    const res = await request.put<ApiResponse<Problem>>(`/oj/problems/${id}`, data)
    return res.data.data
  }
}
