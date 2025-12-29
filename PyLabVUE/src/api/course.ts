// src/api/course.ts
import request from '@/utils/request'
import type { ApiResponse } from '@/model/common'

// === 接口定义 ===

export interface CourseCreateReq {
  title: string
  desc?: string
  cover?: string
  price?: number
}

export interface ChapterCreateReq {
  title: string
  rank?: number
}

export interface LessonCreateReq {
  title: string
  type: 'video' | 'problem'
  rank?: number
  video_id?: number
}

export interface Course {
  id: number
  title: string
  cover: string
  // ... 其他字段
}

export interface Chapter {
  id: number
  title: string
}

export interface Lesson {
  id: number
  title: string
}

export interface CourseListQuery {
  page?: number
  size?: number
  keyword?: string
}

// [新增] 课程列表响应结构
export interface CourseListRes {
  items: Array<Course & { teacher_name: string }> // 混入讲师名
  total: number
  page: number
  size: number
}

// === API 类 ===

export class CourseApi {
  /**
   * 1. 创建课程
   */
  static async createCourse(data: CourseCreateReq) {
    const res = await request.post<ApiResponse<Course>>('/courses', data)
    return res.data.data
  }

  /**
   * 2. 创建章节
   */
  static async createChapter(courseId: number, data: ChapterCreateReq) {
    const res = await request.post<ApiResponse<Chapter>>(`/courses/${courseId}/chapters`, data)
    return res.data.data
  }

  /**
   * 3. 创建课时 (挂载视频)
   */
  static async createLesson(courseId: number, chapterId: number, data: LessonCreateReq) {
    const res = await request.post<ApiResponse<Lesson>>(
      `/courses/${courseId}/chapters/${chapterId}/lessons`,
      data,
    )
    return res.data.data
  }
  static async getCourses(params: CourseListQuery) {
    const res = await request.get<ApiResponse<CourseListRes>>('/courses', { params })
    return res.data.data
  }
}
