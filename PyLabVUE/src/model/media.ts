// src/model/media.ts

/**
 * 视频创建参数
 */
export interface CreateVideoReq {
  title: string
  file_key: string // 七牛云的文件 Key
  file_hash: string // 七牛云的文件 Hash
  file_size: number
  duration?: number // 视频时长 (可选)
}

/**
 * 视频信息响应
 */
export interface VideoInfo {
  id: number
  title: string
  play_url: string
  cover_url: string
  created_at: string
}
