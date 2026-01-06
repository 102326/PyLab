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
  desc?: string
  cover: string
  price: number
  view_count: number
  is_published: boolean // [新增]
  teacher_name?: string
  created_at: string
  is_joined?: boolean
}

export interface Lesson {
  id: number
  title: string
  type: 'video' | 'problem'
  rank: number
  video?: {
    play_url: string
    duration: number
    title: string
    file_key: string
    file_size: number
  }
  problem?: {
    id: number
    title: string
    content: string
    init_code: string
    time_limit: number
    memory_limit: number
  }
  problem_id?: number
}

export interface Chapter {
  id: number
  title: string
  rank: number
  lessons: Lesson[]
}

export interface UserCourse {
  id: number
  course_id: number
  user_id: number
  progress: number
  joined_at: string
}

export interface CourseListQuery {
  page?: number
  size?: number
  keyword?: string
  sort?: 'new' | 'hot'
}

export interface CourseListRes {
  items: Array<Course & { teacher_name: string }>
  total: number
  page: number
  size: number
}

export interface CourseDetailRes {
  info: Course
  related: Course[]
}

export class CourseApi {
  static async createCourse(data: CourseCreateReq) {
    const res = await request.post<ApiResponse<Course>>('/courses', data)
    return res.data.data
  }

  // [修复] 补全 getMyCourses
  static async getMyCourses() {
    const res = await request.get<ApiResponse<Course[]>>('/courses/my')
    return res.data.data
  }

  static async createChapter(courseId: number, data: ChapterCreateReq) {
    const res = await request.post<ApiResponse<Chapter>>(`/courses/${courseId}/chapters`, data)
    return res.data.data
  }

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

  static async getCourseDetail(courseId: number) {
    const res = await request.get<ApiResponse<CourseDetailRes>>(`/courses/${courseId}`)
    return res.data.data
  }

  static async joinCourse(courseId: number) {
    const res = await request.post<ApiResponse<UserCourse>>(`/courses/${courseId}/join`)
    return res.data.data
  }

  static async getCourseChapters(courseId: number) {
    const res = await request.get<ApiResponse<Chapter[]>>(`/courses/${courseId}/chapters`)
    return res.data.data
  }

  static async publishCourse(courseId: number) {
    const res = await request.patch<ApiResponse<any>>(`/courses/${courseId}`, {
      is_published: true,
    })
    return res.data.data
  }

  static async updateCourse(id: number, data: Partial<Course>) {
    return request.patch(`/courses/${id}`, data)
  }

  static async updateChapter(id: number, data: { title: string; rank: number }) {
    return request.put(`/courses/chapters/${id}`, data)
  }

  static async deleteChapter(id: number) {
    return request.delete(`/courses/chapters/${id}`)
  }

  static async updateLesson(id: number, data: any) {
    return request.put(`/courses/lessons/${id}`, data)
  }

  static async deleteLesson(id: number) {
    return request.delete(`/courses/lessons/${id}`)
  }
  static async deleteCourse(id: number) {
    return request.delete(`/courses/${id}`).then((res) => res.data)
  }
}
