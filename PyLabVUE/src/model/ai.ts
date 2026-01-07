// src/model/ai.ts
export interface ChatReq {
  message: string
  history?: Array<{ role: string; content: string }>
}
