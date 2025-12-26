import request from '@/utils/request'
import type { ApiResponse } from '@/model/common' // 如果没有 common.ts，请看下面补充
import type { CreateVideoReq, VideoInfo } from '@/model/media'

export interface QiniuTokenRes {
  token: string
  domain: string
}

export interface IdCardVerifyReq {
  front_url: string
  back_url: string
}

export interface QiniuTokenRes {
  token: string
  domain: string
}

export interface IdCardVerifyReq {
  front_url: string
  back_url: string
}

export class MediaApi {
  /**
   * 1. 获取七牛云上传凭证
   */
  static async getUploadToken(): Promise<QiniuTokenRes> {
    const res = await request.get<ApiResponse<QiniuTokenRes>>('/media/token')
    return res.data.data
  }

  /**
   * 2. 提交认证信息 (图片URL)
   */
  static async verifyIdCard(data: IdCardVerifyReq) {
    const res = await request.post<ApiResponse<any>>('/auth/verify/idcard', data)
    return res.data.data
  }
  static async createVideo(data: CreateVideoReq): Promise<VideoInfo> {
    const res = await request.post<ApiResponse<VideoInfo>>('/media/videos', data)
    return res.data.data
  }
}
export function uploadFile(file: File | Blob) {
  const formData = new FormData()

  if (file instanceof Blob && !(file instanceof File)) {
    // [关键修正] 根据 Blob 的 type 决定后缀名
    let extension = 'webm'
    if (file.type.includes('mp4')) extension = 'm4a'
    else if (file.type.includes('ogg')) extension = 'ogg'
    // 默认回落到 webm (Chrome/Edge/Firefox)

    // 生成文件名：voice_时间戳.webm
    formData.append('file', file, `voice_${Date.now()}.${extension}`)
  } else {
    // 普通文件上传 (图片等)
    formData.append('file', file)
  }

  return request.post('/media/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
