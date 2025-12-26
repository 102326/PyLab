// src/composables/useAudioRecorder.ts
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const mediaRecorder = ref<MediaRecorder | null>(null)
  const audioChunks = ref<Blob[]>([])
  const audioUrl = ref<string | null>(null)
  const audioBlob = ref<Blob | null>(null)

  // 检测当前浏览器支持的 MIME 类型
  const getSupportedMimeType = () => {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4', // Safari
    ]
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type
      }
    }
    return '' // 都不支持（极少见）
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = getSupportedMimeType()

      if (!mimeType) {
        ElMessage.error('当前浏览器不支持录音')
        return
      }

      mediaRecorder.value = new MediaRecorder(stream, { mimeType })
      audioChunks.value = []

      mediaRecorder.value.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.value.push(event.data)
        }
      }

      mediaRecorder.value.start() // 每 1000ms 触发一次数据片段，防止最后丢失
      isRecording.value = true
    } catch (err) {
      console.error('无法获取麦克风权限', err)
      ElMessage.error('请检查麦克风权限')
    }
  }

  // 返回 Promise 以便 await 等待录音结束
  const stopRecording = (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorder.value || !isRecording.value) {
        resolve(null)
        return
      }

      mediaRecorder.value.onstop = () => {
        // [关键修正] 使用 recorder 实际的 mimeType，而不是强行指定 mp3
        const mimeType = mediaRecorder.value?.mimeType || 'audio/webm'
        const blob = new Blob(audioChunks.value, { type: mimeType })

        audioBlob.value = blob
        audioUrl.value = URL.createObjectURL(blob)

        // 释放麦克风
        mediaRecorder.value?.stream.getTracks().forEach((track) => track.stop())
        mediaRecorder.value = null
        isRecording.value = false

        resolve(blob)
      }

      mediaRecorder.value.stop()
    })
  }

  return {
    isRecording,
    audioUrl,
    audioBlob,
    startRecording,
    stopRecording,
  }
}
